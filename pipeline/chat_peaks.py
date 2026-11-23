"""Step 4b. Usage: python pipeline/chat_peaks.py <work> [N=35]
Ranks the chat's LAUGHTER and REACTION spikes (z-score vs. ±7 min) with what the streamer said right before.
Writes work/chat_per_min.tsv and work/chat_peaks.txt.
Key idea: in big or slow-mode chats the total message count is flat; what changes is the KIND of message."""
import json, os, re, sys, statistics as st, collections
W = sys.argv[1]; TOP = int(sys.argv[2]) if len(sys.argv) > 2 else 35
d = json.load(open(os.path.join(W, 'chat.json'), encoding='utf-8'))
C = [(int(c['content_offset_seconds']), (c['message']['body'] or '').strip()) for c in d['comments']]
N = max(t for t, _ in C) + 1
laugh = re.compile(r'^(ju+|lol+|xd+|ja(ja)+j*|jsj\w*|haha\w*|kekw|lmao|lmfao|icant|rofl)\b|KEKW|OMEGALUL|LUL|ICANT', re.I)
shock = re.compile(r'^(no+o+|wtf|saj|f|d:|que cojones|pog\w*|goty|ostia|hostia|omg|wow|holy)\b|QueCojonesBro|monkaS|Pog', re.I)
L = [0]*N; S = [0]*N; T = [0]*N
for t, m in C:
    T[t] += 1
    if laugh.search(m): L[t] += 1
    elif shock.search(m): S[t] += 1
with open(os.path.join(W, 'chat_per_min.tsv'), 'w', encoding='utf-8') as f:
    f.write('min\ttotal\tlaughs\treactions\n')
    for i in range((N+59)//60): f.write(f"{i//60}:{i%60:02d}\t{sum(T[i*60:i*60+60])}\t{sum(L[i*60:i*60+60])}\t{sum(S[i*60:i*60+60])}\n")
Wn = 15
def roll(A):
    s = [0]*(N+1)
    for i in range(N): s[i+1] = s[i] + A[i]
    return [s[min(N, i+Wn)] - s[i] for i in range(N)]
RL, RS = roll(L), roll(S)
def z(R, i):
    w = R[max(0, i-420):i+420:15]; return (R[i] - st.median(w)) / (st.pstdev(w) or 1)
sc = sorted(((z(RL, i) + 0.7*z(RS, i), i, RL[i], RS[i]) for i in range(min(600, N//10), N-Wn, 5)), reverse=True)
pk = []
for s in sc:
    if all(abs(s[1]-p[1]) > 120 for p in pk): pk.append(s)
    if len(pk) >= TOP: break
srt = os.path.join(W, 'transcript.srt')
segs = [(int(m[1])*3600 + int(m[2])*60 + int(m[3]), ' '.join(m[4].split()))
        for m in re.finditer(r'(\d\d):(\d\d):(\d\d),\d+ --> .*?\n(.*?)(?:\n\n|\Z)', open(srt, encoding='utf-8').read(), re.S)] if os.path.exists(srt) else []
f = lambda s: f"{s//3600}:{s%3600//60:02d}:{s%60:02d}"
out = [f"messages {len(C)} | avg/min {round(len(C)/N*60)}"]
for s, i, a, b in pk:
    top = collections.Counter(m[:18] for t, m in C if i <= t < i+Wn).most_common(3)
    tx = ' | '.join(x for t, x in segs if i-25 <= t <= i+5)[-230:]
    out.append(f"{f(i)} z={s:.1f} laughs={a} reactions={b} {top}\n    >> {tx}")
open(os.path.join(W, 'chat_peaks.txt'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('\n'.join(out))
