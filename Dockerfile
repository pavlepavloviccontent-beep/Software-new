FROM python:3.11-slim

# Install system dependencies (ffmpeg for whisper, yt-dlp needs it too)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download whisper base model so first request isn't slow
RUN python -c "import whisper; whisper.load_model('base')"

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "300", "app:app"]
