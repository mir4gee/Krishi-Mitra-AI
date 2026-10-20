import os
import math
import json
import logging
import datetime as dt
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

import numpy as np
import pandas as pd

# ---- LLM (Gemini) ----
from google import genai
from google.genai import errors, types
from dateutil import tz
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

# ---- Forecasting ----
try:
    from prophet import Prophet
    _HAS_PROPHET = True
except Exception:
    _HAS_PROPHET = False
from statsmodels.tsa.holtwinters import ExponentialSmoothing

log = logging.getLogger(__name__)
INDIA_TZ = tz.gettz("Asia/Kolkata")

# -----------------------------
# LLM: Gemini client & helpers
# -----------------------------
# Tried in order: free-tier Flash models are often briefly overloaded (503) or rate limited (429).
GEMINI_MODELS = os.getenv("GEMINI_MODELS", "gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.8-flash").split(",")
GEMINI_TIMEOUT_MS = 30_000


class GeminiUnavailable(RuntimeError):
    """No API key, or every model in GEMINI_MODELS failed."""


def make_gemini_client() -> genai.Client:
    if not os.getenv("GEMINI_API_KEY"):
        raise GeminiUnavailable("GEMINI_API_KEY not set")
    return genai.Client(http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS))  # reads GEMINI_API_KEY


def _retryable(exc: Exception) -> bool:
    if isinstance(exc, errors.ServerError):
        return True
    return isinstance(exc, errors.ClientError) and exc.code == 429


def gemini_generate(client: genai.Client, contents, config: Optional[types.GenerateContentConfig] = None):
    """generate_content with model fallback; returns the response of the first model that answers."""
    for i, model in enumerate(GEMINI_MODELS):
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as exc:
            if not _retryable(exc) or i == len(GEMINI_MODELS) - 1:
                raise GeminiUnavailable(f"{model}: {exc}") from exc
            log.warning("Gemini %s unavailable (%s), trying %s", model, type(exc).__name__, GEMINI_MODELS[i + 1])


def gemini_json(client: genai.Client, system_prompt: str, user_prompt: str) -> dict:
    config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.1,
                                         response_mime_type="application/json")
    return json.loads(gemini_generate(client, user_prompt, config).text)


def gemini_text(client: genai.Client, system_prompt: str, user_prompt: str) -> str:
    config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.3)
    return gemini_generate(client, user_prompt, config).text.strip()

# -----------------------------
# Price Forecasting
# -----------------------------
class PriceForecaster:
    """
    Accepts a price series (date, price). Provides n-day forecast and trend label.
    Uses Prophet if available; otherwise falls back to ExponentialSmoothing.
    """
    def __init__(self):
        self._model = None
        self._mode = None  # 'prophet' or 'ets'

    def fit(self, df_prices: pd.DataFrame):
        """
        df_prices columns: ['date','price'] with date as datetime64[ns] or string.
        """
        df = df_prices.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df.dropna(subset=['price'])

        if len(df) < 7:
            # too few points; pad with last known price
            last = df['price'].iloc[-1]
            for i in range(7 - len(df)):
                df = pd.concat([df, pd.DataFrame([{'date': df['date'].iloc[-1] + pd.Timedelta(days=1),
                                                   'price': last}])])

        if _HAS_PROPHET:
            # a day-of-week pattern only exists in daily data; on weekly prices it makes forecasts swing wildly
            is_daily = df['date'].diff().median() <= pd.Timedelta(days=1)
            # The defaults keep the trend too stiff for a few months of mandi prices: a price that peaked and
            # has fallen for weeks was still forecast to rise. Let the trend bend, including in recent weeks.
            m = Prophet(daily_seasonality=False, weekly_seasonality=bool(is_daily), yearly_seasonality=False,
                        changepoint_range=0.95, changepoint_prior_scale=0.5)
            train = df.rename(columns={'date': 'ds', 'price': 'y'})
            m.fit(train)
            self._model = m
            self._mode = 'prophet'
        else:
            # Simple additive ETS as fallback
            s = df.set_index('date')['price'].asfreq('D').interpolate()
            model = ExponentialSmoothing(s, trend="add", seasonal=None).fit()
            self._model = model
            self._mode = 'ets'
        return self

    def predict(self, days_ahead: int) -> pd.DataFrame:
        """
        Returns DataFrame with ['date','predicted_price'] of future dates only.
        """
        if self._mode == 'prophet':
            future = self._model.make_future_dataframe(periods=days_ahead, freq='D', include_history=False)
            fc = self._model.predict(future)[['ds', 'yhat']]
            fc.columns = ['date', 'predicted_price']
            return fc
        elif self._mode == 'ets':
            fc = self._model.forecast(days_ahead)
            # forecast continues from the last observation, like Prophet's future dataframe
            out = pd.DataFrame({'date': pd.date_range(start=fc.index[0],
                                                      periods=days_ahead, freq='D'),
                                'predicted_price': np.asarray(fc)})
            return out
        else:
            raise RuntimeError("Model not fitted")

    @staticmethod
    def trend_label(series: List[float]) -> str:
        if len(series) < 2:
            return "stable"
        # slope relative to the mean price, so ₹/kg and ₹/quintal crops use the same threshold
        x = np.arange(len(series))
        y = np.array(series)
        slope = np.polyfit(x, y, 1)[0] / np.mean(y)
        if slope > 0.002:  # > +0.2% per day
            return "increasing"
        if slope < -0.002:
            return "decreasing"
        return "stable"

