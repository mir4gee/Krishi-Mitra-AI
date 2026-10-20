# ai_model_service.py - the agent pipeline behind /api/chat
#
#   price forecaster  ┐
#   spoilage agent    ├─> supervisor (fuse_decision) ─> Gemini explains the decision to the farmer
#   news sentiment    ┘
#
# Every number the farmer sees comes from these agents; Gemini only explains them.
import os
import json
import time
import logging
import datetime as dt
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

from model_service import (
    INDIA_TZ, GeminiUnavailable, make_gemini_client, gemini_generate, gemini_text,
    spoilage_from_deadline, sentiment_from_headlines, fuse_decision, run_price_forecast,
)

log = logging.getLogger(__name__)

CSV_PATH = Path(__file__).with_name("market_data_csv.csv")
FORECAST_DAYS = 15
STORAGE_COST_PCT_PER_DAY = 0.001  # holding cost as a share of the latest price, per day
NEWS_TTL_S = 30 * 60

# Free-text crop names from the form -> commodity names in the CSV
CROP_ALIASES = {
    "tomatoes": "tomato", "onions": "onion", "potatoes": "potato", "paddy": "rice",
    "gehun": "wheat", "gehu": "wheat", "chawal": "rice", "dhan": "rice", "aloo": "potato",
    "pyaz": "onion", "pyaaz": "onion", "tamatar": "tomato", "ganna": "sugarcane",
}
LANGUAGES = {"en": "English", "hi": "Hindi (Devanagari script)"}


def normalise_crop(name: str) -> str:
    key = (name or "").strip().lower()
    return CROP_ALIASES.get(key, key)


# -----------------------------
# Market data (sample CSV)
# -----------------------------
@lru_cache(maxsize=1)
def load_market_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    df["commodity"] = df["commodity"].str.lower()
    return df.sort_values("date")


def available_commodities() -> List[str]:
    return sorted(load_market_data()["commodity"].unique())


@lru_cache(maxsize=32)
def _forecast(crop: str) -> Optional[Dict]:
    """Price agent: forecast from the crop's real history, or None if we have no data for it."""
    rows = load_market_data()
    rows = rows[rows["commodity"] == crop]
    if len(rows) < 2:
        return None
    fc = run_price_forecast(rows[["date", "price"]], days_ahead=FORECAST_DAYS)
    last = rows.iloc[-1]
    fc.update({
        "data_as_of": last["date"].date().isoformat(),
        "latest_price": float(last["price"]),
        "unit": last["unit"],
        "market": f"{last['location']} mandi",
        "history_points": len(rows),
    })
    return fc


# -----------------------------
# News sentiment agent
# -----------------------------
_news_cache: Dict[str, tuple] = {}


def fetch_headlines(crop: str) -> List[str]:
    """Real headlines from NewsAPI; an empty list when no key is set or the call fails."""
    key = os.getenv("NEWSAPI_KEY")
    if not key:
        return []
    cached = _news_cache.get(crop)
    if cached and time.time() - cached[0] < NEWS_TTL_S:
        return cached[1]
    try:
        resp = requests.get("https://newsapi.org/v2/everything", timeout=10, params={
            "q": f"{crop} AND (price OR mandi OR farmers OR harvest) AND India",
            "language": "en", "sortBy": "publishedAt", "pageSize": 10,
            "from": (dt.date.today() - dt.timedelta(days=7)).isoformat(), "apiKey": key,
        })
        resp.raise_for_status()
        headlines = [a["title"] for a in resp.json().get("articles", []) if a.get("title")]
    except Exception as e:
        log.warning("NewsAPI failed: %s", e)
        return []
    _news_cache[crop] = (time.time(), headlines)
    return headlines


def analyse_sentiment(crop: str) -> Dict:
    headlines = fetch_headlines(crop)
    if not headlines:
        return {"score": 0.0, "source": "none (no NEWSAPI_KEY or no recent headlines)", "headlines": []}
    client = make_gemini_client() if os.getenv("GEMINI_API_KEY") else None
    score = sentiment_from_headlines(headlines, use_gemini=client is not None, model=client)
    return {"score": round(score, 2), "source": "newsapi", "headlines": headlines[:5]}


