# Aesthetic Music Tagger — Apify Actor
# Analyzes audio files and returns aesthetic/mood/energy tags
# Uses librosa for lightweight analysis — no OWL factory code involved
FROM apify/actor-python:3.11

COPY main.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "apify", "run"]