# -----------------------------
# Spoilage Risk (rule-based)
# -----------------------------
# Base shelf-life days by crop & storage (rough indicative defaults; tune per literature)
BASE_SHELF_LIFE = {
    # crop: {storage: days}
    "onion": {"open": 14, "ambient": 21, "cold": 45},
    "tomato": {"open": 4, "ambient": 7, "cold": 14},
    "wheat": {"open": 60, "ambient": 120, "cold": 240},
    "potato": {"open": 10, "ambient": 20, "cold": 60},
}

def estimate_spoilage_days_left(
    crop: str,
    storage: str,
    harvest_date: dt.date,
    today: Optional[dt.date],
    avg_temp_c: float,
    avg_humidity: float
) -> Tuple[int, float]:
    """
    Returns (days_left, risk_score 0..1)
    Risk increases with temp/humidity and time since harvest.
    """
    today = today or dt.datetime.now(tz=INDIA_TZ).date()
    storage_key = storage.lower()
    crop_key = crop.lower()

    base = BASE_SHELF_LIFE.get(crop_key, {}).get(storage_key, 10)

    # temperature/humidity penalties
    temp_pen = max(0.0, (avg_temp_c - 25.0) * 0.5)  # every 1C above 25 reduces ~0.5 day
    hum_pen = max(0.0, (avg_humidity - 60.0) * 0.05)  # every 1% above 60 reduces 0.05 day
    penalty = temp_pen + hum_pen

    days_since_harvest = (today - harvest_date).days
    effective_life = max(1.0, base - penalty)
    days_left = int(max(0, math.floor(effective_life - days_since_harvest)))

    # risk score: 1 if days_left<=2, else scale with temperature/humidity
    risk = 1.0 if days_left <= 2 else min(1.0, 0.4 + (penalty / 20.0))
    return days_left, round(risk, 2)

def spoilage_from_deadline(spoilage_date: dt.date, today: Optional[dt.date] = None) -> Tuple[int, float]:
    """
    For when the farmer already knows the date the stock goes bad.
    Returns (days_left, risk_score 0..1): risk is 1 within 2 days and falls to 0.1 at 30+ days.
    """
    today = today or dt.datetime.now(tz=INDIA_TZ).date()
    days_left = max(0, (spoilage_date - today).days)
    risk = 1.0 if days_left <= 2 else max(0.1, 1.0 - (days_left - 2) / 28 * 0.9)
    return days_left, round(risk, 2)

# -----------------------------
# Headline Sentiment (optional)
# -----------------------------
POS_KWS = ["shortage", "export demand", "price rise", "spike", "higher demand"]
NEG_KWS = ["bumper crop", "oversupply", "glut", "price fall", "import", "ban", "stock release"]

