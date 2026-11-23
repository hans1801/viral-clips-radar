# viral-clips-radar

This repo turns a Twitch VOD into vertical 9:16 shorts, plus the original horizontal cut of each one. It picks the moments from the chat's spikes of laughter and reactions, matched with the streamer's transcript. Then each short can be dressed up (stickers, titles, sound effects, zooms) in an edit layer with a live studio at http://localhost:3006. The user may be a beginner: explain each step in one plain line, in the user's language, with no jargon.

## When the user gives you a VOD

A short message is enough: "make the best clips from <link>", "saca los mejores clips de <link>", a bare `twitch.tv/videos/…` link, etc. Treat it as the production prompt: read `prompts/production.md` and follow its steps exactly, filling its options from the message:

- **Link:** the one they gave you. If there's none, ask for it; that's the only thing you can't infer.
- **Number of clips:** 10–12, unless they ask for a different number.
- **Length:** ~90 s, unless they ask for a different length.
- **Language:** `auto`, which detects it from the audio. Tell them in one line which language was detected.
- **Subtitles:** yes (swear words masked), unless they say otherwise.

Do it in one go: picking, cutting, rendering and checking are your own working tools, so check them yourself and don't stop to ask for approval. Only stop for what is truly the user's call: the stream is still live, or the VOD is sub-only. At the end, deliver the clip table, the folders and the studio link. The user then asks for changes or edits by clip number.

## When the user asks for edits

"Edit clip 03: …", "ponle un sticker de 💀 cuando…", "add a sound when…", "render it": read `prompts/edit.md` and follow it. Write the edits yourself, check them with lint and snapshots, keep the studio on that clip, and only render when they ask (or when they say they like it).

## If something is missing

If `.venv`, `tools/TwitchDownloaderCLI`, ffmpeg or `editor/node_modules` is missing, the project isn't set up yet. Tell the user and offer to run the steps in `prompts/setup.md` first. For a quick check, run `pipeline/setup_tools.py`: it must end with the "ALL SET" box.

## Fixed rules

- Never delete anything in `clips/` unless the user asks.
- Never call `gql.twitch.tv` by hand: the chat is downloaded with `pipeline/fetch_chat.py`.
- Always use the environment's Python (`.venv/bin/python`, or `.venv\Scripts\python` on Windows), so the scripts find the right ffmpeg (`tools/bin` on macOS) and yt-dlp.
- In edits, use only the library's sounds, emoji, or files the user provides and has rights to.
