#!/bin/bash
# Instagram Viral Analyzer - Setup Script
# Run this once to install all dependencies

set -e

echo "=== Instagram Viral Analyzer Setup ==="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required. Install it first."
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check for ffmpeg (needed by whisper)
if ! command -v ffmpeg &> /dev/null; then
    echo ""
    echo "WARNING: ffmpeg is not installed."
    echo "Whisper needs ffmpeg for audio processing."
    echo "Install it with:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS:         brew install ffmpeg"
    echo "  Windows:       choco install ffmpeg"
fi

echo ""
echo "=== Setup complete! ==="
echo "Run the app with: ./run.sh"