def sentiment_from_headlines(
    headlines: List[str],
    use_gemini: bool = False,
    model: Optional[genai.Client] = None
) -> float:
    """
    Returns sentiment score in [-1, 1].
    If use_gemini=True, asks Gemini to rate headlines for price impact.
    """
    if use_gemini and model is not None and len(headlines) > 0:
        sys = "You are an agri-market analyst. Rate the expected 7-day price impact of the following headlines for the crop as a number in [-1,1], where -1 means strong downward pressure, +1 means strong upward pressure. Return JSON: {\"score\": number}."
        user = "Headlines:\n" + "\n".join([f"- {h}" for h in headlines])
        try:
            j = gemini_json(model, sys, user)
            return max(-1.0, min(1.0, float(j.get("score", 0.0))))
        except Exception as e:
            log.warning("Gemini sentiment failed, using keywords: %s", e)

    # keyword heuristic fallback
    score = 0.0
    text = " ".join(h.lower() for h in headlines)
    for w in POS_KWS:
        if w in text:
            score += 0.2
    for w in NEG_KWS:
        if w in text:
            score -= 0.2
    return max(-1.0, min(1.0, score))

# -----------------------------
# Fusion Policy (recommendation)
# -----------------------------
@dataclass
class Recommendation:
    best_date: dt.date
    expected_price: float
    best_market: str
    confidence: float
    reasoning: str
    alternatives: List[Dict]

def fuse_decision(
    crop: str,
    location_name: str,
    markets: List[Dict],  # [{name, distance_km, latest_price}]
    forecast_df: pd.DataFrame,  # ['date','predicted_price']
    spoilage_days_left: int,
    storage_cost_per_day: float,
    sentiment_score: float,
    min_price: Optional[float] = None,
) -> Recommendation:
    """
    Choose best date within forecast horizon considering:
      - predicted price
      - spoilage window
      - sentiment tilt
      - storage cost
      - nearby markets (simple uplift vs latest_price)
    """
    horizon = len(forecast_df)
    if horizon == 0:
        raise ValueError("Empty forecast")

    # sentiment boosts or penalizes curve gently
    adj = 1.0 + (0.05 * sentiment_score)  # ±5%
    forecast_df = forecast_df.copy()
    forecast_df['adj_price'] = (forecast_df['predicted_price'] * adj).round(2)

    # enforce spoilage window
    sell_window = min(spoilage_days_left, horizon)
    if sell_window <= 0:
        # immediate sale
        row0 = forecast_df.iloc[0]
        base_price = row0['adj_price']
        market = max(markets, key=lambda m: m.get('latest_price', base_price))
        exp = float(max(base_price, market.get('latest_price', base_price)))
        return Recommendation(
            best_date=row0['date'].date(),
            expected_price=exp,
            best_market=market['name'],
            confidence=0.55,
            reasoning="High spoilage risk; recommending immediate sale.",
            alternatives=[]
        )

    # compute net price after storage cost
    def net_price(day_index: int, base_price: float) -> float:
        return base_price - (storage_cost_per_day * day_index)

    candidates = []
    for i in range(sell_window):
        row = forecast_df.iloc[i]
        day_price = float(row['adj_price'])
        # consider market uplift vs local
        best_mkt = None
        best_mkt_price = day_price
        for m in markets:
            uplift = m.get('latest_price', day_price)
            # assume future tracks proportionally; we'll take max
            if uplift > best_mkt_price:
                best_mkt_price = uplift
                best_mkt = m['name']
        best_mkt = best_mkt or (markets[0]['name'] if markets else "Local Mandi")

        net = net_price(i+1, best_mkt_price)  # i+1 because day_1 = tomorrow
        candidates.append((i, row['date'].date(), net, best_mkt, best_mkt_price))

    # pick argmax net
    idx, date, net, mname, raw_price = max(candidates, key=lambda x: x[2])

    # confidence: higher when (trend up) & ample window & sentiment positive
    prices = forecast_df['adj_price'].tolist()
    trend = PriceForecaster.trend_label(prices)
    conf = 0.6
    if trend == "increasing":
        conf += 0.15
    elif trend == "decreasing":
        conf -= 0.1
    conf += 0.1 * max(0, (sell_window - 2)) / 10.0
    conf += 0.1 * max(0.0, sentiment_score)
    conf = max(0.3, min(0.95, conf))

    # min acceptable price guard
    if min_price is not None and net < min_price:
        # suggest earliest day meeting min_price or fallback earliest sale
        feasible = [c for c in candidates if c[2] >= min_price]
        if feasible:
            idx, date, net, mname, raw_price = feasible[0]
            conf -= 0.05
        else:
            # recommend immediate with note
            date = forecast_df.iloc[0]['date'].date()
            mname = candidates[0][3]
            net = float(forecast_df.iloc[0]['adj_price'])
            conf = max(0.4, conf - 0.2)

    # alternatives: top-3 other days
    alts = []
    for j in sorted(candidates, key=lambda x: x[2], reverse=True)[1:4]:
        alts.append({
            "date": j[1].isoformat(),
            "expected_price": round(j[2], 2),
            "market": j[3]
        })

    reason = f"Selected {date.isoformat()} because adjusted price curve is {trend}, " \
             f"spoilage window is {sell_window} days, sentiment tilt={sentiment_score:.2f}, " \
             f"and storage cost penalizes waiting."

    return Recommendation(
        best_date=date,
        expected_price=round(net, 2),
        best_market=mname,
        confidence=round(conf, 2),
        reasoning=reason,
        alternatives=alts
    )

