"""Step 7. Usage: python pipeline/frames.py <work>
For each clip: work/frames/<clip>_grid.png (8 frames, to see whether the facecam moves)
and work/frames/<clip>_full.png (one full-resolution frame with a 100 px grid, to measure it).
Default position used by render.py: cam 0,470,420,273 (in 1920x1080)."""
import os, sys
from common import ffmpeg, read_clips, read_offsets
W = sys.argv[1]; RAW = os.path.join(W, 'raw'); F = os.path.join(W, 'frames'); os.makedirs(F, exist_ok=True)
off = read_offsets(RAW)
for c in read_clips(os.path.join(W, 'clips.tsv')):
    n = c['name']; src = os.path.join(RAW, n + '.mp4'); rel = c['a'] - off[n]; dur = c['b'] - c['a']
    tmp = []
    for j in range(8):
        p = os.path.join(F, f'_{n}_{j}.png'); tmp.append(p)
        ffmpeg('-ss', f'{rel + j*dur/8:.1f}', '-i', src, '-frames:v', '1', '-vf', 'scale=480:-2', p)
    ins = sum((['-i', p] for p in tmp), [])
    lay = '|'.join(f'{(i%4)*480}_{(i//4)*270}' for i in range(8))
    ffmpeg(*ins, '-filter_complex', ''.join(f'[{i}:v]' for i in range(8)) + f'xstack=inputs=8:layout={lay}', os.path.join(F, f'{n}_grid.png'))
    for p in tmp: os.remove(p)
    ffmpeg('-ss', f'{rel + dur/2:.1f}', '-i', src, '-frames:v', '1', '-vf', 'drawgrid=w=100:h=100:t=1:c=yellow@0.5', os.path.join(F, f'{n}_full.png'))
    print('OK', n)
