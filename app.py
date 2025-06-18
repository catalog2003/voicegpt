from flask import Flask, request, jsonify
import speech_recognition as sr
from pydub import AudioSegment
import os
import requests

app = Flask(__name__)
os.makedirs("uploads", exist_ok=True)


AZURE_OPENAI_ENDPOINT = "https://newstoreapi.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"
AZURE_OPENAI_KEY = "5LkVKN23Wi4dF5lFI4ywkIHkb08dDXIG9IH95q51qszCUvslWPnfJQQJ99BFACYeBjFXJ3w3AAABACOGyTn5"

def send_to_azure_openai(text):
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY
    }
    payload = {
        "messages": [
            {"role": "system", "content": "I am Neel Prajapati. I’m a passionate Software Engineer with a superpower for rapidly building AI-powered, full-stack solutions that solve real-world problems. I love turning complex ideas into working apps using Python, .NET, React, and cloud platforms.I’m focused on growing in scalable AI system design, DevOps/MLOps, and open-source contribution. While I’m often seen as an independent builder, I thrive in collaborative teams and constantly push my limits through cross-domain, impactful projects."},
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
        <title>Speech to AI</title>
        <style>
            body { font-family: sans-serif; padding: 20px; max-width: 600px; margin: auto; }
            button { padding: 10px 20px; margin: 5px; }
        </style>
    </head>
    <body>
        <h2>🎤 Talk to AI</h2>
        <button id="start" onclick="start()">Start</button>
        <button id="stop" onclick="stop()" disabled>Stop</button>
        <p id="status">Ready</p>
        <script>
            let recorder, chunks = [], speech = window.speechSynthesis;
            async function start() {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                recorder = new MediaRecorder(stream);
                recorder.ondataavailable = e => chunks.push(e.data);
                recorder.onstop = async () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    const form = new FormData(); form.append('audio', blob);
                    document.getElementById("status").innerText = "Processing...";
                    const res = await fetch('/convert', { method: 'POST', body: form });
                    const data = await res.json();
                    let msg = data.ai_response || "Sorry, an error occurred.";
                    let utter = new SpeechSynthesisUtterance(msg);
                    speech.cancel(); speech.speak(utter);
                    utter.onend = () => document.getElementById("status").innerText = "Ready";
                    chunks = [];
                };
                recorder.start();
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
        webm_path = "uploads/temp.webm"
        wav_path = "uploads/temp.wav"
        request.files['audio'].save(webm_path)
        AudioSegment.from_file(webm_path).export(wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)

        os.remove(webm_path)
        os.remove(wav_path)

        ai_response = send_to_azure_openai(text)
        return jsonify({"ai_response": ai_response})
    except sr.UnknownValueError:
        return jsonify({"ai_response": "I couldn't understand that. Please try again."})
    except Exception as e:
        return jsonify({"ai_response": f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
