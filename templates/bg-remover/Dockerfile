FROM apify/actor-python:3.11

# Build-essential needed for ONNX runtime compilation
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY main.py ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "apify", "run"]
