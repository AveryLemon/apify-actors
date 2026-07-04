# Stem Separator — Apify Actor
# Separates audio files into stems (vocals, drums, bass, other)
# Uses audio-separator with ONNX runtime for lightweight inference
FROM apify/actor-python:3.11

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY main.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "apify", "run"]
