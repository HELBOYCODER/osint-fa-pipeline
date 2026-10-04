import sys
from faster_whisper import WhisperModel
# usage: python tr.py <audio> [lang]
m = WhisperModel('small', device='cpu', compute_type='int8')
segs, info = m.transcribe(sys.argv[1], language=sys.argv[2] if len(sys.argv) > 2 else 'fa')
print('LANG:', info.language)
print(' '.join(s.text.strip() for s in segs))
