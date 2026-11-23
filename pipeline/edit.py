"""Edit layer (HyperFrames). Turns each clip into an editable project, previews it on localhost and renders it.

  python pipeline/edit.py new <work> [01 05 ...]        build clips/<…>/edits/<clip>/ from the horizontal cut
  python pipeline/edit.py preview <work> <01> [--open]  open that clip in the studio at http://localhost:3006
  python pipeline/edit.py render <work> [01 05 ...]     render the edited clips -> clips/<…>/edited/<clip>.mp4
  python pipeline/edit.py stop <work>                   stop the preview

Every project is a HyperFrames composition (index.html) with layers built from the ORIGINAL horizontal cut:
blurred background, facecam, gameplay (with the audio), subtitles as text, and an EDITS block where the
stickers, titles, sound effects and zooms go. `new` keeps the EDITS blocks when it rebuilds a project."""
import os, sys, re, json, shutil, subprocess
from common import ROOT, EXE, ffmpeg, encoder, read_clips, tool

ED = os.path.join(ROOT, 'editor')
PORT = 3006


def hf():
    """The pinned HyperFrames CLI installed in editor/node_modules."""
    exe = os.path.join(ED, 'node_modules', '.bin', 'hyperframes' + ('.cmd' if os.name == 'nt' else ''))
    if not os.path.exists(exe):
        sys.exit('HyperFrames is not installed. Run: python pipeline/setup_tools.py')
    return exe


def env():
    # HyperFrames calls ffmpeg: give it the project's one first (ffmpeg-full on macOS)
    return dict(os.environ, PATH=os.path.join(ROOT, 'tools', 'bin') + os.pathsep + os.environ.get('PATH', ''))


def dirs(W):
    base = os.path.dirname(os.path.abspath(W))
    return base, os.path.join(base, 'horizontal'), os.path.join(base, 'edits'), os.path.join(base, 'edited')


def pick(W, nums):
    cl = read_clips(os.path.join(W, 'clips.tsv'))
    return [c for c in cl if not nums or c['name'][:2] in nums]


def keep_blocks(html):
    """Return the existing EDITS blocks of a project, to put them back after a rebuild."""
    h = re.search(r'<!-- EDITS:HTML START -->(.*?)<!-- EDITS:HTML END -->', html, re.S)
    j = re.search(r'// EDITS:JS START(.*?)// EDITS:JS END', html, re.S)
    return (h.group(1) if h else None), (j.group(1) if j else None)


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def new(W, nums):
    base, HOR, EDITS, _ = dirs(W)
    gsap = os.path.join(ED, 'node_modules', 'gsap', 'dist', 'gsap.min.js')
    if not os.path.exists(gsap):
        sys.exit('GSAP is not installed. Run: python pipeline/setup_tools.py')
    tpl = open(os.path.join(ED, 'template', 'index.html'), encoding='utf-8').read()
    enc = encoder()
    for c in pick(W, nums):
        n = c['name']; src = os.path.join(HOR, n + '.mp4'); dur = round(c['b'] - c['a'], 3)
        if not os.path.exists(src):
            sys.exit(f'Missing {src}: run pipeline/render.py first (it saves the horizontal cut).')
        P = os.path.join(EDITS, n); A = os.path.join(P, 'assets'); os.makedirs(A, exist_ok=True)
        nocam = c['cam'] == 'none'
        if nocam:
            game_vf, gtop, gh, suby = 'scale=1080:608', 656, 608, 1340
        else:
            gw, gh0, gx, gy = map(int, c['game'].split(',')) if c['game'] else (1500, 970, 420, 55)
            game_vf, gtop, gh, suby = f'crop={gw}:{gh0}:{gx}:{gy},scale=1080:698', 902, 698, 902
            cx, cy, cw, ch = map(int, c['cam'].split(',')) if c['cam'] else (0, 470, 420, 273)
            ffmpeg('-i', src, '-vf', f'crop={cw}:{ch}:{cx}:{cy},scale=1080:702', '-an', *enc, os.path.join(A, 'cam.mp4'))
        ffmpeg('-i', src, '-vf', game_vf, *enc, '-c:a', 'aac', '-b:a', '192k', os.path.join(A, 'game.mp4'))
        ffmpeg('-i', src, '-vf', 'scale=360:640:force_original_aspect_ratio=increase,crop=360:640,boxblur=10:2,eq=brightness=-0.18',
               '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', os.path.join(A, 'bg.mp4'))
        shutil.copy(gsap, os.path.join(P, 'gsap.min.js'))
        for lib in ('sfx', 'stickers'):
            s = os.path.join(ED, 'library', lib)
            if os.path.isdir(s): shutil.copytree(s, os.path.join(P, lib), dirs_exist_ok=True)
        subs_json = os.path.join(W, 'subs', n + '.json')
        subs = json.load(open(subs_json, encoding='utf-8')) if os.path.exists(subs_json) else []
        subs_html = '\n'.join(
            f'  <div id="sub-{i:03d}" class="clip sub" data-start="{s["start"]}" data-duration="{max(0.1, round(s["end"] - s["start"], 2))}" data-track-index="3">{esc(s["text"])}</div>'
            for i, s in enumerate(subs, 1) if s['start'] < dur)
        cam_html = '' if nocam else f'  <video id="cam" class="clip" src="assets/cam.mp4" data-start="0" data-duration="{dur}" muted data-track-index="1"></video>'
        html = (tpl.replace('{{DURATION}}', str(dur)).replace('{{GAME_TOP}}', str(gtop)).replace('{{GAME_H}}', str(gh))
                   .replace('{{SUB_Y}}', str(suby)).replace('{{CAM_HTML}}', cam_html).replace('{{SUBS_HTML}}', subs_html))
        idx = os.path.join(P, 'index.html')
        if os.path.exists(idx):   # rebuild: keep the user's edits
            h, j = keep_blocks(open(idx, encoding='utf-8').read())
            if h is not None: html = re.sub(r'(<!-- EDITS:HTML START -->).*?(<!-- EDITS:HTML END -->)', lambda m: m.group(1) + h + m.group(2), html, flags=re.S)
            if j is not None: html = re.sub(r'(// EDITS:JS START).*?(// EDITS:JS END)', lambda m: m.group(1) + j + m.group(2), html, flags=re.S)
        open(idx, 'w', encoding='utf-8').write(html)
        print('OK', n, '->', P, flush=True)


