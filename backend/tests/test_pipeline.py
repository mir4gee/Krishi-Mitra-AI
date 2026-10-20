"""Offline tests: no Gemini or NewsAPI calls (keys are removed, Gemini is stubbed where needed)."""
import datetime as dt
import io
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ai_model_service as svc  # noqa: E402
import model_service as ms  # noqa: E402
from app import app  # noqa: E402

TODAY = dt.date(2026, 10, 20)


@pytest.fixture(autouse=True)
def no_keys(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_falling_prices_forecast_down_and_sell_now():
    # onion peaked in June 2024 and fell for nine weeks in the sample data
    result = svc.analyse({"cropType": "Onions", "spoilageDate": "2026-12-30"}, today=TODAY)
    assert result["crop"] == "onion"
    assert result["forecast"]["trend"] == "decreasing"
    assert result["forecast"]["predictions"][0]["price"] <= result["forecast"]["latest_price"] * 1.02
    assert result["recommendation"]["action"] == "sell now"


def test_rising_prices_with_time_to_spare_can_wait():
    df = pd.DataFrame({"date": pd.date_range("2024-01-06", periods=20, freq="7D"),
                       "price": [100 + 5 * i for i in range(20)]})
    fc = ms.run_price_forecast(df, days_ahead=15)
    assert fc["trend"] == "increasing"
    forecast_df = pd.DataFrame(fc["predictions"]).rename(columns={"price": "predicted_price"})
    forecast_df["date"] = pd.to_datetime(forecast_df["date"])
    rec = ms.fuse_decision("x", "m", [{"name": "m"}], forecast_df, spoilage_days_left=30,
                           storage_cost_per_day=0.1, sentiment_score=0.0)
    assert rec.best_date > forecast_df["date"].iloc[0].date()


def test_spoilage_deadline_caps_the_wait():
    result = svc.analyse({"cropType": "sugarcane", "spoilageDate": "2026-10-22"}, today=TODAY)
    assert result["spoilage"] == {"days_left": 2, "risk_score": 1.0, "spoils_on": "2026-10-22"}
    assert result["recommendation"]["sell_in_days"] <= 2


def test_spoilage_risk_falls_with_time_left():
    assert ms.spoilage_from_deadline(TODAY + dt.timedelta(days=1), TODAY) == (1, 1.0)
    _, mid = ms.spoilage_from_deadline(TODAY + dt.timedelta(days=10), TODAY)
    _, far = ms.spoilage_from_deadline(TODAY + dt.timedelta(days=60), TODAY)
    assert 1.0 > mid > far == 0.1


def test_no_news_key_means_neutral_and_no_invented_headlines():
    sentiment = svc.analyse_sentiment("wheat")
    assert sentiment["score"] == 0.0
    assert sentiment["headlines"] == []


def test_keyword_sentiment_is_on_minus_one_to_one_scale():
    assert ms.sentiment_from_headlines(["Onion glut as bumper crop arrives", "Price fall feared"]) < 0
    assert ms.sentiment_from_headlines(["Tomato shortage drives price rise"]) > 0
    assert ms.sentiment_from_headlines([]) == 0.0


def test_unknown_crop_has_no_forecast_and_says_so():
    result = svc.analyse({"cropType": "mango"}, today=TODAY)
    assert result["forecast"] is None and result["recommendation"] is None
    assert "mango" in svc.fallback_text(result)


def test_chat_without_gemini_key_returns_model_output(client):
    resp = client.post("/api/chat", json={"prompt": "Should I sell?", "userContext": {"cropType": "wheat"}})
    body = resp.get_json()
    assert resp.status_code == 200 and body["success"]
    assert "raw model output" in body["response"]
    assert body["analysis"]["forecast"]["data_as_of"] == "2024-08-17"


def test_chat_passes_language_and_analysis_to_gemini(client, monkeypatch):
    seen = {}

    def fake_text(_client, system, user):
        seen["system"], seen["user"] = system, user
        return "**Sell now.**"

    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setattr(svc, "gemini_text", fake_text)
    resp = client.post("/api/chat", json={"prompt": "बेचूं?", "language": "hi",
                                          "userContext": {"cropType": "tomato", "spoilageDate": "2026-10-25"}})
    assert resp.get_json()["response"] == "Sell now."
    assert "Hindi" in seen["system"]
    assert '"crop": "tomato"' in seen["user"] and "बेचूं?" in seen["user"]


def test_chat_rejects_missing_prompt(client):
    assert client.post("/api/chat", json={}).status_code == 400
    assert client.post("/api/chat", data="not json").status_code == 400


def test_audio_requires_file_and_reports_missing_key(client):
    assert client.post("/api/audio-chat").status_code == 400
    resp = client.post("/api/audio-chat", content_type="multipart/form-data",
                       data={"audio": (io.BytesIO(b"\x00" * 10), "a.webm", "audio/webm")})
    assert resp.status_code == 503
