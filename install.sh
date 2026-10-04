#!/bin/bash
# نصب یک‌خطی پیل‌لاین OSINT فارسی (Linux/WSL)
set -e
echo "🔍 نصب پیل‌لاین OSINT فارسی..."

# ابزارهای سیستمی
command -v ffmpeg >/dev/null || sudo apt install -y ffmpeg
command -v exiftool >/dev/null || sudo apt install -y libimage-exiftool-perl
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh

# محیط پایتون: whisper فارسی + ابزار تصویر/نجوم
uv venv ~/.venvs/osint || true
uv pip install --python ~/.venvs/osint/bin/python faster-whisper "av==12.3.0" pillow ephem numpy

# yt-dlp
command -v yt-dlp >/dev/null || pip install yt-dlp || pipx install yt-dlp

echo "✅ نصب کامل — حالا اسکریپت‌های پوشه scripts/ را استفاده کن."
echo "   نکته: برای Whisper همیشه HF_ENDPOINT=https://hf-mirror.com بگذار."
