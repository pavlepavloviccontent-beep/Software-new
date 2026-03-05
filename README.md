# Instagram Viral Analyzer

A desktop web app that analyzes any Instagram profile to find the most and least viral videos, then transcribes them to extract the scripts.

## Features

- **Profile Analysis** — Enter any public Instagram profile URL or username
- **Viral Ranking** — Top 15 most viral + 15 least viral videos sorted by views
- **Auto-Transcription** — Transcribes each video using OpenAI Whisper (runs locally, free)
- **Export All** — Download all transcripts as a text file with one click
- **Copy Scripts** — Copy any individual transcript to clipboard
- **Desktop-First UI** — Two-column grid layout, dark theme, responsive down to mobile

## Deploy to the Web (Render — Free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) and sign up (free)
3. Click **New > Web Service**
4. Connect your GitHub repo
5. Render auto-detects the `Dockerfile` — just click **Deploy**
6. Your app will be live at `https://your-app.onrender.com`

> **Note:** The free Render tier has 512MB RAM. Whisper's `base` model fits fine. For heavy usage, upgrade to a paid plan.

## Run Locally

```bash
# 1. Install dependencies
chmod +x setup.sh run.sh
./setup.sh

# 2. Run the app
./run.sh

# 3. Open http://localhost:5000
```

## Requirements

- Python 3.9+
- ffmpeg (`sudo apt install ffmpeg` / `brew install ffmpeg`)

## How It Works

1. You enter an Instagram profile URL or @username
2. The app fetches all video posts using Instaloader
3. Videos are ranked by view count
4. Top 15 and bottom 15 videos are transcribed using OpenAI Whisper
5. Results shown in a two-column grid with expandable transcript cards

## Tech Stack

- **Backend**: Python / Flask / Gunicorn
- **Scraping**: Instaloader
- **Video Download**: yt-dlp
- **Transcription**: OpenAI Whisper (local, no API key)
- **Frontend**: Vanilla HTML/CSS/JS
- **Hosting**: Docker + Render
