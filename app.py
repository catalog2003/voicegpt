from flask import Flask, request, jsonify
import speech_recognition as sr
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
            {"role": "system", "content": "You are a Neel Prajapati a software devloper.You're someone who loves solving real-world problems with AI and full-stack development. Your superpower is turning complex ideas into powerful, working apps using Python, .NET, React, and cloud technologies. You're focused on growing in scalable AI design, DevOps/MLOps, and open-source. People might think you prefer working solo—but you actually thrive in collaborative, high-energy teams and always push your limits through bold, interdisciplinary projects."},
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
                recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                chunks = [];

                recorder.ondataavailable = e => chunks.push(e.data);

                recorder.onstop = async () => {
                    document.getElementById("status").innerText = "Processing...";
                    
                    try {
                        // Convert WebM to WAV in the browser
                        const blob = new Blob(chunks, { type: 'audio/webm' });
                        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        const arrayBuffer = await blob.arrayBuffer();
                        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                        
                        // Convert to WAV
                        const wavBlob = audioBufferToWav(audioBuffer);
                        const form = new FormData();
                        form.append('audio', wavBlob, 'recording.wav');

                        const res = await fetch('/convert', { method: 'POST', body: form });
                        const data = await res.json();
                        const msg = data.ai_response || "Sorry, something went wrong.";

                        // Speak the response aloud
                        let utter = new SpeechSynthesisUtterance(msg);
                        speech.cancel(); // stop any ongoing speech
                        speech.speak(utter);
                        utter.onend = () => document.getElementById("status").innerText = "Ready";
                    } catch (e) {
                        console.error(e);
                        document.getElementById("status").innerText = "Error";
                        // Speak the error message
                        let utter = new SpeechSynthesisUtterance("Sorry, an error occurred. Please try again.");
                        speech.cancel();
                        speech.speak(utter);
                    }

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

            // Helper function to convert AudioBuffer to WAV Blob
            function audioBufferToWav(buffer) {
                const numChannels = buffer.numberOfChannels;
                const sampleRate = buffer.sampleRate;
                const length = buffer.length;
                
                // Interleave the channels
                const interleaved = new Float32Array(numChannels * length);
                for (let channel = 0; channel < numChannels; channel++) {
                    const channelData = buffer.getChannelData(channel);
                    for (let i = 0; i < length; i++) {
                        interleaved[i * numChannels + channel] = channelData[i];
                    }
                }
                
                // Create WAV header
                const wavHeader = createWavHeader(numChannels, sampleRate, length * numChannels * 2);
                
                // Convert to Int16 and combine with header
                const int16 = new Int16Array(length * numChannels);
                for (let i = 0; i < interleaved.length; i++) {
                    int16[i] = Math.min(1, interleaved[i]) * 0x7FFF;
                }
                
                const wavBytes = new Uint8Array(wavHeader.byteLength + int16.byteLength);
                wavBytes.set(new Uint8Array(wavHeader), 0);
                wavBytes.set(new Uint8Array(int16.buffer), wavHeader.byteLength);
                
                return new Blob([wavBytes], { type: 'audio/wav' });
            }
            
            // Helper function to create WAV header
            function createWavHeader(numChannels, sampleRate, dataLength) {
                const byteRate = sampleRate * numChannels * 2;
                const blockAlign = numChannels * 2;
                const header = new ArrayBuffer(44);
                const view = new DataView(header);
                
                // RIFF identifier
                writeString(view, 0, 'RIFF');
                // RIFF chunk length
                view.setUint32(4, 36 + dataLength, true);
                // RIFF type
                writeString(view, 8, 'WAVE');
                // Format chunk identifier
                writeString(view, 12, 'fmt ');
                // Format chunk length
                view.setUint32(16, 16, true);
                // Sample format (raw)
                view.setUint16(20, 1, true);
                // Channel count
                view.setUint16(22, numChannels, true);
                // Sample rate
                view.setUint32(24, sampleRate, true);
                // Byte rate (sample rate * block align)
                view.setUint32(28, byteRate, true);
                // Block align (channel count * bytes per sample)
                view.setUint16(32, blockAlign, true);
                // Bits per sample
                view.setUint16(34, 16, true);
                // Data chunk identifier
                writeString(view, 36, 'data');
                // Data chunk length
                view.setUint32(40, dataLength, true);
                
                return header;
            }
            
            function writeString(view, offset, string) {
                for (let i = 0; i < string.length; i++) {
                    view.setUint8(offset + i, string.charCodeAt(i));
                }
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
            text = recognizer.recognize_google(audio)

        os.remove(wav_path)

        ai_response = send_to_azure_openai(text)
        return jsonify({"ai_response": ai_response})

    except sr.UnknownValueError:
        return jsonify({"ai_response": "Sorry, I couldn't understand that. Please try again."})
    except Exception as e:
        return jsonify({"ai_response": f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)