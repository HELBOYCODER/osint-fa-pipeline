#!/bin/bash
# 🔧 نصب کامل پیش‌نیازهای پیل‌لاین OSINT فارسی — «غول به تمام‌معنا» (Linux/WSL)
set -e
echo "🔍 نصب پیل‌لاین OSINT فارسی — نسخه کامل"

# ---------- سیستمی ----------
echo "==> ابزارهای سیستمی"
sudo apt-get update -qq
sudo apt-get install -y -qq \
  ffmpeg libimage-exiftool-perl \
  tesseract-ocr tesseract-ocr-fas tesseract-ocr-ara \
  python3 python3-pip python3-venv git curl jq

# ---------- ابزارهای دانلود ----------
echo "==> yt-dlp"
command -v yt-dlp >/dev/null || pip install yt-dlp 2>/dev/null || pipx install yt-dlp || {
  sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
  sudo chmod +x /usr/local/bin/yt-dlp
}

# ---------- محیط پایتون OSINT ----------
echo "==> venv پایتون (whisper فارسی + نجوم + تصویر)"
python3 -m venv ~/.venvs/osint 2>/dev/null || true
PIP=~/.venvs/osint/bin/pip
$PIP install -q --upgrade pip
# نکته حیاتی: av==12.3.0 (نسخه‌های جدید با faster-whisper تداخل دارند)
# نکته حیاتی: HF_ENDPOINT=hf-mirror.com (فیلترینگ/بلاک huggingface)
HF_ENDPOINT=https://hf-mirror.com $PIP install -q faster-whisper "av==12.3.0" pillow ephem numpy

# ---------- کلید Gemini (اختیاری ولی به‌شدت توصیه‌شده) ----------
# موتور OCR اصلی؛ بدون آن fallback به tesseract (کیفیت پایین‌تر برای فارسی)
if [ -z "$GEMINI_API_KEY" ]; then
  echo ""
  echo "⚠️  GEMINI_API_KEY تنظیم نشده."
  echo "   برای OCR فارسی دقیق، کلید رایگان از https://aistudio.google.com بگیر و:"
  echo '   echo "export GEMINI_API_KEY=کلید" >> ~/.bashrc && source ~/.bashrc'
  echo "   (بدون آن، ocr.py به tesseract آفلاین fallback می‌کند؛ ocr.py کلید را از docker کانتینر n8n هم می‌خواند)"
fi

# ---------- بررسی نصب ----------
echo ""
echo "==> بررسی نهایی"
for t in ffmpeg exiftool yt-dlp tesseract; do
  command -v $t >/dev/null && echo "✅ $t" || echo "❌ $t"
done
~/.venvs/osint/bin/python -c "import faster_whisper, PIL, ephem; print('✅ whisper + PIL + ephem')" 2>/dev/null \
  || echo "❌ venv ناقص — دستور pip بالا را دستی اجرا کن"

echo ""
echo "🚀 نصب کامل. استفاده:"
echo "   python3 scripts/orchestrator.py <لینک ریل یا مسیر عکس>"
echo "   python3 scripts/ocr.py <عکس>          # فقط OCR"
echo "   python3 scripts/moon.py <lat> <lon> <YYYY-MM-DD> <HH:MM> <tz>  # فاز ماه"
