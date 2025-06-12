from flask import Flask, request, jsonify
from openai import OpenAI
from pydub import AudioSegment
import tempfile
import os
import json

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
            print("📤 Enviando a Whisper para transcripción
