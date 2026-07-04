# TTS Voiceover Actor — Apify Actor
# Converts text to natural-sounding speech with multiple voice presets
# Uses gTTS (Google Text-to-Speech) — lightweight, no GPU or C extensions needed
FROM apify/actor-python:3.11

COPY main.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "apify", "run"]
