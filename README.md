# 🔍 پیل‌لاین OSINT فارسی برای عکس و ریل (ایجنت-آماده)

> روش ترکیبی که توسط ایجنت Hermes (مدل ارساز) در عمل تست و تایید شده — از دانلود ریل اینستاگرام تا لوکیت خیابان به خیابان.
> هر ایجنتی (Hermes، Claude، ChatGPT، ...) این فایل را بدهد، دقیقاً همین چرخه را اجرا می‌کند.

## ⚡ شروع سریع (۲ دستور)

```bash
git clone https://github.com/HELBOYCODER/osint-fa-pipeline && cd osint-fa-pipeline
./install.sh                                        # همه پیش‌نیازها خودکار
python3 scripts/orchestrator.py <لینک ریل یا مسیر عکس>   # چرخه کامل + گزارش
```

خروجی: `osint_out/گزارش.md` — شامل متادیتا، EXIF، متن‌های OCR (تابلو/پلاک/دیوارنوشته) و پیاده‌سازی صوت.
برای عکس‌های شب با لوکیت: `python3 scripts/moon.py 35.69 51.39 2026-10-04 21:30 3.5`

---

## چرخه کامل (۴ مرحله)

```
عکس/ریل  →  ① دانلود + متادیتا  →  ② بینایی (فریم‌ها + OCR فارسی)  →  ③ صوت (Whisper فارسی)  →  ④ لوکیت (EXIF / متن تابلو / ماه / تطبیق وب)
```

---

## مرحله ۱ — دانلود و متادیتا

```bash
# ریل/پست اینستاگرام (yt-dlp):
cd /tmp && yt-dlp --no-playlist -o "ig_reel.%(ext)s" "<URL>"
yt-dlp --no-playlist -J "<URL>"   # متادیتا: title / uploader / description / likes / timestamp

# استخراج ورودی‌های تحلیل:
ffmpeg -y -i reel.mp4 -vn -ar 16000 -ac 1 audio.wav                    # برای پیاده‌سازی صوت
mkdir frames && ffmpeg -y -i reel.mp4 -vf fps=1/10 frames/f_%02d.jpg   # ۱ فریم هر ۱۰ ثانیه

# EXIF (اولین چیزی که باید چک شود — اغلب توسط تلگرام/اینستا پاک می‌شود):
exiftool image.jpg          # GPS؟ دستگاه؟ زمان؟
python3 -c "from PIL import Image; im=Image.open('image.jpg'); print(im._getexif())"
```

**قانون:** EXIF خالی ≠ بن‌بست. از مرحله ۲ ادامه بده.

---

## مرحله ۲ — تحلیل بینایی + OCR فارسی (کلید طلایی)

هر فریم را به مدل بینایی بده، **دو بار**:
1. **سؤال باز:** «چه چیزی هست؟ متن فارسی؟ نشانه‌ها؟ معماری؟ پوشش گیاهی؟»
2. **کراپ هدفمند + بزرگ‌نمایی ۳x** روی هر تابلو/متن/پلاک — این جایی است که لوکیت پیدا می‌شود:

```python
from PIL import Image
im = Image.open("photo.jpg"); w,h = im.size
# کراپ ناحیه تابلو و بزرگ‌نمایی با LANCZOS
c = im.crop((x1,y1,x2,y2)); c = c.resize((c.width*3, c.height*3), Image.LANCZOS)
c.save("sign_3x.jpg")
```

سپس متن خوانده‌شده را **وب‌سرچ کن** — مثال واقعی:
- تابلوی نارنجی فلش‌دار → «خبرگزاری بین‌المللی قرآن / ایکنا»
- وب‌سرچ آدرس رسمی → `تهران، خیابان انقلاب → قدس → بزرگمهر، پلاک ۸۵` ✅ لوکیت دقیق

**شواهد محیطی که باید ثبت کنی:** معماری (بام شیروانی/مسطح، آجر/سیمان)، پوشش گیاهی (چنار=خیابان‌کشی شهری ایران)، فرش شهری (آبخوری/سقاخانه)، پلاک در، پلاک خودرو (کد استان در مربع سمت راست!)، اسکای‌لاین، دیوارنگاره‌ها.

---

## مرحله ۳ — پیاده‌سازی صوت (فارسی)

```bash
# محیط (یک‌بار): faster-whisper با av پین‌شده
uv venv ~/.venvs/osint && uv pip install --python ~/.venvs/osint/bin/python faster-whisper "av==12.3.0"

# اجرا — دقت کن: HuggingFace مستقیم بلاک است، همیشه از میرور:
HF_ENDPOINT=https://hf-mirror.com ~/.venvs/osint/bin/python tr.py audio.wav
```

