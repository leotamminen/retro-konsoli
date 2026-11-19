#!/usr/bin/env python3
"""Headless playtest. Example:

    python3 tools/playtest/run.py kultakiri --players 4 --rounds 1 --seed 1
"""
import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run a game headless, record video, and cut highlights.")
    parser.add_argument("game", help="Adapter name, for example kultakiri")
    parser.add_argument("--players", type=int, default=4)
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", type=Path, default=None, help="Output directory (default: tools/playtest/out/...)")
    parser.add_argument("--max-seconds", type=float, default=0, help="Stop early. 0 plays until the rounds finish.")
    parser.add_argument("--cpus", type=int, default=0, help="CPU opponents. --players counts human-like bots.")
    parser.add_argument("--difficulty", default="normaali", choices=("helppo", "normaali", "vaikea"))
    parser.add_argument("--no-video", action="store_true", help="Skip ffmpeg. Still plays the rounds.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    # Must be set before pygame (imported by the adapter) opens a display.
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ.setdefault("KULTAKIRI_NO_MUSIC", "1")
    os.environ.setdefault("KULTAKIRI_NO_SFX", "1")
    os.environ.setdefault("KULTAKIRI_WINDOWED", "1")
    from adapters import get_adapter
    from session import run_session

    adapter = get_adapter(args.game)
    out = args.out
    if out is None:
        out = HERE / "out" / ("%s-p%d-seed%d" % (adapter.name, args.players, args.seed))
    print(
        "playtest %s  players=%d cpus=%d difficulty=%s rounds=%d seed=%d"
        % (adapter.name, args.players, args.cpus, args.difficulty, args.rounds, args.seed)
    )
    run_session(
        adapter, args.players, args.rounds, args.seed, out,
        max_seconds=args.max_seconds, cpus=args.cpus,
        difficulty=args.difficulty, video=not args.no_video,
    )


if __name__ == "__main__":
    main()
