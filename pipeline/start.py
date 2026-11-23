"""Step 1. Usage: python pipeline/start.py <VOD link>
Reads the metadata, creates clips/<streamer>_<date>/work/ and saves meta.json. Prints the work folder."""
import os, sys, json, re
from common import ROOT, ytdlp, save_json

url = sys.argv[1]
out = ytdlp('--print', '%(id)s\t%(uploader)s\t%(title)s\t%(duration)s\t%(live_status)s\t%(upload_date)s', url)
vid, uploader, title, dur, live, date = out.splitlines()[-1].split('\t')
vid = vid.lstrip('v')
name = re.sub(r'[^a-z0-9]+', '_', uploader.lower()).strip('_') or 'streamer'
d = f"{date[:4]}-{date[4:6]}-{date[6:]}" if date and date != 'NA' else 'no_date'
work = os.path.join(ROOT, 'clips', f'{name}_{d}', 'work')
os.makedirs(work, exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(work), 'shorts'), exist_ok=True)
meta = {'url': url, 'id': vid, 'uploader': uploader, 'title': title, 'duration': float(dur), 'live_status': live, 'date': d}
save_json(meta, os.path.join(work, 'meta.json'))
print(json.dumps(meta, ensure_ascii=False, indent=1))
if live == 'is_live':
    print('WARNING: the stream is still LIVE; the VOD is incomplete.')
print('WORK=' + work)
