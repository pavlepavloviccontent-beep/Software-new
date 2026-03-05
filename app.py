import os
import re
import json
import shutil
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify

import instaloader
import whisper

app = Flask(__name__)

# Store analysis jobs in memory (use a DB for production)
jobs = {}
jobs_lock = threading.Lock()

DOWNLOAD_DIR = Path(tempfile.gettempdir()) / "insta_analyzer"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Lazy-load whisper model
_whisper_model = None
_whisper_lock = threading.Lock()


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        with _whisper_lock:
            if _whisper_model is None:
                _whisper_model = whisper.load_model("base")
    return _whisper_model


def extract_username(profile_input):
    """Extract Instagram username from a URL or plain text."""
    profile_input = profile_input.strip().rstrip("/")
    # Handle URLs like https://www.instagram.com/username/
    match = re.search(r"instagram\.com/([A-Za-z0-9._]+)", profile_input)
    if match:
        return match.group(1)
    # Handle plain username (possibly with @)
    return profile_input.lstrip("@")


def fetch_profile_videos(username):
    """Fetch all video posts from an Instagram profile using Instaloader."""
    loader = instaloader.Instaloader(
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    profile = instaloader.Profile.from_username(loader.context, username)

    videos = []
    for post in profile.get_posts():
        if not post.is_video:
            continue
        videos.append(
            {
                "shortcode": post.shortcode,
                "url": f"https://www.instagram.com/p/{post.shortcode}/",
                "video_url": post.video_url,
                "views": post.video_view_count or 0,
                "likes": post.likes,
                "comments": post.comments,
                "caption": (post.caption or "")[:200],
                "date": post.date_utc.isoformat(),
                "thumbnail": post.url,  # thumbnail image URL
            }
        )

    return videos, profile.full_name, profile.mediacount


def download_and_transcribe(video_url, shortcode):
    """Download a video and transcribe its audio using Whisper."""
    import subprocess

    video_dir = DOWNLOAD_DIR / shortcode
    video_dir.mkdir(exist_ok=True)
    audio_path = video_dir / "audio.mp3"

    try:
        # Use yt-dlp to download audio only
        subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "5",
                "-o", str(video_dir / "audio.%(ext)s"),
                "--no-playlist",
                "--quiet",
                video_url,
            ],
            check=True,
            timeout=120,
        )

        if not audio_path.exists():
            # yt-dlp might save with different name
            mp3_files = list(video_dir.glob("*.mp3"))
            if mp3_files:
                audio_path = mp3_files[0]
            else:
                return "[Could not extract audio]"

        model = get_whisper_model()
        result = model.transcribe(str(audio_path), language=None)
        return result.get("text", "").strip() or "[No speech detected]"

    except Exception as e:
        return f"[Transcription failed: {str(e)[:100]}]"
    finally:
        # Clean up downloaded files
        if video_dir.exists():
            shutil.rmtree(video_dir, ignore_errors=True)


def run_analysis(job_id, profile_input):
    """Background worker that performs the full analysis."""
    try:
        username = extract_username(profile_input)

        with jobs_lock:
            jobs[job_id]["status"] = "fetching"
            jobs[job_id]["message"] = f"Fetching videos from @{username}..."

        videos, full_name, media_count = fetch_profile_videos(username)

        if not videos:
            with jobs_lock:
                jobs[job_id]["status"] = "done"
                jobs[job_id]["message"] = "No videos found on this profile."
                jobs[job_id]["result"] = {
                    "username": username,
                    "full_name": full_name,
                    "total_videos": 0,
                    "top_videos": [],
                    "bottom_videos": [],
                }
            return

        # Sort by views
        videos.sort(key=lambda v: v["views"], reverse=True)

        top_15 = videos[:15]
        bottom_15 = videos[-15:] if len(videos) > 15 else videos[::-1][:15]

        total = len(top_15)
        with jobs_lock:
            jobs[job_id]["status"] = "transcribing"
            jobs[job_id]["message"] = f"Found {len(videos)} videos. Transcribing top {total}..."
            jobs[job_id]["progress"] = 0
            jobs[job_id]["progress_total"] = total

        # Transcribe top 15 videos
        for i, video in enumerate(top_15):
            with jobs_lock:
                jobs[job_id]["message"] = f"Transcribing video {i + 1}/{total}..."
                jobs[job_id]["progress"] = i

            transcript = download_and_transcribe(video["video_url"], video["shortcode"])
            video["transcript"] = transcript

        # Also attempt to transcribe bottom videos (skip if same as top)
        top_codes = {v["shortcode"] for v in top_15}
        bottom_to_transcribe = [v for v in bottom_15 if v["shortcode"] not in top_codes]

        if bottom_to_transcribe:
            with jobs_lock:
                jobs[job_id]["message"] = f"Transcribing least viral videos..."

            for video in bottom_to_transcribe:
                transcript = download_and_transcribe(video["video_url"], video["shortcode"])
                video["transcript"] = transcript

        # For bottom videos that overlap with top, copy transcript
        top_map = {v["shortcode"]: v.get("transcript", "") for v in top_15}
        for video in bottom_15:
            if "transcript" not in video and video["shortcode"] in top_map:
                video["transcript"] = top_map[video["shortcode"]]

        with jobs_lock:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["message"] = "Analysis complete!"
            jobs[job_id]["progress"] = total
            jobs[job_id]["result"] = {
                "username": username,
                "full_name": full_name,
                "total_videos": len(videos),
                "total_posts": media_count,
                "top_videos": top_15,
                "bottom_videos": bottom_15,
            }

    except instaloader.exceptions.ProfileNotExistsException:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["message"] = "Profile not found. Check the username and try again."
    except instaloader.exceptions.LoginRequiredException:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["message"] = "Instagram requires login to view this profile. The profile may be private."
    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["message"] = f"Error: {str(e)[:200]}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    profile_input = data.get("profile", "").strip()

    if not profile_input:
        return jsonify({"error": "Please provide an Instagram profile URL or username."}), 400

    job_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + extract_username(profile_input)

    with jobs_lock:
        jobs[job_id] = {
            "status": "starting",
            "message": "Starting analysis...",
            "progress": 0,
            "progress_total": 0,
            "result": None,
        }

    thread = threading.Thread(target=run_analysis, args=(job_id, profile_input), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
