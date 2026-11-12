# Working on this repository

The playable games are single pygame files. Older files under `TuonelanPolku/` and `HyppyUkot/` are released artifacts. Do not edit them, replace them, or regenerate a version that already exists.

## Tuonelan polku

Change the game by editing:

- `TuonelanPolku/src/` — the modules listed in `TuonelanPolku/build.py` (`ORDER`)
- `TuonelanPolku/maps/world.json` and `TuonelanPolku/maps/vellamo.json`
- `TuonelanPolku/version.json` — the only version string

Then run `python3 build.py` from `TuonelanPolku/`. That writes a new `TuonelanPolku<version>.pygame`. The built file is generated. Do not hand-edit it. If the version did not change, you are about to overwrite a release; bump `version.json` first.

`python3 run_source.py` runs the same modules in a desktop window. The one-file release is what goes on Batocera. It needs only Python and pygame, and it carries the maps inside it.

`python3 -m editor` is a separate desktop editor for `maps/world.json` and `maps/vellamo.json`. It is not shipped inside the pygame file and it is not needed on the Pi. Do not point a normal build at an existing `TuonelanPolku*.pygame`; `build.py` leaves those files untouched unless the generated text is already identical. Preview builds go to a new filename.

A module owns its classes. Do not add a later file that does `GameCore.method = ...`, `Player.method = ...`, or `setattr` on a class. Put the behavior on the class. `build.py` refuses that kind of rebinding, a missing module, and a module that is out of order.

## What stays

`TuonelanPolku1.0` through `TuonelanPolku1.3.4`, and every `HyppyUkot` file, stay byte-for-byte. Tests check their SHA-256. A new executable gets the next version in `version.json`, and the title, the filename, and that file have to match.
