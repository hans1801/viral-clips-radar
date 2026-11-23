# Production prompt: VOD → shorts

You usually don't need to paste this: saying "make the best clips from <link>" in a chat opened in the project folder is enough, because `CLAUDE.md` brings Claude here. Use it when you want to control every option.

```text
Make viral shorts from this Twitch VOD: <LINK>
- Number of clips: 10–12
- Length: ~90 s (between 60 and 105)
- Streamer's language: auto
- Subtitles: yes (swear words masked, e.g. P*TA)
- Notes: <optional: moments you don't want to miss, topics to avoid…>
```

---

## Steps (instructions for Claude)

In every command, `PY` is the environment's Python: `.venv/bin/python` on macOS and Linux, `.venv\Scripts\python` on Windows. Run them from the repo root. Every script prints `OK` when it finishes. Run anything that takes more than 2 minutes in the background, and tell the user which step you're on in one line.

1. **Start**
   - Run `PY pipeline/start.py <LINK>`. It creates `clips/<streamer>_<date>/work/` (`W` from here on) and shows the metadata.
   - If it warns that the stream is still **live**, ask the user whether to wait until it ends or work with what's there.

2. **Audio**
   - Run `PY pipeline/fetch_audio.py W`.
   - It downloads the audio in segments, creates `audio16.wav` and `loud.json` (loudness per second), and saves in `meta.json` the `offset` (where the real sound starts) and the ranges Twitch muted.

3. **Transcript**
   - Run `PY pipeline/transcribe.py W <language>`, with `auto` by default. It detects the language, saves it in `meta.json` and writes `transcript.srt` in real VOD time.
   - It uses the GPU if there is one (NVIDIA or Apple). On the CPU, 8 hours of audio can take more than an hour: tell the user.

4. **Chat** (can run in parallel with the transcript)
   - Run `PY pipeline/fetch_chat.py W`. No account needed. A sub-only VOD can't be downloaded without a token: tell the user and continue with the transcript only.
   - Once the transcript is ready, run `PY pipeline/chat_peaks.py W 35`. It writes `chat_peaks.txt` (the spike ranking with what the streamer said right before) and `chat_per_min.tsv`.
   - **Key idea:** the total chat volume is usually flat (slow mode, sub-only, huge chats). The signal is the *kind* of message: laughs (JAJA, JU, LOL, XD, KEKW) and reactions (NOOO, F, WTF, Pog), measured as a z-score against the surrounding ±7 minutes.

5. **Picking the clips**
   - Run `PY pipeline/compact.py W` and read `compact.txt` **whole**, in parts. If a part is too long, trim each line to ~220 characters.
   - Match the spikes in `chat_peaks.txt` with what happens in the transcript. Keep the moments that make sense on their own in 90 s. Drop spikes without a clear moment, and anything the "Rules" section rules out.
   - For each candidate, run `PY pipeline/seg.py W h:mm:ss-h:mm:ss`.
     - **End:** the first complete sentence after the chat spike. The chat runs ~5–10 s behind the picture.
     - **Start:** a complete sentence ~60–90 s earlier, so the short has context.
   - Write `W/clips.tsv`, with tab-separated columns: `NN_short_name  h:mm:ss  h:mm:ss`. Number `NN` in the chat's ranking order.

6. **Video**
   - Run `PY pipeline/build_raw.py W`. It downloads only the segments it needs.
   - Run `PY pipeline/align.py W`. Every clip must say `OK`. If one says `CHECK`, investigate before going on.

7. **Facecam**
   - Run `PY pipeline/frames.py W` and look at the images in `W/frames/`. `<clip>_grid.png` shows 8 moments of each clip; `<clip>_full.png` is one full-resolution frame with a 100 px grid.
   - The default position is `0,470,420,273` (x,y,width,height in 1920x1080). If the camera is somewhere else or moves, measure it and write it in the 4th column of `clips.tsv`, with an aspect of ~1.54.
   - In the 5th column, put a gameplay crop `w,h,x,y` with an aspect of 1.547 that **doesn't overlap** the camera (default `1500,970,420,55`).
   - During cutscenes the camera may be missing or swapped for an avatar. That's normal.
   - **If the stream has no facecam**, write `none` in the 4th column: the gameplay comes out large and centered over a blurred background, with the subtitles below.

