"""Shared helpers: paths, ffmpeg, time parsing, whisper. Works on macOS, Windows and Linux."""
import os, sys, shutil, subprocess, platform, json, urllib.request

for _s in (sys.stdout, sys.stderr):   # the Windows console isn't always UTF-8 (accents, ñ, ¡)
    try: _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
EXE = '.exe' if os.name == 'nt' else ''


def tool(name):
    """Look in tools/bin first (e.g. ffmpeg-full on macOS), then on the PATH."""
    local = os.path.join(TOOLS, 'bin', name + EXE)
    if os.path.exists(local):
        return local
    found = shutil.which(name)
    if not found:
        sys.exit(f'"{name}" is missing. Run the setup prompt again (prompts/setup.md).')
    return found


FFMPEG = None
FFPROBE = None


def ff():
    global FFMPEG, FFPROBE
    if FFMPEG is None:
        FFMPEG, FFPROBE = tool('ffmpeg'), tool('ffprobe')
    return FFMPEG, FFPROBE


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def ffmpeg(*args, **kw):
    return run([ff()[0], '-v', 'error', '-y', *args], **kw)


def ffout(*args):
    r = subprocess.run([ff()[0], '-hide_banner', *args], capture_output=True, text=True)
    return r.stdout + r.stderr


def encoder():
    """Hardware H.264 when available (Mac: videotoolbox, NVIDIA: nvenc); otherwise libx264."""
    enc = ffout('-encoders')
    if platform.system() == 'Darwin' and 'h264_videotoolbox' in enc:
        return ['-c:v', 'h264_videotoolbox', '-b:v', '10M', '-maxrate', '14M']
    if 'h264_nvenc' in enc and probe_nvenc():
        return ['-c:v', 'h264_nvenc', '-preset', 'p5', '-b:v', '10M', '-maxrate', '14M']
    return ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20']


def probe_nvenc():
    r = subprocess.run([ff()[0], '-v', 'error', '-f', 'lavfi', '-i', 'color=s=256x256:d=0.1',
                        '-c:v', 'h264_nvenc', '-f', 'null', '-'], capture_output=True)
    return r.returncode == 0


def parse_t(x):
    """'1:02:03' or '1:02:03.5' -> seconds."""
    parts = [float(v) for v in x.split(':')]
    while len(parts) < 3:
        parts.insert(0, 0)
    return parts[0]*3600 + parts[1]*60 + parts[2]


def fmt_t(s):
    s = int(s)
    return f"{s//3600}:{s%3600//60:02d}:{s%60:02d}"


def read_clips(tsv):
    """clips.tsv: name<TAB>start<TAB>end[<TAB>cam x,y,w,h[<TAB>game w,h,x,y]]"""
    out = []
    for l in open(tsv, encoding='utf-8'):
        if not l.strip() or l.startswith('#'):
            continue
        c = l.rstrip('\n').split('\t')
        out.append({'name': c[0], 'a': parse_t(c[1]), 'b': parse_t(c[2]),
                    'cam': c[3] if len(c) > 3 else '', 'game': c[4] if len(c) > 4 else ''})
    return out


def read_offsets(raw):
    return {l.split()[0]: int(l.split()[1]) for l in open(os.path.join(raw, 'offsets.txt'))}


def download(url, dest, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'viral-clips-radar'})
            with urllib.request.urlopen(req, timeout=60) as r, open(dest + '.part', 'wb') as f:
                shutil.copyfileobj(r, f)
            os.replace(dest + '.part', dest)
            return
        except Exception:
            if i == tries - 1:
                raise


def ytdlp(*args):
    """yt-dlp from the .venv (or from the PATH)."""
    exe = os.path.join(os.path.dirname(sys.executable), 'yt-dlp' + EXE)
    if not os.path.exists(exe):
        exe = tool('yt-dlp')
    return subprocess.run([exe, *args], capture_output=True, text=True, check=True).stdout.strip()


def save_json(obj, path):
    json.dump(obj, open(path, 'w', encoding='utf-8'), ensure_ascii=False)


def lang_arg(x):
    """'auto' (or nothing) lets whisper detect the language; otherwise a code like 'es' or 'en'."""
    return None if not x or x == 'auto' else x


def whisper_model(size='small'):
    """faster-whisper on the best device: NVIDIA GPU (cuda) > Apple GPU (mps) > CPU."""
    from faster_whisper import WhisperModel
    import ctranslate2
    tries = []
    try:
        if ctranslate2.get_cuda_device_count() > 0: tries.append(('cuda', 'float16'))
    except Exception:
        pass
    if platform.system() == 'Darwin' and platform.machine() == 'arm64': tries.append(('mps', 'float16'))
    tries.append(('cpu', 'int8'))
    for dev, ct in tries:
        try:
            m = WhisperModel(size, device=dev, compute_type=ct, cpu_threads=os.cpu_count() or 4)
            print(f'whisper {size} on {dev}', flush=True)
            return m
        except Exception:
            continue


def load_audio(path, start=None, dur=None):
    """Decode with ffmpeg to float32 mono 16 kHz (avoids PyAV, whose API changes between versions)."""
    import numpy as np
    args = [ff()[0], '-v', 'error']
    if start is not None: args += ['-ss', str(start)]
    args += ['-i', path]
    if dur is not None: args += ['-t', str(dur)]
    args += ['-vn', '-ac', '1', '-ar', '16000', '-f', 's16le', '-']
    raw = subprocess.run(args, capture_output=True, check=True).stdout
    return np.frombuffer(raw[:len(raw)//2*2], np.int16).astype(np.float32) / 32768.0
