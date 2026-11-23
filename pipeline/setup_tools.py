"""Usage: python pipeline/setup_tools.py
Installs what doesn't come from pip and checks that everything works (safe to run again):
  1. TwitchDownloaderCLI (for the chat) for your system, verifying its SHA-256.
  2. On macOS, links ffmpeg-full (which includes libass) into tools/bin.
  3. Checks ffmpeg (libass and encoder), yt-dlp and faster-whisper (downloads the 'small' model).
  4. Installs the edit layer (HyperFrames + GSAP, pinned) in editor/ with npm.
  5. Renders a 6-second test short in the final layout -> clips/_test/shorts/01_test.mp4,
     turns it into an editable project with a few demo edits, and opens it in the studio at http://localhost:3006.
With --open the studio also opens in your browser."""
import os, sys, platform, hashlib, zipfile, shutil, subprocess, stat
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, TOOLS, EXE, download

TDL_VERSION = '1.56.5'
TDL = {  # asset -> SHA-256 published at https://github.com/lay295/TwitchDownloader/releases/tag/1.56.5
    'MacOSArm64': '17a0182f83689a0ae429f48cf03c26f1701eed7edcd787fa3d261898a6023d76',
    'MacOS-x64': 'efaa61d6109dfbce4ddedc28da55e23dc1de30caa2f6a35dc611f9b3bb48b724',
    'Windows-x64': '8b1b0695f2b1b6bf0d2535fab4b84032951cded8cf4078dfdf4d58e391c813a0',
    'Linux-x64': 'f2bcee00d0e6da759d97c23767345634cb9cdb10cdff96cfa96f97983d51bf55',
    'LinuxArm64': '2fde836f07c3ebfcf61cace23742a2c43543fc30fda96071eb96ab8e10c24f7f',
}
os.makedirs(TOOLS, exist_ok=True)
sysname, arch = platform.system(), platform.machine().lower()
arm = arch in ('arm64', 'aarch64')
asset = {'Darwin': 'MacOSArm64' if arm else 'MacOS-x64', 'Windows': 'Windows-x64', 'Linux': 'LinuxArm64' if arm else 'Linux-x64'}[sysname]

print(f'==> System: {sysname} {arch}')
print(f'==> TwitchDownloaderCLI {TDL_VERSION} ({asset})')
exe = os.path.join(TOOLS, 'TwitchDownloaderCLI' + EXE)
if not os.path.exists(exe):
    z = os.path.join(TOOLS, 'tdl.zip')
    download(f'https://github.com/lay295/TwitchDownloader/releases/download/{TDL_VERSION}/TwitchDownloaderCLI-{TDL_VERSION}-{asset}.zip', z)
    got = hashlib.sha256(open(z, 'rb').read()).hexdigest()
    if got != TDL[asset]:
        os.remove(z); sys.exit(f'    ERROR: SHA-256 mismatch ({got}). Not installing it.')
    print('    SHA-256 verified')
    zipfile.ZipFile(z).extractall(TOOLS); os.remove(z)
    os.chmod(exe, os.stat(exe).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
else:
    print('    already installed')

if sysname == 'Darwin':
    pref = subprocess.run(['brew', '--prefix', 'ffmpeg-full'], capture_output=True, text=True).stdout.strip() if shutil.which('brew') else ''
    if pref and os.path.exists(os.path.join(pref, 'bin', 'ffmpeg')):
        os.makedirs(os.path.join(TOOLS, 'bin'), exist_ok=True)
        for b in ('ffmpeg', 'ffprobe'):
            dst = os.path.join(TOOLS, 'bin', b)
            if os.path.lexists(dst): os.remove(dst)
            os.symlink(os.path.join(pref, 'bin', b), dst)
        print('==> ffmpeg-full linked into tools/bin')

import common
ffm, ffp = common.ff()
print('==> Checks')
probs = []
fl = common.ffout('-filters')
print('    ffmpeg:', ffm)
print('    libass (subtitles):', 'ok' if ' ass ' in fl else 'MISSING'); ' ass ' in fl or probs.append('ffmpeg without libass')
print('    encoder:', common.encoder()[1])
try:
    print('    yt-dlp:', common.ytdlp('--version'))
except Exception:
    probs.append('yt-dlp does not work')
try:
    common.whisper_model('small'); print('    faster-whisper + small model: ok')
except Exception as e:
    probs.append(f'faster-whisper: {e}')
r = subprocess.run([exe, '--version'], capture_output=True, text=True, env=dict(os.environ, DOTNET_SYSTEM_GLOBALIZATION_INVARIANT='1'))
tdl_ok = 'TwitchDownloaderCLI' in (r.stdout + r.stderr)
print('    TwitchDownloaderCLI:', 'ok' if tdl_ok else 'FAILS'); tdl_ok or probs.append('TwitchDownloaderCLI does not start')

print('==> Edit layer (HyperFrames)')
ED = os.path.join(ROOT, 'editor')
node, npm = shutil.which('node'), shutil.which('npm')
nv = subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip() if node else ''
ver = tuple(int(x) for x in nv.lstrip('v').split('.')[:2]) if nv else (0, 0)
if ver < (22, 18):
    probs.append(f'Node.js 22.18 or later is needed for the edit layer (found: {nv or "none"})')
    print('    Node.js:', nv or 'MISSING')
else:
    print('    Node.js:', nv)
    if not os.path.exists(os.path.join(ED, 'node_modules', '.bin', 'hyperframes' + ('.cmd' if os.name == 'nt' else ''))):
        subprocess.run([npm, 'ci', '--silent'], cwd=ED, check=True)
    r = subprocess.run([os.path.join(ED, 'node_modules', '.bin', 'hyperframes' + ('.cmd' if os.name == 'nt' else '')), '--version'],
                       capture_output=True, text=True)
    print('    hyperframes:', r.stdout.strip() or 'FAILS'); r.stdout.strip() or probs.append('hyperframes does not start')

print('==> Test short')
W = os.path.join(ROOT, 'clips', '_test', 'work'); os.makedirs(os.path.join(W, 'raw'), exist_ok=True); os.makedirs(os.path.join(W, 'subs'), exist_ok=True)
common.ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=1920x1080:r=60:d=8', '-f', 'lavfi', '-i', 'sine=f=440:d=8',
              '-vf', 'drawbox=x=0:y=470:w=420:h=273:c=red@0.8:t=fill,drawtext=text=FACECAM:x=120:y=590:fontsize=40:fontcolor=white',
              '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', '-shortest', os.path.join(W, 'raw', '01_test.mp4'))
