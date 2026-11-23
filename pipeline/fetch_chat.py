"""Step 4a. Usage: python pipeline/fetch_chat.py <work>
Downloads the VOD's full chat with TwitchDownloaderCLI (no account or API key needed) -> work/chat.json"""
import os, sys, json, subprocess
from common import TOOLS, EXE
W = sys.argv[1]; meta = json.load(open(os.path.join(W, 'meta.json'), encoding='utf-8'))
exe = os.path.join(TOOLS, 'TwitchDownloaderCLI' + EXE)
if not os.path.exists(exe):
    sys.exit('TwitchDownloaderCLI is missing. Run: python pipeline/setup_tools.py')
env = dict(os.environ, DOTNET_SYSTEM_GLOBALIZATION_INVARIANT='1')
subprocess.run([exe, 'chatdownload', '--id', meta['id'], '-o', os.path.join(W, 'chat.json'), '--threads', '8', '--collision', 'Overwrite'],
               check=True, env=env, stdout=subprocess.DEVNULL)
d = json.load(open(os.path.join(W, 'chat.json'), encoding='utf-8'))
print('OK:', len(d['comments']), 'messages')
