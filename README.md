# Instagram Viral Analyzer

A mobile-friendly web app that analyzes any Instagram profile to find the most and least viral videos, then transcribes them to extract the scripts.

## Features

- **Profile Analysis**: Enter any public Instagram profile URL or username
- **Viral Ranking**: Shows top 15 most viral and 15 least viral videos sorted by view count
- **Auto-Transcription**: Automatically transcribes each video's audio using OpenAI Whisper (runs locally, free)
- **Copy Scripts**: One-tap copy of any video transcript
- **Mobile-First**: Designed for phone screens with a dark, modern UI

## Requirements

- Python 3.9+
- ffmpeg (for audio processing)

## Quick Start

```bash
# 1. Install dependencies
chmod +x setup.sh run.sh
./setup.sh

# 2. Run the app
./run.sh

# 3. Open on your phone
# Navigate to http://<your-computer-ip>:5000
```

## How It Works

1. You enter an Instagram profile URL or @username
2. The app fetches all video posts from the profile using Instaloader
3. Videos are ranked by view count (most to least viral)
4. Top 15 and bottom 15 videos are transcribed using OpenAI Whisper
5. Results are displayed with expandable cards showing the full transcript

## Tech Stack

- **Backend**: Python / Flask
- **Scraping**: Instaloader
- **Video Download**: yt-dlp
- **Transcription**: OpenAI Whisper (local, no API key needed)
- **Frontend**: Vanilla HTML/CSS/JS (mobile-first design)

## Notes

- Only **public** Instagram profiles can be analyzed (private profiles require login)
- Transcription quality depends on audio clarity; the "base" Whisper model is used by default for speed
- The first run downloads the Whisper model (~140MB), subsequent runs use the cached model
- For better transcription accuracy, change `whisper.load_model("base")` to `"medium"` or `"large"` in `app.py`
