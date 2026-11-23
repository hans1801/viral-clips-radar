# Setup prompt

The only thing you install yourself is Claude Code. Open Claude Code in any folder (your Desktop, for example), paste this prompt once and Claude does the rest: it installs the programs, downloads the project, checks that everything works and makes a 6-second test short with a few demo edits. When it's done, the editing studio opens at **http://localhost:3006** with that test short, so you can play it and see it's ready. It ends with "✅ All set" and a summary of what it did and how to make your first clips.

---

```text
I want to set up the project https://github.com/hans1801/viral-clips-radar on my computer (it turns a Twitch VOD into viral 9:16 shorts using the chat's metrics, and lets me edit them with stickers, titles and sound effects). I'm a beginner: do everything yourself and explain each step in one plain line, no jargon, in my language.

1. Check which system I'm on (macOS, Windows or Linux).
2. Check for Git, ffmpeg with libass, Python 3.10 to 3.14 (3.12 is the safest; newer ones, like 3.15, can't install the transcription yet) and Node.js 22.18 or later. Install whatever is missing (or update Node if it's older):
   - macOS: with Homebrew (`brew install git ffmpeg-full python@3.12 node`). Use `ffmpeg-full`, not `ffmpeg`: the regular one no longer includes libass, which the subtitles need. It installs on its own and doesn't replace any ffmpeg I already have. If Homebrew isn't there, its installer asks for the Mac's password and you can't type it: give me the exact command to paste into the Terminal app, warn me that the password doesn't show while I type it, and wait until I say "done". Then install the rest yourself.
   - Windows: with `winget install` (Git.Git, Gyan.FFmpeg, Python.Python.3.12, OpenJS.NodeJS.LTS). Gyan's ffmpeg already includes libass.
   - Linux: with the package manager (for example `sudo apt install git ffmpeg python3.12 python3.12-venv`, and Node 22 from nodejs.org or NodeSource if the distro's is older). If it asks for a password (sudo), give me the command and wait.
   Then check the versions again. If something you just installed doesn't show up, look for it in its install path before asking me to restart anything.
3. If this folder isn't the project already, download it here with `git clone https://github.com/hans1801/viral-clips-radar.git` and work inside `viral-clips-radar`.
4. Create the Python environment at the root with a Python from 3.10 to 3.14: `python3 -m venv .venv` if `python3 --version` is in that range, otherwise `python3.12 -m venv .venv` (on Windows `py -3.12 -m venv .venv`). Then install the dependencies without bumping versions (they're pinned on purpose): `.venv/bin/pip install -r requirements.txt` (on Windows `.venv\Scripts\pip install -r requirements.txt`).
5. Run `.venv/bin/python pipeline/setup_tools.py --open` (on Windows `.venv\Scripts\python pipeline\setup_tools.py --open`). It:
   - downloads TwitchDownloaderCLI (the tool that downloads the chat; no account or API key needed) and verifies its SHA-256;
   - checks ffmpeg, libass, yt-dlp and the transcription, and downloads the whisper model (~490 MB);
   - installs the editor (HyperFrames, pinned version) in `editor/`;
   - renders a test short at `clips/_test/shorts/01_test.mp4`, turns it into an editable project with demo edits (a title, a 🎉 sticker, a zoom and three sound effects) and opens the studio at http://localhost:3006 (the exact link is in the "ALL SET" box).
   It must end with the "ALL SET" box. If it says "PROBLEMS", fix them and run it again.
6. Give me the studio link from the box and tell me it's open: there I press play to watch the test short with its edits, and drag the timeline to move through it. If your app has a browser panel, open the link there too.
7. If something fails, fix it without changing how the project works and tell me what you changed.
8. **Always** finish with this summary, even if something failed or you had to stop halfway (then start it with what's missing and the exact step to finish it). Write it in my language, for someone who has never programmed: short lines, no jargon, and every command in its own block so I can copy it.
   - **First line, on its own:** "✅ All set: the project works and the studio is open at <link>" (in my language). If something failed, write "⚠️ Not ready yet" and what's missing instead.
   - **What got done:** each program (installed now or already there, one line each, with what it's for in a few words) and the full path of the project folder.
   - **Your test short:** the studio link (it stays open in the background even if I close this chat) and the full path of `01_test.mp4`. To close the studio, and to open it again another day, give me these two commands, and tell me they're run from inside the project folder (the `cd` to get there first, with the full path): `.venv/bin/python pipeline/edit.py stop clips/_test/work` and `.venv/bin/python pipeline/edit.py preview clips/_test/work 01 --open` (with `.venv\Scripts\python` on Windows).
   - **How to make clips:** I open a NEW Claude Code chat in the project folder and paste the Twitch VOD link (for example "make the best clips from https://www.twitch.tv/videos/…"). A VOD is the recording Twitch keeps of a stream; its link is in the channel's Videos tab. The vertical shorts come out in `clips/<streamer>_<date>/shorts/`, the original horizontal cuts in `horizontal/`, with a `CLIPS.md` explaining each clip. An 8-hour VOD takes ~30–60 min.
   - **How to edit a clip:** in that same chat I say, for example, "edit clip 03: a 💀 sticker with a honk when…". Claude adds it, I see it at the studio link, and when I like it I say "render it" (it comes out in `edited/`).
   - **If something breaks later:** I open a chat in the project folder and say what I see, or paste this same setup prompt again: it only installs what's missing.
```
