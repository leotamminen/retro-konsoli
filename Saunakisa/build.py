#!/usr/bin/env python3
# Bundle the package into one versioned file for Batocera.
# The only version number is version.json. Copy the result to /userdata/roms/pygame/
import json
import pathlib
import py_compile
import sys

ROOT = pathlib.Path(__file__).resolve().parent
ORDER = (
    "const.py",
    "font.py",
    "text.py",
    "input.py",
    "settings.py",
    "audio.py",
    "world.py",
    "actors.py",
    "draw.py",
    "game.py",
    "main.py",
)


def strip_local_imports(src):
    lines = src.splitlines(True)
    out = []
    skipping = False
    depth = 0
    for line in lines:
        if skipping:
            depth += line.count("(") - line.count(")")
            if depth <= 0:
                skipping = False
            continue
        stripped = line.strip()
        if stripped.startswith("from .") or stripped.startswith("from saunakisa"):
            depth = line.count("(") - line.count(")")
            if depth > 0:
                skipping = True
            continue
        out.append(line)
    return "".join(out)


def main():
    version = str(json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]).strip()
    if not version:
        sys.exit("version.json is empty")
    parts = [
        "#!/usr/bin/env python3\n",
        "# SAUNAKISA - rento 2-4 pelaajan saunakisa Batoceralle (pygame 2).\n",
        "# Yksi tiedosto, ei assetteja. Kopioi kansioon /userdata/roms/pygame/\n",
        "# Versio tulee buildin aikana version.jsonista.\n",
        "def load_version():\n",
        "    return %r\n" % version,
        "\n",
    ]
    for name in ORDER:
        src = (ROOT / "saunakisa" / name).read_text(encoding="utf-8")
        parts.append("\n# ---- %s ----\n" % name)
        parts.append(strip_local_imports(src))
        if not parts[-1].endswith("\n"):
            parts.append("\n")
    out = ROOT / ("Saunakisa%s.pygame" % version)
    out.write_text("".join(parts), encoding="utf-8")
    out.chmod(0o755)
    py_compile.compile(str(out), doraise=True)
    print(out)


if __name__ == "__main__":
    main()