STATE = os.path.join(ED, '.preview')   # which project the studio is showing (one at a time, on PORT)


def stop(W=None):
    if os.path.exists(STATE):
        subprocess.run([hf(), 'preview', '--stop', open(STATE).read().strip()], capture_output=True, env=env())
        os.remove(STATE)


def preview(W, num, open_browser):
    _, _, EDITS, _ = dirs(W)
    c = pick(W, [num])
    if not c: sys.exit(f'No clip {num} in clips.tsv')
    P = os.path.join(EDITS, c[0]['name'])
    if not os.path.exists(os.path.join(P, 'index.html')): new(W, [num])
    stop(W)
    r = subprocess.run([hf(), 'preview', P, '--port', str(PORT), '--background', '--json', '--open' if open_browser else '--no-open'],
                       capture_output=True, text=True, env=env())
    try:
        info = json.loads(r.stdout.strip().splitlines()[-1])['result']
    except Exception:
        sys.exit('The preview did not start:\n' + r.stdout + r.stderr)
    open(STATE, 'w').write(P)
    url = info.get('studioUrl') or info.get('serverUrl')
    print('PREVIEW=' + url)
    return url


def render(W, nums):
    _, _, EDITS, OUT = dirs(W); os.makedirs(OUT, exist_ok=True)
    for c in pick(W, nums):
        n = c['name']; P = os.path.join(EDITS, n)
        if not os.path.exists(os.path.join(P, 'index.html')): new(W, [n[:2]])
        lint = subprocess.run([hf(), 'lint', P, '--json'], capture_output=True, text=True, env=env())
        try:
            errs = [f for f in json.loads(lint.stdout)['findings'] if f['severity'] == 'error']
        except Exception:
            errs = []
        if errs:
            sys.exit(f'{n}: fix these before rendering:\n' + '\n'.join(f"- {e['message']}" for e in errs))
        subprocess.run([hf(), 'render', P, '--fps', '60', '--gpu', '--video-bitrate', '10M', '--quiet',
                        '-o', os.path.join(OUT, n + '.mp4')], check=True, env=env(), cwd=P)
        print('OK', n, '->', os.path.join(OUT, n + '.mp4'), flush=True)


if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(__doc__)
    cmd, W, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    nums = [a for a in rest if not a.startswith('--')]
    if cmd == 'new': new(W, nums)
    elif cmd == 'preview': preview(W, nums[0] if nums else '01', '--open' in rest)
    elif cmd == 'render': render(W, nums)
    elif cmd == 'stop': stop(W)
    else: sys.exit(__doc__)
