# Aesthetic Style Analyzer — Apify Actor
# Analyzes images for aesthetic quality, composition rules, style classification
# Uses Pillow + numpy for lightweight analysis — no OWL factory code involved
FROM apify/actor-python:3.11

COPY main.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "apify", "run"]
