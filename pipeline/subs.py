"""Step 8. Usage: python pipeline/subs.py <work> [language=auto] [--no-censor]
Transcribes each clip word by word (faster-whisper) and writes work/subs/<clip>.ass:
short UPPERCASE lines, Arial Black, black outline, centered on the cam/gameplay seam (y=902).
Swear words are masked in the text (PUTA -> P*TA, FUCK -> F*CK) unless --no-censor; the audio is untouched.
'auto' uses the language detected by transcribe.py (meta.json) or detects it per clip."""
import os, re, sys, json
from common import read_clips, read_offsets, whisper_model, load_audio, lang_arg
argv = [a for a in sys.argv[1:] if not a.startswith('--')]; censor = '--no-censor' not in sys.argv
W = argv[0]; lang = lang_arg(argv[1] if len(argv) > 1 else 'auto')
if lang is None:
    lang = json.load(open(os.path.join(W, 'meta.json'), encoding='utf-8')).get('language')
RAW = os.path.join(W, 'raw'); OUT = os.path.join(W, 'subs'); os.makedirs(OUT, exist_ok=True)
wm = whisper_model('small')
HDR = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Arial Black,68,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,7,3,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
# whisper hallucinations over music, in Spanish and English
junk = re.compile(r'[\[\]\*♪]|suscr[ií]bete|gracias por ver|subt[ií]tul|subscribe|thanks for watching', re.I)
# swear words (Spanish + English). Matched on the word stem, so plurals and variants are caught too.
SWEAR = re.compile(r"\b(put[ao]s?|putada|putiza|hijueputa|joder|jodid[ao]s?|j[oó]dete|coñ[oa]|cojones|cabr[oó]n(es|a)?|mierdas?|"
                   r"gilipollas|pendej[ao]s?|chingad[ao]s?|ching[ao]|verga|culer[ao]|polla|zorras?|marica|maric[oó]n|"
                   r"fuck\w*|shit\w*|bitch\w*|dick\w*|cunt\w*|asshole\w*|motherfuck\w*|bastard\w*)\b", re.I)
def mask(m):
    w = m.group(0)
    vowels = [i for i, ch in enumerate(w) if ch.lower() in 'aeiouáéíóú' and 0 < i < len(w) - 1]
    i = vowels[0] if vowels else len(w) // 2
    return w[:i] + '*' + w[i+1:]
def clean(t): return SWEAR.sub(mask, t) if censor else t
def ts(t): return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
off = read_offsets(RAW)
for c in read_clips(os.path.join(W, 'clips.tsv')):
    n = c['name']
    audio = load_audio(os.path.join(RAW, n + '.mp4'), start=c['a'] - off[n], dur=c['b'] - c['a'])
    segs, _ = wm.transcribe(audio, language=lang, word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
    words = [w for s in segs for w in (s.words or [])]
    lines, cur = [], []
    for w in words:          # group into lines of <= 24 characters and <= 2.5 s
        txt = w.word.strip()
        if not txt: continue
        if cur and (len(' '.join(x.word.strip() for x in cur + [w])) > 24 or w.end - cur[0].start > 2.5):
            lines.append(cur); cur = []
        cur.append(w)
        if txt[-1] in '.?!': lines.append(cur); cur = []
    if cur: lines.append(cur)
    out = [HDR]; js = []; prev = None
    for i, ln in enumerate(lines):
        t = ' '.join(x.word.strip() for x in ln)
        if junk.search(t) or t == prev: continue
        prev = t; a = ln[0].start; b = ln[-1].end + 0.5
        if i + 1 < len(lines):   # no flicker: if the next line comes soon, stay until it does
            nxt = lines[i+1][0].start
            b = nxt if nxt - b < 0.8 else min(b, nxt)
        out.append(f"Dialogue: 0,{ts(a)},{ts(b)},Sub,,0,0,0,,{{\\pos(540,902)}}{clean(t).upper()}\n")
        js.append({'start': round(a, 2), 'end': round(b, 2), 'text': clean(t).upper()})
    open(os.path.join(OUT, n + '.ass'), 'w', encoding='utf-8').write(''.join(out))
    json.dump(js, open(os.path.join(OUT, n + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('OK', n, len(out) - 1, 'lines', flush=True)
