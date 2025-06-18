from flask import Flask, request, jsonify
import speech_recognition as sr
from pydub import AudioSegment
import os
import requests

app = Flask(__name__)
os.makedirs("uploads", exist_ok=True)

# Azure OpenAI Config
AZURE_OPENAI_ENDPOINT = "https://newstoreapi.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"
AZURE_OPENAI_KEY = "5LkVKN23Wi4dF5lFI4ywkIHkb08dDXIG9IH95q51qszCUvslWPnfJQQJ99BFACYeBjFXJ3w3AAABACOGyTn5"

def send_to_azure_openai(text):
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 800,
        "temperature": 0.7
    }

    try:
        res = requests.post(AZURE_OPENAI_ENDPOINT, headers=headers, json=payload, timeout=30)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>🎤 Talk to AI</title>
        <style>
            body { font-family: sans-serif; padding: 20px; max-width: 600px; margin: auto; }
            button { padding: 10px 20px; margin: 5px; }
            #ai-text { margin-top: 20px; padding: 10px; background: #f0f0f0; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h2>🎤 Talk to AI</h2>
        <button id="start" onclick="start()">Start</button>
        <button id="stop" onclick="stop()" disabled>Stop</button>
        <p id="status">Ready</p>
        <div id="ai-text"></div>
        <script>
            let recorder, chunks = [], speech = window.speechSynthesis;

            async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(stream, { mimeType: 'audio/ogg; codecs=opus' }); // Use OGG instead of WebM
    chunks = [];

    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/ogg' }); // OGG format
        const form = new FormData();
        form.append('audio', blob, 'recording.ogg'); // Explicitly name it .ogg

        document.getElementById("status").innerText = "Processing...";
        try {
            const res = await fetch('/convert', { method: 'POST', body: form });
            const data = await res.json();
            document.getElementById("ai-text").innerText = "🤖 AI: " + (data.ai_response || "Error");
        } catch (e) {
            document.getElementById("ai-text").innerText = "❌ Failed to connect to server.";
        }
    };
    recorder.start();
}
                document.getElementById("start").disabled = true;
                document.getElementById("stop").disabled = false;
                document.getElementById("status").innerText = "Recording...";
            }

            function stop() {
                recorder.stop();
                document.getElementById("start").disabled = false;
                document.getElementById("stop").disabled = true;
            }
        </script>
    </body>
    </html>
    '''

@app.route('/convert', methods=['POST'])
def convert():
    try:
        ogg_path = "uploads/temp.ogg"
        request.files['audio'].save(ogg_path)

        recognizer = sr.Recognizer()
        with sr.AudioFile(ogg_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)

        os.remove(ogg_path)
        ai_response = send_to_azure_openai(text)
        return jsonify({"ai_response": ai_response})

    except sr.UnknownValueError:
        return jsonify({"ai_response": "Sorry, I couldn't understand that."})
    except Exception as e:
        return jsonify({"ai_response": f"Error: {str(e)}"})
if __name__ == '__main__':
    app.run(debug=True, port=5000)
