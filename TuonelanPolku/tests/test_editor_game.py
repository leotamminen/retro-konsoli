"""Edited map builds into a preview and is active when that file runs as __main__."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from editor.model import PLAT, MapDoc

SHIPPED = ROOT / "TuonelanPolku1.3.5.pygame"
SHIPPED_HASH = "cdfc238275245e02c7cb6ccc3ab28fd4a73b4eedd969f928d4c851050b517e8f"
FAIL = []


def req(ok, name):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        FAIL.append(name)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="editor_game_"))
    env_save = os.environ.get("TUONELA_SAVE")
    env_set = os.environ.get("TUONELA_SETTINGS")
    try:
        body(tmp)
    finally:
        if env_save is None:
            os.environ.pop("TUONELA_SAVE", None)
        else:
            os.environ["TUONELA_SAVE"] = env_save
        if env_set is None:
            os.environ.pop("TUONELA_SETTINGS", None)
        else:
            os.environ["TUONELA_SETTINGS"] = env_set
        shutil.rmtree(tmp, ignore_errors=True)
    if FAIL:
        print("EDITOR GAME FAIL", len(FAIL))
        sys.exit(1)
    print("OK editor game")


def body(tmp):
    before = hashlib.sha256(SHIPPED.read_bytes()).hexdigest()
    req(before == SHIPPED_HASH, "1.3.5 hash before the editor build")
    stamp = SHIPPED.stat().st_mtime
    checked = subprocess.run([sys.executable, str(ROOT / "build.py"), "--check"], cwd=str(ROOT), capture_output=True, text=True)
    req(checked.returncode == 0 and SHIPPED.stat().st_mtime == stamp, "check does not rewrite the shipped file")

    maps = tmp / "spaced maps"
    maps.mkdir()
    shutil.copy(ROOT / "maps" / "world.json", maps / "world.json")
    shutil.copy(ROOT / "maps" / "vellamo.json", maps / "vellamo.json")
    doc = MapDoc.load(maps / "world.json")
    doc.paint(8, 28, PLAT)
    doc.add_spawn("peikko", 14, 0)
    ok, errors = doc.save(maps / "world.json")
    req(ok and errors == [], "edited map saved " + " ".join(errors))
    preview = tmp / "TuonelanPolku-esikatselu.pygame"
    built = subprocess.run(
        [sys.executable, str(ROOT / "build.py"), "--maps", str(maps), str(preview)],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    req(built.returncode == 0 and preview.is_file(), "preview build " + built.stderr[-200:])
    refused = subprocess.run(
        [sys.executable, str(ROOT / "build.py"), "--maps", str(maps), str(SHIPPED)],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    after = hashlib.sha256(SHIPPED.read_bytes()).hexdigest()
    req(refused.returncode != 0 and after == SHIPPED_HASH, "edited maps cannot overwrite 1.3.5")

    os.environ["TUONELA_SAVE"] = str(tmp / "save.json")
    os.environ["TUONELA_SETTINGS"] = str(tmp / "settings.json")
    os.environ["TUONELA_WINDOWED"] = "1"
    source = preview.read_text(encoding="utf-8")
    old = "    while g.running:\n        g.update(); g.draw()\n        pygame.display.flip()\n        clock.tick(60)\n"
    new = "    g.update(); g.draw(); PROBE(g)\n    while False:\n        pass\n        pass\n"
    req(source.count(old) == 1 and source.count('if __name__ == "__main__":') == 1, "preview has one real loop")
    seen = {}

    def probe(game):
        seen["grid"] = game and ns["GRID"][28][8] == PLAT
        seen["spawn"] = any(kind == "peikko" and column == 14 for kind, column, _row in ns["SPAWNS"])
        pad = ns["ScriptPad"]("editor")
        game.add_pad(pad)
        game.start_session(ns["new_save"]("warrior"), pad)
        seen["enemy"] = any(getattr(enemy, "kind", None) == "peikko" and int(enemy.x // 16) == 14 for enemy in game.enemies)
        player = game.players[0]
        player.x = 8 * 16 + 8
        player.y = 30 * 16
        game.snap_cam()
        game.draw()
        surf = game.chunk(0)
        color = surf.get_at((8 * 16 + 2, 28 * 16 + 1))
        seen["chunk"] = color[0] > 120 and color[1] > 70 and color[2] < 110
        sx = int(8 * 16 - game.cam[0]) + 2
        sy = int(28 * 16 - game.cam[1]) + 1
        pixel = game.canvas.get_at((sx, sy))
        seen["screen"] = pixel[0] > 100 and 0 <= sx < ns["W"] and 0 <= sy < ns["H"]

    ns = {"__name__": "__main__", "PROBE": probe}
    exec(compile(source.replace(old, new, 1), str(preview), "exec"), ns)
    req(seen.get("grid"), "built game grid has the platform")
    req(seen.get("spawn"), "built game spawn list has the enemy")
    req(seen.get("enemy"), "enemy is active in the session")
    req(seen.get("chunk"), "platform is visible in the chunk renderer")
    req(seen.get("screen"), "platform is visible on the game canvas")
    req("pouch_uusi_" not in json.dumps(json.loads((ROOT / "maps" / "world.json").read_text(encoding="utf-8"))), "canonical world.json was not rewritten")


if __name__ == "__main__":
    main()
