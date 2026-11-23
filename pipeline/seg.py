"""Usage: python pipeline/seg.py <work> 1:05:00-1:07:00 [more ranges]
Every line with its exact VOD time, to start and end a clip on a complete sentence."""
import os, re, sys
from common import parse_t
W = sys.argv[1]; segs = []
for m in re.finditer(r'(\d\d):(\d\d):(\d\d),(\d+) --> .*?\n(.*?)(?:\n\n|\Z)', open(os.path.join(W, 'transcript.srt'), encoding='utf-8').read(), re.S):
    segs.append((int(m[1])*3600 + int(m[2])*60 + int(m[3]) + int(m[4])/1000, ' '.join(m[5].split())))
f = lambda s: f"{int(s)//3600}:{int(s)%3600//60:02d}:{s%60:05.2f}"
for r in sys.argv[2:]:
    a, b = map(parse_t, r.split('-')); print('=====', r)
    for s, t in segs:
        if a <= s <= b: print(f(s), t[:140])
