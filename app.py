from flask import Flask, request, jsonify
import requests
from pydub import AudioSegment
import tempfile
import os
import openai

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    return "🟢 Transcriptor-Respondedor funcionando"

@app.route("/transcripcion", methods=["POST"])
def transcripcion():
    if "audio" not in request.files:
        return jsonify({"error": "No se envió un archivo de audio"}), 400

    archivo = request.files["audio"]
    ruta_ogg = None
    ruta_mp3 = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f:
            archivo.save(f)
            ruta_ogg = f.name

        # Convertir a mp3
        sonido = AudioSegment.from_file(ruta_ogg)
        ruta_mp3 = ruta_ogg.replace(".ogg", ".mp3")
        sonido.export(ruta_mp3, format="mp3")
        print(f"🎧 Audio convertido a {ruta_mp3}")

        # Transcribir con Whisper
        print("📤 Enviando a Whisper para transcripción...")
        with open(ruta_mp3, "rb") as f:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )

        texto_transcripto = transcript.strip()
        print(f"📝 Transcripción: {texto_transcripto}")

        # Enviar al orquestador
        print("🤖 Enviando transcripción a GPT para respuesta...")
        respuesta_gpt = requests.post(
            "https://orquestador-ms.onrender.com/orquestador-ms",
            json={
                "consulta": texto_transcripto,
                "motivo": "otro"
            }
        )

        if respuesta_gpt.status_code != 200:
            print(f"⚠️ Error al contactar con GPT: {respuesta_gpt.text}")
            return jsonify({"error": "Fallo al contactar con GPT"}), 500

        data = respuesta_gpt.json()
        respuesta_final = data.get("respuesta_agente", "🤖 GPT no respondió.")
        return jsonify({"respuesta": respuesta_final})

    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        if ruta_ogg and os.path.exists(ruta_ogg):
            os.remove(ruta_ogg)
        if ruta_mp3 and os.path.exists(ruta_mp3):
            os.remove(ruta_mp3)

if __name__ == "__main__":
    app.run()
