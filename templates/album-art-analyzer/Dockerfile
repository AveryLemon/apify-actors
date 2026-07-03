# Album Art Analyzer — Apify Actor
# Analyzes album cover images for aesthetic scores, color harmony, and mood
# Uses Pillow for lightweight image analysis — no OWL factory code involved
FROM apify/actor-python:3.11

COPY main.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "apify", "run", "main.py"]