`tr.py`:
```python
import sys
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
segs, info = m.transcribe(sys.argv[1], language='fa')   # 'fa' یا None برای تشخیص خودکار
print(' '.join(s.text.strip() for s in segs))
```

⚠️ `small` روی فارسی گاهی نامفهوم است؛ gist کافی است. `medium`/`large-v3` دقیق‌تر ولی روی CPU دو هسته‌ای ~۵ دقیقه/ریل.

**در صوت دنبال این باش:** نام مکان، نام نرم‌افزار/ابزار، لهجه، اصطلاحات محلی.

---

## مرحله ۴ — لوکیت (۴ تکنیک به ترتیب)

### ۴-الف. EXIF/GPS
اگر بود → تمام. نیست → برو ۴-ب.

### ۴-ب. متن/تابلو (بیشترین بازده در ایران)
تابلوهای نارنجی شهرداری، تابلوهای خیابان، پلاک مغازه، دیوارنوشته → بزرگ‌نمایی → خواندن → وب‌سرچ آدرس رسمی سازمان/محل.

### ۴-ج. فاز ماه (برای عکس‌های شب — وقتی زمان تقریبی داری)
```bash
uv pip install ephem   # آفلاین، بدون دانلود ephemeris
```
```python
import ephem
obs = ephem.Observer(); obs.lat, obs.lon = '35.69', '51.39'   # شهر حدسی
obs.date = ephem.date((2026, 10, 4, 18, 0, 0))                # UTC! (IRST = UTC+3:30)
m = ephem.Moon(); m.compute(obs)
print('azimuth:', float(ephem.degrees(m.az)), 'altitude:', float(ephem.degrees(m.alt)))
```
موقعیت ماه در عکس → آزیموت دوربین → روی نقشه، برج/کوه/دکل در همان راستای آزیموت را پیدا کن.

### ۴-د. جستجوی معکوس (برای عکس‌های عمومی؛ عکس شخصی چیزی پیدا نمی‌کند)
- Google Lens / Yandex / Bing Visual / TinEye
- چهره: PimEyes
- ابزار: [GONZOsint/gvision](https://github.com/GONZOsint/gvision)

### ۴-ه. جعبه‌ابزار OSINT آماده
| هدف | ابزار |
|---|---|
| تلگرام | [Telepathy-Community](https://github.com/prose-intelligence-ltd/Telepathy-Community) |
| همه‌کاره | [divinelabio/Argus](https://github.com/divinelabio/Argus) |
| اینستاگرام | igsearch-osint |
| EXIF | exiftool |
| دانلود هر پلتفرم | yt-dlp |

---

## اسکیل آماده برای ایجنت‌ها (Hermes/Claude Skills)

`skills/ig-reel-osint/SKILL.md` را در پوشه skills ایجنتت کپی کن — به محض دیدن لینک ریل/عکس، همین چرخه اجرا می‌شود.

## مثال‌های واقعی (تست‌شده)

1. **ریل اینستاگرام** `instagram.com/reel/DeCRUK9yGjS` → دانلود ✓، ۶ فریم ✓، صوت فارسی ✓ → تشخیص: آموزش فتوگرامتری با RealityCapture، آپلودر «محمد گنجی» (mkenzo_official)
2. **عکس شب (برج نوری)** → EXIF پاک، تحلیل ساختار دکل (تاج نورانی + بکیون) → در انتظار زمان/جهت برای محاسبه فاز ماه
3. **عکس خیابان (روز)** → OCR تابلوی نارنجی → «ایکنا» → وب‌سرچ → **تهران، خیابان قدس/بزرگمهر** ✅

## نکات سخت‌گained (درس‌های عملی)
- هوش مصنوعی بینایی را با سؤال وسواسی بپرس؛ اگر مطمئن نیست «حدس نزن» بگو — خواندن غلط تابلو = لوکیت غلط
- کراپ + بزرگ‌نمایی LANCZOS قبل از OCR الزامی است
- HuggingFace از سرور ایران/سرورهای ابری بلاک است → `HF_ENDPOINT=https://hf-mirror.com`
- `av` جدیدتر با faster-whisper ناسازگار است → `av==12.3.0`
- عکس خصوصی در جستجوی معکوس هیچ‌وقت نمی‌آید — وقت را هدر نده، برو سراغ متن/ماه

## لایسنس
MIT — رایگان برای همه.
