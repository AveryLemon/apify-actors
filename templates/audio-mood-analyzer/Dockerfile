# Audio Mood Analyzer — Apify Actor
# Analyzes audio files for mood/emotion profiles, energy curves, and segment-level analysis
# Uses librosa only — lightweight, no OWL factory code
FROM apify/actor-python:3.11

COPY main.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "apify", "run"]
