# Content Repurposing Pipeline — Apify Actor
# Takes video/transcript content and generates social posts, quote cards, audiograms
# Uses yt-dlp for YouTube metadata, Pillow for images, gTTS for audio
FROM apify/actor-python:3.11

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY main.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "apify", "run"]
