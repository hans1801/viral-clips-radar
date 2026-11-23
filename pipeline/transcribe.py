"""Step 3. Usage: python pipeline/transcribe.py <work> [language=auto] [model=small] [--from h:mm:ss --to h:mm:ss]
Transcribes the VOD (from OFFSET) with faster-whisper, in 30-minute chunks so it doesn't fill the memory.
transcript.srt is written in REAL VOD TIME. Uses the GPU if there is one (NVIDIA or Apple), otherwise the CPU.
VAD is on so it doesn't invent text over music."""
import os, sys, json, time
from common import whisper_model, load_audio, parse_t, fmt_t, lang_arg

args = [a for a in sys.argv[2:]]
def opt(k):
    if k in args:
        i = args.index(k); v = args[i+1]; del args[i:i+2]; return v
t_from, t_to = opt('--from'), opt('--to')
W = sys.argv[1]; lang = lang_arg(args[0] if args else 'auto'); model = args[1] if len(args) > 1 else 'small'
meta = json.load(open(os.path.join(W, 'meta.json'), encoding='utf-8'))
start = parse_t(t_from) if t_from else meta['offset']; end = parse_t(t_to) if t_to else meta['audio_seconds']
wm = whisper_model(model)
if lang is None:   # detect once on 30 s of speech and keep it for every chunk
    _, info = wm.transcribe(load_audio(os.path.join(W, 'audio16.wav'), start=start + 120, dur=30), vad_filter=True)
    lang = info.language; print(f'language detected: {lang}', flush=True)
    meta['language'] = lang; json.dump(meta, open(os.path.join(W, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
def ts(t):
    ms = int(round(t*1000)); return f"{ms//3600000:02d}:{ms%3600000//60000:02d}:{ms%60000//1000:02d},{ms%1000:03d}"
CH = 1800; t0 = time.time(); n = 0
out = 'transcript.srt' if not (t_from or t_to) else 'transcript_partial.srt'
with open(os.path.join(W, out), 'w', encoding='utf-8') as f:
    for c0 in range(int(start), int(end), CH):
        dur = min(CH, end - c0)
        audio = load_audio(os.path.join(W, 'audio16.wav'), start=c0, dur=dur)
        segs, _ = wm.transcribe(audio, language=lang, vad_filter=True, condition_on_previous_text=False, beam_size=1)
        for s in segs:
            n += 1; f.write(f"{n}\n{ts(s.start+c0)} --> {ts(s.end+c0)}\n{s.text.strip()}\n\n")
        f.flush()
        print(f'  up to {fmt_t(c0+dur)} of {fmt_t(end)} ({(time.time()-t0)/60:.1f} min)', flush=True)
print(f'OK: {out} ({n} lines)')
