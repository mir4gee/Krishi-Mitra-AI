# app.py - Updated Flask application with AI Model integration
from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import json
import google.generativeai as genai
from deep_translator import GoogleTranslator

# Import your new AI model
from ai_model_service import get_ai_response  # Replace the dummy function

app = Flask(__name__)
CORS(app)

# Configure Gemini API
genai.configure(api_key="AIzaSyAazYiCXHrsqwbz2a0tJnt5ysZPUqS4h44")

# Updated AI response using your comprehensive model
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        prompt = data.get("prompt")
        model = data.get("model", "gemini-1.5-flash")
        user_context = data.get("userContext", {})

        if not prompt or not model:
            return jsonify({"success": False, "error": "Missing prompt or model"}), 400

        # Detect and handle language
        language = data.get("language", "en")
        
        # Translate to English if necessary
        translated_prompt = prompt
        if language != "en":
            try:
                translated_prompt = GoogleTranslator(source="auto", target="en").translate(prompt)
            except Exception as e:
                print(f"Translation error: {e}")
                # If translation fails, proceed with original prompt

        # Use the comprehensive AI model instead of dummy response
        ai_response = get_ai_response(translated_prompt, model, user_context)

        # Translate back to user language if needed
        if language != "en":
            try:
                ai_response = GoogleTranslator(source="en", target=language).translate(ai_response)
            except Exception as e:
                print(f"Translation error: {e}")
                # If translation fails, return English response
        
        print(f"AI Response: {ai_response}")
        return jsonify({"success": True, "response": ai_response})

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# Audio Chat Endpoint (updated to use new AI model)
@app.route("/api/audio-chat", methods=["POST"])
def audio_chat():
    try:
        if "audio" not in request.files:
            return jsonify({"success": False, "error": "No audio file uploaded"}), 400

        audio_file = request.files["audio"]

        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            audio_file.save(tmp.name)
            audio_path = tmp.name

        model_name = request.form.get("model", "gemini-1.5-flash")
        user_context = json.loads(request.form.get("userContext", "{}"))

        # Initialize Gemini model for transcription
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Transcribe with Gemini
        try:
            with open(audio_path, "rb") as f:
                audio_data = f.read()
            
            # Create the content for transcription
            response = model.generate_content([
                "Transcribe this audio clearly and accurately.",
                {
                    "mime_type": "audio/webm",
                    "data": audio_data
                }
            ])
            
            transcription = response.text

        except Exception as e:
            print(f"Transcription error: {e}")
            transcription = "Could not transcribe audio clearly. Please try again."

        # Use comprehensive AI model for response
        ai_response = get_ai_response(transcription, model_name, user_context)

        # Clean up temp file
        try:
            os.remove(audio_path)
        except:
            pass

        return jsonify({
            "success": True,
            "transcription": transcription,
            "response": ai_response
        })

    except Exception as e:
        print(f"Error in audio-chat endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)