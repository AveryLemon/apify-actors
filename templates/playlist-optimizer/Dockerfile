# Playlist Optimizer — Apify Actor
# Orders tracks for optimal emotional flow and energy arc
# Pure Python — no audio analysis, just track metadata reordering
FROM apify/actor-python:3.11

COPY main.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "apify", "run", "main.py"]
