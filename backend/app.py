# app.py - Flask API for KrishiMitraAI
import os
import json
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from ai_model_service import get_ai_response, transcribe
from model_service import GeminiUnavailable

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # voice notes are well under this
CORS(app, origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","))

MAX_PROMPT_CHARS = 2000


def _bad_request(message):
    return jsonify({"success": False, "error": message}), 400


def _user_context(raw):
    return raw if isinstance(raw, dict) else {}


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
                    "news_configured": bool(os.getenv("NEWSAPI_KEY"))})


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return _bad_request("Missing prompt")
    if len(prompt) > MAX_PROMPT_CHARS:
        return _bad_request(f"Prompt is longer than {MAX_PROMPT_CHARS} characters")
    try:
        result = get_ai_response(prompt, _user_context(data.get("userContext")), data.get("language", "en"))
    except Exception:
        log.exception("chat failed")
        return jsonify({"success": False, "error": "Something went wrong while analysing your question."}), 500
    return jsonify({"success": True, **result})


@app.post("/api/audio-chat")
def audio_chat():
    audio = request.files.get("audio")
    if audio is None:
        return _bad_request("No audio file uploaded")
    try:
        user_context = _user_context(json.loads(request.form.get("userContext", "{}")))
    except json.JSONDecodeError:
        return _bad_request("userContext is not valid JSON")

    mime_type = (audio.mimetype or "audio/webm").split(";")[0]
    try:
        transcription = transcribe(audio.read(), mime_type)
    except GeminiUnavailable as e:
        log.error("transcription failed: %s", e)
        return jsonify({"success": False, "error": "Voice input is unavailable right now. Please type your question."}), 503
    if not transcription:
        return _bad_request("Could not hear any speech. Please try again.")

    try:
        result = get_ai_response(transcription, user_context, request.form.get("language", "en"))
    except Exception:
        log.exception("audio chat failed")
        return jsonify({"success": False, "error": "Something went wrong while analysing your question."}), 500
    return jsonify({"success": True, "transcription": transcription, **result})


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=int(os.getenv("PORT", 5000)))
