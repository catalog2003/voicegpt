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
    <script src="https://cdn.jsdelivr.net/gh/mattdiamond/Recorderjs/recorder.js"></script>

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
let audioContext;
let recorder;

function start() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
            audioContext = new AudioContext();
            const input = audioContext.createMediaStreamSource(stream);
            recorder = new Recorder(input, { numChannels: 1 });
            recorder.record();

            document.getElementById("status").innerText = "Recording...";
            document.getElementById("start").disabled = true;
            document.getElementById("stop").disabled = false;
        })
        .catch(function(err) {
            console.error('Microphone error:', err);
            document.getElementById("status").innerText = "Microphone access error";
        });
}

function stop() {
    recorder.stop(); // Stop recording

    document.getElementById("status").innerText = "Processing...";
    document.getElementById("start").disabled = false;
    document.getElementById("stop").disabled = true;

    // Export .wav and send
    recorder.exportWAV(function(blob) {
        const formData = new FormData();
        formData.append("audio", blob, "recording.wav");

        fetch("/convert", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById("status").innerText = "AI responded.";
            const text = data.ai_response || data.error || "No response";
            speak(text);
        })
        .catch(err => {
            console.error(err);
            document.getElementById("status").innerText = "Error uploading audio.";
        });
    });
}

function speak(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utterance);
}
</script>

    </body>
    </html>
    '''

@app.route('/convert', methods=['POST'])
def convert():
    try:
        wav_path = "uploads/temp.wav"
        request.files['audio'].save(wav_path)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            transcribed_text = recognizer.recognize_google(audio)

        os.remove(wav_path)

        ai_response = send_to_azure_openai(transcribed_text)
        return jsonify({
            "transcription": transcribed_text,
            "ai_response": ai_response
        })

    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand audio."})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"})



if __name__ == '__main__':
    app.run(debug=True, port=5000)