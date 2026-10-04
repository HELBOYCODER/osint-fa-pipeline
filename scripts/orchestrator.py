#!/usr/bin/env python3
"""orchestrator.py — اجرای کامل چرخه OSINT روی یک ریل/عکس با یک دستور.
usage:
  python3 orchestrator.py <URL یا مسیر عکس> [--outdir DIR]

خروجی: گزارش متنی گزارش.md در outdir شامل متادیتا، EXIF، OCR تابلوها، پیاده‌سازی صوت و سرنخ‌های لوکیت.
"""
import json, os, shutil, subprocess, sys

def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)

def have(t):
    return shutil.which(t) is not None

def main():
    target = sys.argv[1]
    outdir = sys.argv[sys.argv.index('--outdir')+1] if '--outdir' in sys.argv else 'osint_out'
    os.makedirs(outdir, exist_ok=True)
    report = ['# گزارش OSINT\n']

    if target.startswith('http'):
        # مرحله ۱: دانلود با yt-dlp
        if not have('yt-dlp'):
            sys.exit('yt-dlp نصب نیست — install.sh را اجرا کن')
        r = sh(f'yt-dlp --no-playlist -J "{target}"')
        if r.returncode != 0:
            sys.exit(f'دانلود ناموفق: {r.stderr[:300]}')
        meta = json.loads(r.stdout)
        url_media = meta['requested_downloads'][0]['filepath'] if meta.get('requested_downloads') else None
        report += ['## متادیتا', f"- آپلودر: {meta.get('uploader')} (@{meta.get('uploader_id')})",
                   f"- عنوان: {meta.get('title')}", f"- تاریخ: {meta.get('timestamp')}",
                   f"- لایک: {meta.get('like_count')}", '']
        if not url_media:
            sys.exit('فایل رسانه پیدا نشد')
        # صوت و فریم‌ها
        audio = os.path.join(outdir, 'audio.wav')
        sh(f'ffmpeg -y -i "{url_media}" -vn -ac 1 -ar 16000 "{audio}"')
        sh(f'ffmpeg -y -i "{url_media}" -vf fps=1/10 "{outdir}/f_%02d.jpg"')
        media = url_media
    else:
        media, audio = target, None
        sh(f'ffmpeg -y -i "{media}" -vf fps=1/10 "{outdir}/f_%02d.jpg"') if media.lower().endswith(('.mp4','.mov','.webm')) else None
        shutil.copy(media, outdir)

    # مرحله ۲: EXIF
    if have('exiftool'):
        r = sh(f'exiftool -j "{media}"')
        exif = json.loads(r.stdout)[0] if r.stdout else {}
        gps = {k: v for k, v in exif.items() if 'GPS' in k}
        report += ['## EXIF', (f'- GPS: {gps}' if gps else '- بدون GPS (پاک‌شده — ادامه با روش‌های بصری)'), '']

    # مرحله ۳: OCR روی فریم‌ها (حداکثر ۶ فریم)
    ocr = os.path.join(outdir, '..', 'scripts', 'ocr.py')
    ocr = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ocr.py')
    zoom = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zoom.py')
    texts = []
    frames = sorted(f for f in os.listdir(outdir) if f.startswith('f_') and f.endswith('.jpg'))[:6]
    if not frames:
        # عکس ثابت: خود فایل را به‌عنوان فریم بگیر
        base = os.path.basename(media)
        if base.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) and os.path.exists(os.path.join(outdir, base)):
            frames = [base]
    zoom_venv = sh('ls ~/.venvs/osint/bin/python 2>/dev/null').stdout.strip() or 'python3'
    for f in frames:
        path = os.path.join(outdir, f)
        # full frame + 4 quadrant zooms (تابلوها معمولاً کوچک‌اند — OCR روی کراپ‌ها ضروری)
        from PIL import Image
        im = Image.open(path); W, H = im.size
        crops = [('full', path)] + [
            (f'q{i}', f'/tmp/_q{f}_{i}.jpg') for i in range(4)]
        boxes = [(0,0,W//2,H//2), (W//2,0,W,H//2), (0,H//2,W//2,H), (W//2,H//2,W,H)]
        for (name, out), box in zip(crops[1:], boxes):
            sh(f'{zoom_venv} {zoom} {path} {box[0]} {box[1]} {box[2]} {box[3]} {out} 2')
        for name, cpath in crops:
            t = sh(f'python3 {ocr} {cpath}').stdout.strip()
            if t and 'استخراج نشد' not in t and len(t) > 5:
                texts.append(f'[{f}/{name}] {t[:300]}')
    report += ['## متن‌های استخراج‌شده (OCR)'] + (texts or ['- هیچ متنی یافت نشد']) + ['']

    # مرحله ۴: صوت
    if audio and os.path.exists(audio) and os.path.getsize(audio) > 1000:
        py = sh('ls ~/.venvs/osint/bin/python 2>/dev/null').stdout.strip()
        if py:
            tr = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tr.py')
            env = {**os.environ, 'HF_ENDPOINT': 'https://hf-mirror.com'}
            r = subprocess.run([py, tr, audio], capture_output=True, text=True, env=env, timeout=600)
            report += ['## صوت (whisper)'] + [r.stdout.strip()[:1000] or '- خالی'] + ['']

    out = os.path.join(outdir, 'گزارش.md')
    open(out, 'w').write('\n'.join(report))
    print(f'✅ گزارش: {out}')
    print('\n'.join(report))

if __name__ == '__main__':
    main()
