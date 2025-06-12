from flask import Flask, request, jsonify
import openai
import os
from pydub import AudioSegment
import tempfile
import requests

app = Flask(__name__)

# Configurar API Key desde variable de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

# Endpoint del microservicio que genera la respuesta con GPT
ENDPOINT_GPT = "https://gpt-respondedor.onrender.com/webhook"  # Cambiar por el real si es distinto

@app.route("/")
def index():
    return "🎙️ Microservicio de transcripción y respuesta activo."

@app.route("/transcripcion", methods=["POST"])
def transcripcion():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No se envió el archivo de audio"}), 400

        archivo_audio = request.files['audio']

        # Guardar archivo temporal .ogg
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_ogg:
            archivo_audio.save(temp_ogg.name)

            # Convertir a MP3
            audio = AudioSegment.from_file(temp_ogg.name)
            temp_mp3_path = temp_ogg.name.replace(".ogg", ".mp3")
            audio.export(temp_mp3_path, format="mp3")

        # Transcribir con Whisper
        with open(temp_mp3_path, "rb") as audio_file:
            respuesta = openai.Audio.transcribe("whisper-1", audio_file)

        texto_transcripto = respuesta["text"].strip()

        # Limpiar archivos temporales
        os.remove(temp_ogg.name)
        os.remove(temp_mp3_path)

        # Si no se pudo transcribir nada, informar
        if not texto_transcripto:
            return jsonify({"texto": "", "respuesta": "🧐 No pude entender lo que dijiste en el audio."})

        # Enviar transcripción al microservicio de respuesta
        payload = {"consulta": texto_transcripto}
        headers = {"Content-Type": "application/json"}
        respuesta_gpt = requests.post(ENDPOINT_GPT, json=payload, headers=headers)

        if respuesta_gpt.status_code == 200:
            respuesta_texto = respuesta_gpt.json().get("respuesta", "")
        else:
            respuesta_texto = "⚠️ Error al generar la respuesta."

        return jsonify({"texto": texto_transcripto, "respuesta": respuesta_texto})

    except Exception as e:
        print("❌ ERROR EN SERVIDOR:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