# -----------------------------
# Pipeline
# -----------------------------
def _parse_date(value: str) -> Optional[dt.date]:
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def analyse(user_context: Dict, today: Optional[dt.date] = None) -> Dict:
    """Run all agents for the farmer's crop and fuse them into one recommendation."""
    today = today or dt.datetime.now(tz=INDIA_TZ).date()
    crop = normalise_crop(user_context.get("cropType", ""))
    forecast = _forecast(crop)

    spoilage_date = _parse_date(user_context.get("spoilageDate"))
    if spoilage_date:
        days_left, risk = spoilage_from_deadline(spoilage_date, today)
        spoilage = {"days_left": days_left, "risk_score": risk, "spoils_on": spoilage_date.isoformat()}
    else:
        spoilage = None

    sentiment = analyse_sentiment(crop) if crop else {"score": 0.0, "source": "none", "headlines": []}

    result = {"crop": crop, "forecast": forecast, "spoilage": spoilage, "sentiment": sentiment,
              "recommendation": None, "available_crops": available_commodities()}
    if forecast is None:
        return result

    forecast_df = pd.DataFrame(forecast["predictions"]).rename(columns={"price": "predicted_price"})
    forecast_df["date"] = pd.to_datetime(forecast_df["date"])
    rec = fuse_decision(
        crop=crop,
        location_name=forecast["market"],
        markets=[{"name": forecast["market"]}],  # one mandi in the data, so no cross-market uplift
        forecast_df=forecast_df,
        spoilage_days_left=spoilage["days_left"] if spoilage else FORECAST_DAYS,
        storage_cost_per_day=forecast["latest_price"] * STORAGE_COST_PCT_PER_DAY,
        sentiment_score=sentiment["score"],
    )
    # The sample data is historical, so express the plan as "days from now" rather than old calendar dates.
    as_of = dt.date.fromisoformat(forecast["data_as_of"])
    sell_in = (rec.best_date - as_of).days if spoilage is None or spoilage["days_left"] > 0 else 0
    result["recommendation"] = {
        "action": "sell now" if sell_in <= 1 else f"wait and sell in about {sell_in} days",
        "sell_in_days": sell_in,
        "sell_by": (today + dt.timedelta(days=sell_in)).isoformat(),
        "expected_net_price": rec.expected_price,
        "change_vs_latest_pct": round((rec.expected_price / forecast["latest_price"] - 1) * 100, 1),
        "market": rec.best_market,
        "confidence": rec.confidence,
        "alternatives": [
            {"sell_in_days": (dt.date.fromisoformat(a["date"]) - as_of).days, "expected_net_price": a["expected_price"]}
            for a in rec.alternatives
        ],
    }
    return result


SYSTEM_PROMPT = """You are KrishiMitra, an agricultural advisor for Indian farmers.
You are given the farmer's profile and the output of three analysis agents (price forecast,
spoilage, news sentiment) plus a supervisor recommendation. Rules:
- Ground every number you mention in ANALYSIS. Never invent prices, dates, news or schemes' amounts.
- If the farmer asks when or whether to sell, lead with the supervisor recommendation and its confidence,
  then give 2-3 reasons drawn from the forecast trend, spoilage window and news sentiment.
- Say plainly when an input is missing (for example no price data for this crop, or no live news).
- Prices come from a sample dataset; mention its "data_as_of" date once when you quote a price.
- For questions the analysis does not cover (irrigation, pests, schemes), give practical general advice
  and suggest the local Krishi Vigyan Kendra for specifics.
- Plain text only, no markdown symbols. Under 200 words. Short sentences.
- Reply in {language}, whatever language the question is in."""


def fallback_text(analysis: Dict) -> str:
    """Used when Gemini is unavailable: the agents' result, stated plainly."""
    rec, fc = analysis["recommendation"], analysis["forecast"]
    if not rec:
        return (f"I don't have price data for '{analysis['crop'] or 'this crop'}'. "
                f"Crops I can forecast: {', '.join(analysis['available_crops'])}.")
    return (f"Recommendation: {rec['action']} at {rec['market']}, about ₹{rec['expected_net_price']} {fc['unit']} "
            f"({rec['change_vs_latest_pct']:+}% vs ₹{fc['latest_price']} on {fc['data_as_of']}). "
            f"Price trend: {fc['trend']}. Confidence: {rec['confidence']}. "
            f"(The AI explanation is unavailable right now, so this is the raw model output.)")


def get_ai_response(prompt: str, user_context: Dict, language: str = "en") -> Dict:
    analysis = analyse(user_context)
    profile = {k: user_context.get(k) for k in ("name", "cropType", "quantity", "qualityGrade", "farmerLocation", "spoilageDate")}
    # Forecast dates follow the sample data (2024); give Gemini "day N from now" so it never quotes past dates.
    for_llm = dict(analysis)
    if analysis["forecast"]:
        for_llm["forecast"] = {**analysis["forecast"], "predictions": [
            {"day": i + 1, "price": p["price"]} for i, p in enumerate(analysis["forecast"]["predictions"])]}
    user_prompt = (f"FARMER PROFILE:\n{json.dumps(profile, ensure_ascii=False)}\n\n"
                   f"ANALYSIS:\n{json.dumps(for_llm, ensure_ascii=False, default=str)}\n\n"
                   f"QUESTION:\n{prompt}")
    system = SYSTEM_PROMPT.format(language=LANGUAGES.get(language, LANGUAGES["en"]))
    try:
        text = gemini_text(make_gemini_client(), system, user_prompt)
    except GeminiUnavailable as e:
        log.error("Gemini unavailable: %s", e)
        text = fallback_text(analysis)
    return {"response": text.replace("**", ""), "analysis": analysis}


def transcribe(audio: bytes, mime_type: str) -> str:
    resp = gemini_generate(make_gemini_client(), [
        "Transcribe this farmer's voice message exactly, in the language spoken. Return only the transcript.",
        types.Part.from_bytes(data=audio, mime_type=mime_type),
    ])
    return (resp.text or "").strip()