open(os.path.join(W, 'raw', 'offsets.txt'), 'w').write('01_test 0 0 0\n')
open(os.path.join(W, 'clips.tsv'), 'w').write('01_test\t0:00:01\t0:00:07\n')
hdr = open(os.path.join(os.path.dirname(__file__), 'subs.py'), encoding='utf-8').read().split('HDR = """')[1].split('"""')[0]
open(os.path.join(W, 'subs', '01_test.ass'), 'w', encoding='utf-8').write(hdr + 'Dialogue: 0,0:00:00.00,0:00:06.00,Sub,,0,0,0,,{\\pos(540,902)}ALL SET!\n')
import json
json.dump([{'start': 0.0, 'end': 6.0, 'text': 'ALL SET!'}], open(os.path.join(W, 'subs', '01_test.json'), 'w', encoding='utf-8'))
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'render.py'), W], check=True)
out = os.path.join(ROOT, 'clips', '_test', 'shorts', '01_test.mp4')
print('    ', out if os.path.exists(out) else 'NOT CREATED'); os.path.exists(out) or probs.append('the test render failed')

url = ''
if os.path.exists(out) and ver >= (22, 18):
    print('==> Editable test project + studio')
    import edit
    edit.new(W, ['01'])
    P = os.path.join(ROOT, 'clips', '_test', 'edits', '01_test', 'index.html')
    h = open(P, encoding='utf-8').read()
    h = h.replace('<!-- EDITS:HTML START -->\n  <!-- EDITS:HTML END -->', '''<!-- EDITS:HTML START -->
  <div id="hook" class="clip hook" data-start="0" data-duration="3">YOUR CLIPS <span class="hl">START HERE</span></div>
  <div id="party" class="clip sticker" style="left:720px; top:1060px" data-start="2" data-duration="3.8">🎉</div>
  <div id="bar" class="clip bar" data-start="0" data-duration="6"></div>
  <audio id="sfx-whoosh" class="clip" src="sfx/whoosh.wav" data-start="0" data-duration="0.7" data-volume="0.8"></audio>
  <audio id="sfx-pop" class="clip" src="sfx/pop.wav" data-start="2" data-duration="0.18" data-volume="0.9"></audio>
  <audio id="sfx-ding" class="clip" src="sfx/ding.wav" data-start="2.1" data-duration="1" data-volume="0.6"></audio>
  <!-- EDITS:HTML END -->''')
    h = h.replace('// EDITS:JS START\n    // EDITS:JS END', '''// EDITS:JS START
    hook('#hook', 2.6);
    pop('#party', 2, 3.8, { rot: -25, rotTo: 6 });
    shake('#party', 2.35);
    punch(2, 1.2, 1.1);
    progress('#bar');
    // EDITS:JS END''')
    open(P, 'w', encoding='utf-8').write(h)
    try:
        url = edit.preview(W, '01', '--open' in sys.argv)
    except SystemExit as e:
        probs.append(f'the studio did not start: {e}')

if probs:
    print('\nPROBLEMS:\n - ' + '\n - '.join(probs))
    sys.exit(1)
bar = '=' * 66
print(f'\n{bar}\n  ALL SET: viral-clips-radar is ready to make clips\n'
      f'  Studio (edit preview): {url}\n  Test short:            {out}\n{bar}')