8. **Subtitles**
   - Run `PY pipeline/subs.py W`, unless the user doesn't want subtitles. It uses the language detected in step 3.
   - Swear words are masked in the subtitle text (PUTA → P*TA, FUCK → F*CK); the audio is untouched. If the user wants them uncensored, add `--no-censor`.

9. **Render**
   - Do one test clip first: `PY pipeline/render.py W 01`. Grab a frame (`ffmpeg -ss 30 -i <short> -frames:v 1 test.png`) and look at it: the camera well framed, the gameplay without the camera, and the subtitles readable.
   - Then render the rest in 2–3 parallel processes, for example `render.py W 02 03 04` and `render.py W 05 06 07`. With `--nosubs` they come out without subtitles.
   - For every clip, `render.py` also saves the original 16:9 cut (same times, no crop and no subtitles) in `clips/<…>/horizontal/`.

10. **Check**
    - Run `PY pipeline/check.py W`. Every short must say `OK`, start and end on a complete sentence, and have audio (−16 to −24 dB is normal).
    - Look at `shorts/_contact_sheet.png`. If a cut lands mid-sentence, adjust `clips.tsv` and re-render only that clip.

11. **Editable projects**
    - Run `PY pipeline/edit.py new W` (one project per clip in `clips/<…>/edits/`, with no edits yet) and `PY pipeline/edit.py preview W 01 --open`. The studio opens at http://localhost:3006 with the first clip, ready for the user to ask for edits (`prompts/edit.md`).

12. **Deliver**
    - Write `clips/<…>/shorts/CLIPS.md` with a table: file, VOD times, length, chat spike (z and emotes) and what happens in each clip. Add the strong spikes you dropped, and why. Write it in the user's language.
    - Give the user the table, the `shorts/` and `horizontal/` folders, and the studio link. Tell them they can now ask for edits by clip number (for example "edit clip 03: a 💀 sticker with a honk when…"), and suggest one concrete edit for the best clip.
    - Tell them what was **not** checked: the clips weren't watched in full, and automatic subtitles can have mistakes.
    - Remind them the content belongs to the streamer.
    - Don't delete anything.

---

## Output format

Video at 1080x1920 and 60 fps, with H.264 and AAC at 192k. The encoder is picked automatically: videotoolbox on Mac, NVENC with NVIDIA, libx264 otherwise.

| Zone (px) | Content |
|---|---|
| 0–200 | Safe margin: the app's search bar and icons go here. Blurred background |
| 200–902 | The streamer, cropped from the facecam |
| ~902 | UPPERCASE subtitles, Arial Black 68, black outline |
| 902–1600 | Center of the gameplay, without the facecam |
| 1600–1920 | Safe margin: the caption and buttons go here. Blurred background |

Each clip's original horizontal cut is saved in `horizontal/` at the source resolution (normally 1920x1080).

## Rules

- **Explicit content:** skip ranges with nudity or sexual content on screen.
- **Muted ranges:** Twitch mutes parts of the VOD for copyright. They're in `meta.json` (`muted`); avoid them.
- **Licensed music:** if a clip has licensed music in the background, say so, because YouTube may flag it for copyright.
- **Tools:** never call `gql.twitch.tv` by hand; the chat is downloaded only with `fetch_chat.py`.

## Known issues

- **Out-of-sync cuts.** If a clip starts or ends somewhere odd, check `align.py`. In Twitch's `.mp4` segments the PTS (the internal timestamp) starts at the VOD second + ~64; the scripts already account for it.
- **A tool is missing.** If `fetch_chat.py` says TwitchDownloaderCLI is missing, or ffmpeg has no libass, run `pipeline/setup_tools.py` again.
- **Expired VOD.** Twitch deletes VODs after 7, 14 or 60 days. If it's gone, nothing can be done.
