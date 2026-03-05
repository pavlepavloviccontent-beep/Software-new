#!/bin/bash
# Instagram Viral Analyzer - Run Script

set -e

if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting Instagram Viral Analyzer..."
echo "Open http://localhost:5000 on your phone or browser"
echo ""

python3 app.py
