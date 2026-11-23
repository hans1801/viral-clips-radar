"""Step 6. Usage: python pipeline/build_raw.py <work>
Downloads only the video segments (1080p60, or the best there is) that cover each clip in work/clips.tsv and joins them in work/raw/.
work/raw/offsets.txt: name, and the VOD second where each file starts."""
import os, sys, json
from concurrent.futures import ThreadPoolExecutor
from common import ytdlp, download, read_clips
W = sys.argv[1]; meta = json.load(open(os.path.join(W, 'meta.json'), encoding='utf-8'))
m3u8 = ''
for fmt in ('1080p60', '1080p', '720p60', 'best'):
    try:
        m3u8 = ytdlp('-f', fmt, '-g', meta['url']).splitlines()[0]; print('Format:', fmt); break
    except Exception:
        pass
base = m3u8.rsplit('/', 1)[0]
pl = os.path.join(W, 'video.m3u8'); download(m3u8, pl)
lines = open(pl, encoding='utf-8').read().splitlines()
init = ([l.split('URI="')[1].split('"')[0] for l in lines if l.startswith('#EXT-X-MAP')] or [None])[0]
segs = [l for l in lines if l and not l.startswith('#')]   # 10-second segments, in order
RAW, SEGS = os.path.join(W, 'raw'), os.path.join(W, 'segs')
os.makedirs(RAW, exist_ok=True); os.makedirs(SEGS, exist_ok=True)
def get(n):
    p = os.path.join(SEGS, n.replace('/', '_'))
    if not (os.path.exists(p) and os.path.getsize(p) > 0): download(f'{base}/{n}', p)
    return p
clips = []
for c in read_clips(os.path.join(W, 'clips.tsv')):
    s0 = max(0, int(c['a']-10)//10); s1 = min(len(segs)-1, int(c['b']+10)//10)
    clips.append((c['name'], s0, s1))
need = sorted({i for _, s0, s1 in clips for i in range(s0, s1+1)})
with ThreadPoolExecutor(16) as ex:
    list(ex.map(get, ([init] if init else []) + [segs[i] for i in need]))
with open(os.path.join(RAW, 'offsets.txt'), 'w') as off:
    for n, s0, s1 in clips:
        with open(os.path.join(RAW, n + '.mp4'), 'wb') as o:
            if init: o.write(open(get(init), 'rb').read())
            for i in range(s0, s1+1): o.write(open(get(segs[i]), 'rb').read())
        off.write(f"{n} {s0*10} {s0} {s1}\n")
print('OK:', len(clips), 'clips,', len(need), 'segments')
