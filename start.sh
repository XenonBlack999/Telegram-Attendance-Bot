#!/bin/bash
# --------------------------------------
# Start script for Telegram Attendance Bot
# --------------------------------------

# Activate virtual environment (if exists)
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run the bot
echo "🚀 Starting Telegram Bot..."
python3 bot.py
