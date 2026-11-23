"""Step 6b. Usage: python pipeline/align.py <work>
Checks that each file in work/raw starts where offsets.txt says, by matching its audio against loud.json.
Every clip must say OK; if one says CHECK, that clip would come out out of sync."""
import os, sys, json, math, array, subprocess
from common import ff, read_offsets
W = sys.argv[1]; L = json.load(open(os.path.join(W, 'loud.json'))); RAW = os.path.join(W, 'raw')
for n, o in read_offsets(RAW).items():
    raw = subprocess.check_output([ff()[0], '-v', 'error', '-i', os.path.join(RAW, n + '.mp4'), '-vn', '-ac', '1', '-ar', '8000', '-f', 's16le', '-'])
    a = array.array('h'); a.frombytes(raw[:len(raw)//2*2]); Cl = []
    for i in range(len(a)//8000):
        s = a[i*8000:(i+1)*8000:4]; Cl.append(20*math.log10((math.sqrt(sum(x*x for x in s)/len(s)) or 1)/32768))
    best = min((sum((Cl[i]-L[t0+i])**2 for i in range(len(Cl)) if t0+i < len(L))/max(1, len(Cl)), t0)
               for t0 in range(max(0, o-120), min(len(L), o+120)))
    print(n, 'expected', o, 'audio', best[1], 'OK' if abs(best[1]-o) <= 1 else 'CHECK')
