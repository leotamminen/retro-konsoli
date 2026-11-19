# Playtest

Headless play of a real game in this repo: dummy SDL video and audio, bot pads, an H.264 recording, and short clips around anything interesting.

The shared loop lives here. Each game adds an adapter that writes the same input structure its controller code already reads. Kultakiri is the first adapter. TuonelanPolku and HyppyUkot can get one later without changing this runner.

## Run

From the repository root:

```bash
python3 tools/playtest/run.py kultakiri --players 4 --rounds 1 --seed 1
```

`--players` is how many human-like bots. `--cpus` fills the rest of the four slots with the game's own CPU opponents, and `--difficulty` is helppo, normaali or vaikea. Together they must be 2–4. `--rounds` is how many rounds to play before stopping on the scoreboard. `--seed` fixes the bot mistakes and the level shuffle. `--max-seconds` stops early; leave it at 0 for a full round. `--no-video` skips ffmpeg and still plays the rounds.

Needs Python 3, pygame, and `ffmpeg` with libx264. The game package is imported from `Kultakiri/` on disk; nothing is installed.

## What it writes

`tools/playtest/out/<game>-p<N>-seed<S>/`

- `full.mp4` — the whole run, 30 fps, nearest-neighbour scaled from the game's 320×180 canvas to 960×540
- `clips/` — 5–10 second cuts around falls, ghosts, powerups, the round end, and any anomaly
- `events.jsonl` — one JSON object per event
- `report.md` — what each clip shows, and any anomaly

The game still simulates at 60 fps. The video keeps every other frame, so one video second is one game second.

## What it watches

Falls, ghost rescues and returns, being knocked out, powerup pickups, powerup effects (double jump, shield block, speed, glide, magnet, slow bubble), bumps, and the round ending.

Anomalies: an exception, a runner who holds right for more than 3 seconds without moving, a position that is not a finite number or is still on screen when it should have been eliminated, and a frame that takes more than 50 ms and at least eight times the recent median.

## Adding a game

Add `tools/playtest/adapters/<game>.py` and register it in `adapters/__init__.py`.

The adapter needs:

- `start(players, seed, rounds)` — boot the real game under the dummy driver
- `write_inputs()` — put this frame's buttons where that game's pad poll reads them
- `tick()` / `draw()` / `surface()` — one real update, then the canvas
- `collect(frame)` — events and anomalies observed after the update
- `finished()` — true once the requested rounds are on the scoreboard
- `width`, `height`, `sim_fps`, `video_fps`, `name`

Do not teach the runner about one game's physics. Keep that in the adapter.
