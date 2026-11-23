"""Step 10. Usage: python pipeline/check.py <work> [language=auto]
Checks every short: 1080x1920, audio and its loudness, duration, first and last words (they must be complete sentences),
and creates <clips>/shorts/_contact_sheet.png with one frame from each."""
import os, sys, re, json, subprocess, glob
from common import ff, ffmpeg, whisper_model, load_audio, lang_arg
W = os.path.abspath(sys.argv[1]); lang = lang_arg(sys.argv[2] if len(sys.argv) > 2 else 'auto')
if lang is None:
    lang = json.load(open(os.path.join(W, 'meta.json'), encoding='utf-8')).get('language')
OUT = os.path.join(os.path.dirname(W), 'shorts'); FR = os.path.join(W, 'frames'); os.makedirs(FR, exist_ok=True)
wm = whisper_model('small')
vids = sorted(glob.glob(os.path.join(OUT, '*.mp4')))
def words(audio):
    return ' '.join(s.text.strip() for s in wm.transcribe(audio, language=lang, vad_filter=True)[0])
thumbs = []
for v in vids:
    probe = subprocess.run([ff()[1], '-v', 'error', '-show_entries', 'stream=codec_type,width,height:format=duration', '-of', 'default=nw=1', v], capture_output=True, text=True).stdout
    w = re.search(r'width=(\d+)', probe); h = re.search(r'height=(\d+)', probe); d = float(re.search(r'duration=([\d.]+)', probe)[1])
    vol = re.search(r'mean_volume: ([-\d.]+)', subprocess.run([ff()[0], '-hide_banner', '-i', v, '-af', 'volumedetect', '-vn', '-f', 'null', '-'], capture_output=True, text=True).stderr)
    hw = load_audio(v, start=0, dur=7); tw = load_audio(v, start=max(0, d-7))
    ok = w and w[1] == '1080' and h[1] == '1920' and vol
    print(f"{'OK ' if ok else 'BAD'} {os.path.basename(v)}  {d:.0f}s  {w[1] if w else '?'}x{h[1] if h else '?'}  {vol[1] if vol else 'NO AUDIO'} dB")
    print(f"     START: {words(hw)[:120]}\n     END:   {words(tw)[-120:]}")
    th = os.path.join(FR, f'_th{len(thumbs)}.png'); ffmpeg('-ss', str(d/2), '-i', v, '-frames:v', '1', '-vf', 'scale=216:384', th); thumbs.append(th)
if thumbs:
    cols = min(6, len(thumbs))
    ins = sum((['-i', p] for p in thumbs), [])
    lay = '|'.join(f'{(i%cols)*216}_{(i//cols)*384}' for i in range(len(thumbs)))
    flt = ''.join(f'[{i}:v]' for i in range(len(thumbs))) + (f'xstack=inputs={len(thumbs)}:layout={lay}:fill=black' if len(thumbs) > 1 else 'null')
    ffmpeg(*ins, '-filter_complex', flt, os.path.join(OUT, '_contact_sheet.png'))
    for p in thumbs: os.remove(p)
    print('Contact sheet:', os.path.join(OUT, '_contact_sheet.png'))
