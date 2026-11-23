# viral-clips-radar

You give it **a Twitch VOD link** and the AI gives you back **vertical shorts ready to post** (TikTok, Reels, YouTube Shorts), plus the **original horizontal cut** of each one. **The chat** picks the moments: it finds the spikes of laughter and reactions and starts each clip some seconds earlier, so it has context. Then you can **dress each short up by just asking** (stickers, titles, sound effects, zooms) and watch it live in a studio on **localhost**.

> **What's a VOD?** *Video On Demand*: the recording Twitch keeps of a live stream after it ends, so you can watch it later. You'll find it in the channel's **Videos** tab, and its link looks like `https://www.twitch.tv/videos/1234567890`. It also keeps that stream's chat, which is what this project uses to find the best moments. Twitch deletes VODs after 7–60 days, so make your clips early.

Everything runs on your computer (macOS, Windows or Linux). No Twitch account or API keys needed, and nothing is uploaded to the cloud.

## How it works

```
VOD link
 1. Audio         downloaded in segments, in parallel            pipeline/fetch_audio.py
 2. Transcript    line by line, in real VOD time                 pipeline/transcribe.py   (faster-whisper, local)
 3. Chat          the whole replay chat                          pipeline/fetch_chat.py   (TwitchDownloaderCLI)
 4. Spikes        laughs and reactions per minute (z-score)      pipeline/chat_peaks.py
 5. Cuts          the AI matches spikes with the transcript:     clips.tsv
                  start ~60–90 s before, end right after the spike
 6. Video         only the pieces it needs, checked for sync     pipeline/build_raw.py + align.py
 7. Facecam       the AI finds the streamer's camera             pipeline/frames.py
 8. Subtitles     word by word, swear words masked (P*TA)        pipeline/subs.py
 9. Render        9:16 with safe zones + original 16:9 cut       pipeline/render.py
10. Review        format, audio, cuts and a contact sheet        pipeline/check.py
 → clips/<streamer>_<date>/shorts/*.mp4 + horizontal/*.mp4 + CLIPS.md

edits (optional, by asking: "edit clip 03: a 💀 sticker with a honk when…")
11. Project       layers: background, facecam, gameplay, subs    pipeline/edit.py new
12. Studio        live preview at http://localhost:3006          pipeline/edit.py preview   (HyperFrames)
13. Render        the edited short, 60 fps                       pipeline/edit.py render
 → clips/<streamer>_<date>/edited/*.mp4
```

**The layout (1080x1920):** a safe margin on top, the streamer cropped from their facecam, big subtitles on the seam, the center of the gameplay, and a safe margin at the bottom. That way the app's search bar and caption don't cover anything.

