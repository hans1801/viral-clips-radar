"""Step 9. Usage: python pipeline/render.py <work> [only these: 01 05 ...] [--nosubs]
For every clip it writes two files:
  <clips>/shorts/<clip>.mp4      9:16 "streamer on top / gameplay below" with safe zones and subtitles
  <clips>/horizontal/<clip>.mp4  the original 16:9 cut, same times, no crop and no subtitles (to re-edit it your way)
  0-200 margin | 200-902 facecam | 902-1600 gameplay | 1600-1920 margin ; background = blurred gameplay.
clips.tsv col4 = cam "x,y,w,h" (aspect ~1.54; default 0,470,420,273)
          col5 = gameplay "w,h,x,y" (aspect 1.547, not overlapping the cam; default 1500,970,420,55)
          col4 = "none" when the stream has no facecam: large centered gameplay over a blurred background."""
import os, sys
from common import ffmpeg, encoder, read_clips, read_offsets
W = os.path.abspath(sys.argv[1]); args = sys.argv[2:]
nosubs = '--nosubs' in args; only = [a for a in args if not a.startswith('--')]
RAW = os.path.join(W, 'raw'); SUBS = os.path.join(W, 'subs'); OUT = os.path.join(os.path.dirname(W), 'shorts')
HOR = os.path.join(os.path.dirname(W), 'horizontal')
os.makedirs(OUT, exist_ok=True); os.makedirs(HOR, exist_ok=True); off = read_offsets(RAW); enc = encoder()
for c in read_clips(os.path.join(W, 'clips.tsv')):
    n = c['name']
    if only and n[:2] not in only: continue
    bg = "[bs]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:3,eq=brightness=-0.18[bg]"
    if c['cam'] == 'none':
        F = f"[0:v]split=2[bs][gs];{bg};[gs]scale=1080:-2[g];[bg][g]overlay=0:(H-h)/2[v0]"
        ypos = 1250
    else:
        cx, cy, cw, ch = map(int, c['cam'].split(',')) if c['cam'] else (0, 470, 420, 273)
        gw, gh, gx, gy = map(int, c['game'].split(',')) if c['game'] else (1500, 970, 420, 55)
        F = (f"[0:v]split=3[bs][cs][gs];{bg};[cs]crop={cw}:{ch}:{cx}:{cy},scale=1080:702[cam];"
             f"[gs]crop={gw}:{gh}:{gx}:{gy},scale=1080:698[g];[bg][cam]overlay=0:200[t1];[t1][g]overlay=0:902[v0]")
        ypos = 902
    ass = os.path.join(SUBS, n + '.ass')
    if not nosubs and os.path.exists(ass):
        if ypos != 902:
            s = open(ass, encoding='utf-8').read().replace('\\pos(540,902)', f'\\pos(540,{ypos})')
            open(ass, 'w', encoding='utf-8').write(s)
        F += f";[v0]ass={n}.ass,format=yuv420p[v]"     # relative path (cwd=subs) avoids trouble with C:\ on Windows
    else:
        F += ";[v0]format=yuv420p[v]"
    ffmpeg('-ss', str(c['a'] - off[n]), '-i', os.path.join(RAW, n + '.mp4'), '-t', str(c['b'] - c['a']),
           '-filter_complex', F, '-map', '[v]', '-map', '0:a', *enc, '-r', '60', '-c:a', 'aac', '-b:a', '192k',
           '-movflags', '+faststart', os.path.join(OUT, n + '.mp4'), cwd=SUBS if os.path.isdir(SUBS) else W)
    # original horizontal cut (re-encoded so it starts exactly on the frame, not on the previous keyframe)
    ffmpeg('-ss', str(c['a'] - off[n]), '-i', os.path.join(RAW, n + '.mp4'), '-t', str(c['b'] - c['a']),
           '-map', '0:v', '-map', '0:a', *enc, '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', os.path.join(HOR, n + '.mp4'))
    print('OK', n, flush=True)
