"""Step 2. Usage: python pipeline/fetch_audio.py <work>
Downloads the VOD audio as segments in parallel (not yt-dlp's download, which runs at real-time speed on live VODs),
creates audio16.wav (mono 16 kHz) and loud.json (dBFS for every second of the VOD) and finds the OFFSET (where real sound starts)."""
import os, sys, json, math, array, subprocess
from concurrent.futures import ThreadPoolExecutor
from common import ytdlp, download, ff, ffmpeg, save_json

W = sys.argv[1]; meta = json.load(open(os.path.join(W, 'meta.json'), encoding='utf-8'))
m3u8 = ''
for fmt in ('Audio_Only', 'audio_only', 'bestaudio', 'worst'):
    try:
        m3u8 = ytdlp('-f', fmt, '-g', meta['url']).splitlines()[0]; break
    except Exception:
        pass
if not m3u8:
    sys.exit("Couldn't find the VOD's audio.")
base = m3u8.rsplit('/', 1)[0]
pl = os.path.join(W, 'audio.m3u8'); download(m3u8, pl)
lines = open(pl, encoding='utf-8').read().splitlines()
init = [l.split('URI="')[1].split('"')[0] for l in lines if l.startswith('#EXT-X-MAP')]
segs = [l for l in lines if l and not l.startswith('#')]
D = os.path.join(W, 'asegs'); os.makedirs(D, exist_ok=True)
names = init + segs
def get(n):
    p = os.path.join(D, n.replace('/', '_'))
    if not (os.path.exists(p) and os.path.getsize(p) > 0):
        download(f'{base}/{n}', p)
print(f'Downloading {len(segs)} audio segments…', flush=True)
with ThreadPoolExecutor(24) as ex:
    list(ex.map(get, names))
cat = os.path.join(W, 'audio_cat.mp4')
with open(cat, 'wb') as o:
    for n in names:
        o.write(open(os.path.join(D, n.replace('/', '_')), 'rb').read())
ffmpeg('-i', cat, '-vn', '-ac', '1', '-ar', '16000', os.path.join(W, 'audio16.wav'))
# loudness per second (streamed, 8 kHz)
p = subprocess.Popen([ff()[0], '-v', 'error', '-i', os.path.join(W, 'audio16.wav'), '-ac', '1', '-ar', '8000', '-f', 's16le', '-'], stdout=subprocess.PIPE)
L = []
while True:
    b = p.stdout.read(16000)
    if len(b) < 16000:
        break
    a = array.array('h'); a.frombytes(b); s = a[::4]
    L.append(round(20*math.log10((math.sqrt(sum(x*x for x in s)/len(s)) or 1)/32768), 2))
p.wait()
save_json(L, os.path.join(W, 'loud.json'))
first = next((i for i, x in enumerate(L) if x > -50), 0)
offset = max(0, first - 20)
muted = []; s0 = None
for i, x in enumerate(L + [0]):
    if x < -70 and s0 is None: s0 = i
    if x >= -70 and s0 is not None:
        if i - s0 >= 5 and s0 > first: muted.append([s0, i])
        s0 = None
meta.update({'offset': offset, 'audio_seconds': len(L), 'muted': muted})
save_json(meta, os.path.join(W, 'meta.json'))
os.remove(cat)
print(f'OK: {len(L)} s of audio, OFFSET={offset}, muted ranges={len(muted)}')
