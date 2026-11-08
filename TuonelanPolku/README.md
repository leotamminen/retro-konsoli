# Tuonelan polku source

The playable release is one pygame file. This folder is the source. Older releases in the repository stay byte-for-byte as they are. Do not commit to `master` from this work.

## Version

`version.json` is the only version. `build.py` embeds that string once and names the release `TuonelanPolku<version>.pygame`. The title reads the same value. Source modules do not assign `VERSION`.

## Build

From this directory:

```bash
python3 build.py
```

The script reads `src/pNN_*.py` in numeric order and embeds `maps/world.json` and `maps/vellamo.json`. The built file does not open those JSON files at runtime. Runtime dependencies stay Python 3 and pygame 2.6.1. Audio is still generated in the game. The only `main()` call is `src/p99_entry.py`.

Module responsibilities, and the patches that are still separate, are listed in `src/LAYERS.md`.

## Maps

`maps/world.json` is the forest, swamp, river and Pohjola. `rows` is run-length encoding, `count:tile`. Tiles are 0 air, 1 solid, 2 platform, 3 ladder, 4 thorns, 5 water. `extras.blocks` adds optional platforms as `[x, y, w, h, t]` and does not rewrite the first three boss rooms. `maps/vellamo.json` is the later realm in the same block form, on a solid floor at row 20. Leave the boss columns named in that file empty.

Edit the JSON, run `python3 build.py`, then `python3 tests/test_routes.py`. There is no separate editor program.

## Tests

```bash
python3 tests/test_release.py
python3 tests/test_routes.py
bash tests/run_all.sh
```

`test_release.py` executes the built file as `__main__` and drives `update`/`draw`. `run_all.sh` rebuilds, executes that same file as a library so the loop does not start, and runs the older regression scripts. Controllers here are SDL virtual devices or script pads, not a physical DualShock and not Batocera. Release-test screenshots go to `/tmp/tp134`.
