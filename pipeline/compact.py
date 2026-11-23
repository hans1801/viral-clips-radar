"""Usage: python pipeline/compact.py <work>   -> work/compact.txt
The transcript in 30-second blocks with VOD time, to read it whole and find moments."""
import os, re, sys, collections
W = sys.argv[1]; B = collections.OrderedDict()
for m in re.finditer(r'(\d\d):(\d\d):(\d\d),\d+ --> .*?\n(.*?)(?:\n\n|\Z)', open(os.path.join(W, 'transcript.srt'), encoding='utf-8').read(), re.S):
    t = int(m[1])*3600 + int(m[2])*60 + int(m[3])
    B.setdefault(t//30*30, []).append(' '.join(m[4].split()))
with open(os.path.join(W, 'compact.txt'), 'w', encoding='utf-8') as f:
    for k, v in B.items(): f.write(f"[{k//3600}:{k%3600//60:02d}:{k%60:02d}] " + ' '.join(v) + '\n')
print('OK:', len(B), 'blocks')
