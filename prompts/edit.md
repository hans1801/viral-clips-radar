# Edit prompt: stickers, titles, sound effects and zooms

The automatic shorts are the base. To dress one up, open a chat in the project folder and say what you want, by clip number. For example:

```text
Edit clip 03: put a hook title "HE DIDN'T SEE IT COMING 😭", a 💀 sticker with a honk when he gets run over,
a punch-in zoom on that moment and a progress bar.
```

You don't need this template: `CLAUDE.md` brings Claude here whenever you ask for edits. The studio stays open at **http://localhost:3006**, where you can play the clip, scrub the timeline and see every layer. Ask for changes until you like it, then say "render it".

---

## Steps (instructions for Claude)

`PY` is the environment's Python (`.venv/bin/python`, or `.venv\Scripts\python` on Windows). `W` is the VOD's `clips/<streamer>_<date>/work` folder.

1. **Project.** If `clips/<…>/edits/<clip>/index.html` doesn't exist, run `PY pipeline/edit.py new W <NN>`. It builds the layers from the original horizontal cut: blurred background, facecam, gameplay (with the audio) and the subtitles as text.
2. **Studio.** Run `PY pipeline/edit.py preview W <NN> --open` and give the user the link it prints (http://localhost:3006/…). Only one clip is shown at a time; previewing another clip switches it.
3. **Find the moments.** Use `PY pipeline/seg.py W h:mm:ss-h:mm:ss` and the clip's `work/subs/<clip>.json` to time each edit to the words. Times in the composition are **seconds from the start of the clip**, not VOD time (clip time = VOD time − the clip's start in `clips.tsv`).
4. **Write the edits** only between the markers in `index.html`:
   - elements between `<!-- EDITS:HTML START -->` and `<!-- EDITS:HTML END -->`;
   - animation calls between `// EDITS:JS START` and `// EDITS:JS END`.
   `edit.py new` keeps those two blocks if the base is rebuilt. Don't touch the base layers.
5. **Check it.** Run `editor/node_modules/.bin/hyperframes lint <project>` (0 errors), then `hyperframes snapshot <project> --at <t1>,<t2>,… --no-end --describe false` at the edited moments and look at the stills yourself. Fix whatever overlaps or reads badly, then tell the user it's ready to see in the studio.
6. **Render** when the user asks: `PY pipeline/edit.py render W <NN>` → `clips/<…>/edited/<clip>.mp4` (1080x1920, 60 fps). A 90-second clip takes ~3 min on a Mac with Apple Silicon.

## Building blocks

Ready-made CSS classes (in the template) and helper functions:

| what | HTML | animation |
|---|---|---|
| Hook title (first seconds) | `<div id="hook" class="clip hook" data-start="0" data-duration="4">TEXT <span class="hl">HIGHLIGHT</span></div>` | `hook('#hook', 3.5)` |
| Label / sticker card | `<div id="x" class="clip label" style="left:90px; top:1000px" data-start="35" data-duration="6">📸 TEXT</div>` | `pop('#x', 35, 6, { rot: -6, rotTo: -6 })` |
| Emoji sticker | `<div id="s" class="clip sticker" style="left:700px; top:1080px" data-start="44" data-duration="5">💀</div>` | `pop('#s', 44, 5, { from: 0.2, rot: -30, rotTo: 8 })` + `shake('#s', 44.3)` |
| Image sticker | `<img id="i" class="clip img" src="stickers/file.png" style="left:…; top:…; width:300px" data-start="…" data-duration="…">` | `pop('#i', t, dur)` |
| Punch-in zoom (gameplay only) | — | `punch(43.3, 2, 1.15)` |
| Progress bar | `<div id="bar" class="clip bar" data-start="0" data-duration="<clip length>"></div>` | `progress('#bar')` |
| Sound effect | `<audio id="sfx-boom-1" class="clip" src="sfx/boom.wav" data-start="43.3" data-duration="1" data-volume="0.7"></audio>` | — |

The sound effects are listed in `editor/library/README.md`: whoosh, pop, boom, ding, honk, riser, fail and boing.

## Rules

- **Every timed element needs a unique `id`.** An `<audio>` without an `id` is **silent** in the render.
- Every timed element has `class="clip"`, `data-start` and `data-duration`. An `<audio>`'s `data-duration` is the sound's length.
- **Safe zones** (1080x1920): nothing in y 0–200 (the app's top bar) or y 1600–1920 (caption and buttons), and keep stickers away from the right 120 px (like and comment buttons). The facecam is y 200–902 and the gameplay y 902–1600; the subtitles sit on the seam (y ≈ 902), so don't put stickers right there.
- **Timing:** a sound effect lands on the frame of its moment, or 0.05–0.1 s before. A zoom or sticker goes on the word or the action, not after it. Leave the first 0.3 s clean except for the hook.
- **Don't overdo it:** 3–6 edits per minute. Every edit has to point at something that's happening.
- **Volume:** sound effects at `data-volume` 0.5–0.9 so they don't drown the streamer's voice.
- **Original assets only:** the library's sounds, emoji, or files the user provides and has rights to. Never sound effects or stickers taken from the internet without a license.