**The edit layer:** each short becomes a [HyperFrames](https://github.com/heygen-com/hyperframes) project (HTML + [GSAP](https://gsap.com)) built from the original horizontal cut, so a zoom only moves the gameplay and the subtitles stay editable text. Claude writes the edits (hook titles, labels, emoji or image stickers, punch-in zooms, a progress bar, and sound effects from a small library made for this project) and you watch them live in the studio before rendering.

**Why the chat:** in big streams the chat is almost always maxed out (slow mode, sub-only), so counting messages tells you nothing. What changes is *what* people type: when something is funny it fills up with JAJA, LOL and KEKW; when something is shocking, with NOOO, F and WTF. That's what it measures.

## Start from zero

You install just one thing by hand: Claude Code. Everything else (Git, ffmpeg, Python, Node, the project and its dependencies) Claude installs for you.

**1. Install Claude Code.** You need a Claude account (Pro or Max plan). Pick one:
- **Desktop app:** download it from [claude.ai/download](https://claude.ai/download) and open the **Code** tab.
- **Terminal:** on macOS or Linux paste `curl -fsSL https://claude.ai/install.sh | bash`. On Windows follow [the official guide](https://docs.claude.com/en/docs/claude-code/setup). Then type `claude`.

**2. Open Claude Code in any folder**, for example your Desktop. The project will be downloaded there.

**3. Paste the setup prompt:** copy the block in [prompts/setup.md](prompts/setup.md) and send it. Claude installs whatever is missing, downloads the project and makes a 6-second test short with a few demo edits. It opens in the studio in your browser (http://localhost:3006): when it plays, you're ready. It ends with "✅ All set" and a summary of what it did.

**4. Make your clips:** open a new chat in Claude Code in the `viral-clips-radar` folder and write:

```text
make the best clips from https://www.twitch.tv/videos/XXXXXXXXXX
```

(Any language works, e.g. *"saca los mejores clips de …"*.) The project's `CLAUDE.md` tells Claude the whole process, and it does it in one go: it picks the moments, cuts them, finds the camera, adds subtitles, checks everything and delivers the shorts in `clips/<streamer>_<date>/shorts/`, the horizontal cuts in `horizontal/`, and a table of what happens in each one. An 8-hour VOD takes ~30–60 min. Want more control (number of clips, length, language, no subtitles)? Use the template in [prompts/production.md](prompts/production.md).

**5. Edit a clip (optional):** in the same chat, ask for what you want by clip number:

```text
edit clip 03: a hook title "HE DIDN'T SEE IT COMING 😭", a 💀 sticker with a honk when he gets run over, and a zoom on that moment
```

Claude adds it and you watch it in the studio at http://localhost:3006. Ask for changes until you like it, then say *"render it"*: it comes out in `clips/<streamer>_<date>/edited/`. Everything you can ask for is in [prompts/edit.md](prompts/edit.md).

<details>
<summary>Doing it by hand, without Claude Code</summary>

With Git, ffmpeg with libass (on macOS, `ffmpeg-full`), Python 3.10 to 3.14 and Node.js 22.18+ installed, from the repo folder:

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python pipeline/setup_tools.py
```

(On Windows, `py -3.12 -m venv .venv` and `.venv\Scripts\python` instead of `.venv/bin/python`.)

One VOD (`W` is the folder `start.py` prints):

```bash
.venv/bin/python pipeline/start.py https://www.twitch.tv/videos/XXXXXXXXXX
.venv/bin/python pipeline/fetch_audio.py W
.venv/bin/python pipeline/transcribe.py W
.venv/bin/python pipeline/fetch_chat.py W
.venv/bin/python pipeline/chat_peaks.py W
.venv/bin/python pipeline/compact.py W
# (write W/clips.tsv:  name<TAB>start<TAB>end, using pipeline/seg.py W h:mm:ss-h:mm:ss)
.venv/bin/python pipeline/build_raw.py W
.venv/bin/python pipeline/align.py W
.venv/bin/python pipeline/frames.py W
.venv/bin/python pipeline/subs.py W
.venv/bin/python pipeline/render.py W
.venv/bin/python pipeline/check.py W
```

Edits for one clip (write them between the `EDITS` markers of its `index.html`):

```bash
.venv/bin/python pipeline/edit.py new W 03
.venv/bin/python pipeline/edit.py preview W 03 --open
.venv/bin/python pipeline/edit.py render W 03
```

The language is detected automatically; pass it as an extra argument (`es`, `en`…) to `transcribe.py`, `subs.py` and `check.py` to force it.

</details>

## Structure

```
pipeline/         start, fetch_audio, transcribe, fetch_chat, chat_peaks, compact, seg,
                  build_raw, align, frames, subs, render, check, edit, setup_tools, common
prompts/          setup.md (setup), production.md (steps for each VOD), edit.md (edits and their rules)
editor/           template/ (the layered composition), library/ (sound effects, stickers), HyperFrames + GSAP
clips/<streamer>_<date>/
                  work/        audio, transcript, chat, spikes, clips.tsv, raw pieces (not in git)
                  shorts/      the vertical .mp4 files, CLIPS.md and _contact_sheet.png
                  horizontal/  the original 16:9 cut of each clip, to re-edit
                  edits/       one HyperFrames project per clip (index.html + layers)
                  edited/      the rendered edited shorts
tools/            TwitchDownloaderCLI (and on macOS, the link to ffmpeg-full); created by setup_tools.py
CLAUDE.md         what Claude reads in every chat here: a VOD link starts the whole process, "edit clip N" the edits
```

## References

Tools the project uses. They're installed separately (they don't ship inside the repo).

| what | for |
|---|---|
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | transcribes the VOD and each clip, word by word |
| [TwitchDownloaderCLI](https://github.com/lay295/TwitchDownloader) | downloads the replay chat (no account or API key) |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | VOD metadata and links to its segments |
| [ffmpeg](https://ffmpeg.org) + libass | cuts, builds the 9:16 layout, burns the subtitles and encodes |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | the edit layer: live studio on localhost and frame-by-frame render |
| [GSAP](https://gsap.com) | the animation timeline of the edits |

## Disclaimer

The clips are the streamer's content: ask for their permission or follow their clipper rules before posting. TwitchDownloaderCLI uses Twitch's internal API; it isn't an official tool.

## License

[MIT](LICENSE). The license covers this code, not the clips you make: those stay the streamer's content.
