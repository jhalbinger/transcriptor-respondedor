from flask import Flask, request, jsonify
from openai import OpenAI
from pydub import AudioSegment
import tempfile
import os
import json
import requests  # Esto también es necesario para llamar al microservicio GPT

client = OpenAI()

app = Flask(__name__)

@app.route("/")
def index():
    return "🎙️ Microservicio transcriptor-respondedor activo"

@app.route("/transcripcion", methods=["POST"])
def transcripcion():
    try:
        if 'audio' not in request.files:
            print("⚠️ No se recibió archivo 'audio'")
            return jsonify({"error": "No se envió el archivo de audio"}), 400

        archivo_audio = request.files['audio']

        # Guardar temporalmente el archivo OGG
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_ogg:
            archivo_audio.save(temp_ogg.name)
            print(f"📥 Audio recibido y guardado como {temp_ogg.name}")

            # Convertir a MP3
            audio = AudioSegment.from_file(temp_ogg.name)
            temp_mp3_path = temp_ogg.name.replace(".ogg", ".mp3")
            audio.export(temp_mp3_path, format="mp3")
            print(f"🎧 Audio convertido a {temp_mp3_path}")

        # Transcripción con Whisper
        with open(temp_mp3_path, "rb") as audio_file:
            print("📤 Enviando a Whisper para transcripción...")
            respuesta = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        texto_transcripto = respuesta.text
        print("📝 Transcripción:", texto_transcripto)

        # Enviar ese texto al microservicio generador de respuestas
        print("🤖 Enviando transcripción a GPT para respuesta...")
        respuesta_gpt = requests.post(
            "https://orquestador-ms.onrender.com/webhook",  # Cambiar por la URL de tu microservicio si se modifica
            json={"consulta": texto_transcripto}
        )

        if respuesta_gpt.status_code == 200:
            respuesta_final = respuesta_gpt.json().get("respuesta", "🤷 No entendí tu mensaje.")
            return jsonify({"respuesta": respuesta_final})
        else:
            print("⚠️ Error al contactar con GPT:", respuesta_gpt.text)
            return jsonify({"respuesta": "⚠️ Error al generar respuesta"}), 500

    except Exception as e:
        print("❌ ERROR EN SERVIDOR:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
