# Edit library

Everything here can be used in any edit. `pipeline/edit.py new` copies `sfx/` and `stickers/` into each edit project, so a composition uses them as `sfx/<name>` and `stickers/<name>`.

## Sound effects (`sfx/`)

Made for this project from synthesized tones and noise: free to use, no attribution needed.

| file | sounds like | good for |
|---|---|---|
| `whoosh.wav` | air sweep, 0.7 s | a label or title flying in |
| `pop.wav` | short bubbly pop | a sticker appearing |
| `boom.wav` | deep hit, 1 s | the big moment, a punch-in zoom |
| `ding.wav` | bell, 1 s | "correct", a reveal, a good idea |
| `honk.wav` | car horn, 0.4 s | a fail, something absurd |
| `riser.wav` | rising tone, 1.2 s | tension right before the moment |
| `fail.wav` | falling tone, 0.9 s | a sad or failed moment |
| `boing.wav` | cartoon spring, 0.5 s | a jump, a silly reaction |

Add your own: drop `.wav` or `.mp3` files in `sfx/` (only ones you have the rights to use).

## Stickers

- **Emoji** need no file: `<div class="clip sticker" …>💀</div>`. They're drawn with the system's emoji font.
- **Images:** drop `.png` (transparent background) or `.gif` files in `stickers/` and use `<img class="clip img" src="stickers/<file>" …>`.
