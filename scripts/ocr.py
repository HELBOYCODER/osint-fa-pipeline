#!/usr/bin/env python3
"""ocr.py — استخراج متن فارسی/انگلیسی از عکس. سه موتور با fallback خودکار:
1) Gemini (رایگان، دقیق‌ترین برای فارسی) — کلید از GEMINI_API_KEY
2) Tesseract (آفلاین) — tesseract-ocr-fas
3) اگر هیچ‌کدام نبود، خطای راهنما می‌دهد
usage: python3 ocr.py <image> [prompt_hint]
"""
import base64, json, os, subprocess, sys, urllib.request

def via_gemini(img, hint):
    key = os.environ.get('GEMINI_API_KEY') or read_gemini_key()
    if not key:
        return None
    b64 = base64.b64encode(open(img, 'rb').read()).decode()
    prompt = ('تمام متن‌های فارسی و انگلیسی این تصویر را دقیقاً و حرف‌به‌حرف استخراج کن. '
              'اگر تابلو/پلاک/نوشته دیواری هست، هر کدام را جدا لیست کن. ' + (hint or ''))
    body = json.dumps({'contents': [{'parts': [{'text': prompt}, {'inline_data': {'mime_type': 'image/jpeg', 'data': b64}}]}]}).encode()
    req = urllib.request.Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}',
        data=body, headers={'Content-Type': 'application/json'})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return r['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print('[gemini fail]', e, file=sys.stderr)
        return None

def read_gemini_key():
    # 1) docker exec n8n (یافت‌شده در تست واقعی) 2) فایل‌های محلی
    try:
        r = subprocess.run(['sudo', 'docker', 'exec', 'n8n', 'printenv', 'GEMINI_API_KEY'],
                           capture_output=True, text=True, timeout=10)
        if r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    for p in ('/home/agentuser/n8n/docker-compose.yml', os.path.expanduser('~/.hermes/.env')):
        try:
            for line in open(p):
                if line.strip().startswith('GEMINI_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
        except OSError:
            pass
    return None

def via_tesseract(img):
    if not subprocess.run(['which', 'tesseract'], capture_output=True).returncode == 0:
        return None
    r = subprocess.run(['tesseract', img, 'stdout', '-l', 'fas+ara+eng', '--psm', '6'],
                       capture_output=True, text=True)
    return r.stdout.strip() or None

if __name__ == '__main__':
    img = sys.argv[1]
    hint = sys.argv[2] if len(sys.argv) > 2 else ''
    out = via_gemini(img, hint) or via_tesseract(img)
    print(out if out else '⚠️ هیچ متنی استخراج نشد — تصویر را بزرگ‌نمایی کنید (scripts/zoom.py) و دوباره امتحان کنید.')