# -----------------------------
# Orchestrator functions you call from endpoints
# -----------------------------
def run_price_forecast(df_prices: pd.DataFrame, days_ahead: int = 15) -> Dict:
    """
    df_prices: columns ['date','price'] with recent mandi prices for the crop+region.
    Raises ValueError when there is no history to forecast from (never invents prices).
    """
    if df_prices.empty or len(df_prices) < 2:
        raise ValueError("need at least 2 price points to forecast")
    forecaster = PriceForecaster().fit(df_prices)
    fc = forecaster.predict(days_ahead)
    trend = PriceForecaster.trend_label(fc['predicted_price'].tolist())
    return {
        "model": forecaster._mode,
        "trend": trend,
        "predictions": [
            {"date": d.strftime("%Y-%m-%d"), "price": round(float(p), 2)}
            for d, p in zip(fc['date'], fc['predicted_price'])
        ]
    }

def run_spoilage(crop: str, storage: str, harvest_date: str, avg_temp_c: float, avg_humidity: float) -> Dict:
    try:
        hd = dt.datetime.strptime(harvest_date, "%Y-%m-%d").date()
        days_left, risk = estimate_spoilage_days_left(
            crop=crop, storage=storage, harvest_date=hd, today=None,
            avg_temp_c=avg_temp_c, avg_humidity=avg_humidity
        )
        return {"spoilage_days_left": int(days_left), "risk_score": float(risk)}
    except Exception as e:
        print(f"Spoilage calculation error: {e}")
        # Return safe defaults
        return {"spoilage_days_left": 10, "risk_score": 0.3}

def run_sentiment(headlines: List[str], use_gemini: bool = False) -> Dict:
    try:
        model = make_gemini_client() if use_gemini and os.getenv("GEMINI_API_KEY") else None
        score = sentiment_from_headlines(headlines, use_gemini=use_gemini, model=model)
        return {"sentiment_score": round(float(score), 3)}
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        # Return neutral sentiment as fallback
        return {"sentiment_score": 0.0}

def run_recommendation(
    crop: str,
    location_name: str,
    markets: List[Dict],
    df_price_forecast: pd.DataFrame,
    spoilage_days_left: int,
    storage_cost_per_day: float,
    sentiment_score: float,
    min_price: Optional[float] = None
) -> Dict:
    rec = fuse_decision(
        crop=crop,
        location_name=location_name,
        markets=markets,
        forecast_df=df_price_forecast,
        spoilage_days_left=spoilage_days_left,
        storage_cost_per_day=storage_cost_per_day,
        sentiment_score=sentiment_score,
        min_price=min_price
    )
    return {
        "best_date_to_sell": rec.best_date.isoformat(),
        "expected_price": rec.expected_price,
        "market": rec.best_market,
        "confidence": rec.confidence,
        "reasoning": rec.reasoning,
        "alternatives": rec.alternatives
    }
