# Tuonelan polku source

The playable release is one pygame file. This folder is the source. Older releases in the repository stay byte-for-byte as they are, including `TuonelanPolku1.3.4.pygame`. Do not commit to `master` from this work.

Edit `src/` and `maps/`. Do not hand-edit a generated `TuonelanPolku*.pygame`. The repository rule is also in `AGENTS.md` at the root.

## Version

`version.json` is the only version. `build.py` embeds that string once and names the release `TuonelanPolku<version>.pygame`. The title reads the same value. Source modules do not assign `VERSION`. The current source builds 1.3.7. `TuonelanPolku1.3.4.pygame`, `TuonelanPolku1.3.5.pygame` and `TuonelanPolku1.3.6.pygame` stay as they were. The editor version is separate and shown in the editor window.

## Build

From this directory:

```bash
python3 build.py
python3 run_source.py
```

`build.py` reads `src/` in the order named by `ORDER`. It fails if a module is missing, extra, out of dependency order, or if it rebinds a class method from outside the class. It embeds `maps/world.json` and `maps/vellamo.json`. The built file does not open those JSON files at runtime. Runtime dependencies stay Python 3 and pygame. Audio is generated in the game. The only `main()` call is `src/entry.py`, and it is last.

`run_source.py` loads those same modules for a desktop window. The one-file release is the Batocera file.

Module ownership is listed in `src/LAYERS.md`.

## Maps

`maps/world.json` is the forest, swamp, river and Pohjola. `rows` is run-length encoding, `count:tile`. Tiles are 0 air, 1 solid, 2 platform, 3 ladder, 4 thorns, 5 water. `extras.blocks` adds optional platforms as `[x, y, w, h, t]` and does not rewrite the first three boss rooms. `maps/vellamo.json` is the later realm in the same block form, on a solid floor at row 20. Leave the boss columns named in that file empty.

Edit the JSON by hand or with the editor, then `python3 tests/test_routes.py`. `python3 build.py` refuses to overwrite an existing `TuonelanPolku<version>.pygame`. A preview from the editor is written to `esikatselu/TuonelanPolku-esikatselu.pygame`.

## Editor

`python3 -m editor` opens the Finnish map editor (Python 3 and pygame). It is a development tool, not part of the one-file game. `editor/KAYTTO.txt` is the Windows guide. The normal brush paints overlay blocks and leaves the base world's run-length rows alone. Closing the window does not save. Saving writes the canonical JSON and keeps the previous file in `maps/backups/`. The editor does not open the game's save or settings.

## Tests

```bash
python3 tests/test_release.py
python3 tests/test_routes.py
bash tests/run_all.sh
```

`test_release.py` executes the built file as `__main__` and drives `update`/`draw`. `run_all.sh` rebuilds, then runs the architecture audit and the older regression scripts. Controllers here are SDL virtual devices or script pads, not a physical DualShock and not Batocera.
