"""1.3.4 Continue trap, and the 1.3.7 path that cannot strand a co-op pair in Pohjola."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "TuonelanPolku1.3.4.pygame"
FAIL = []


def req(ok, name):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        FAIL.append(name)


PROBE = r"""
import json, os, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["TUONELA_WINDOWED"] = "1"
path, save_path, expect = sys.argv[1], sys.argv[2], sys.argv[3]
os.environ["TUONELA_SAVE"] = save_path
os.environ["TUONELA_SETTINGS"] = save_path + ".settings.json"
ns = {"__name__": "tp"}
exec(compile(open(path, encoding="utf-8").read(), path, "exec"), ns)
import pygame
pygame.init()
screen = pygame.display.set_mode((ns["W"], ns["H"]))
g = ns["Game"](screen, test=True)
p1, p2 = ns["ScriptPad"]("p1"), ns["ScriptPad"]("p2")
g.add_pad(p1); g.add_pad(p2); g.last_pad = p1
sv = ns["new_save"]("warrior")
sv["stats"]["vit"] = 3
sv["bosses"] = ["hiisi", "turso", "tytti"]
sv["bonfire"] = "b9"
sv["louhi_unlocked"] = True
sv["done"] = True
sv["p2"] = {"cls": "sage", "level": 2, "stats": {"vit": 1, "end": 0, "str": 0, "foc": 1}, "souls": 40}
ns["write_save"](sv)
g.start_session(sv, p1)
g.add_p2("sage", p2)
g.players[0].ch["stats"]["str"] = 4
g.players[1].ch["souls"] = 77
class Boss(object):
    key = "louhi"
    x = 100
    y = 80
g.on_boss_dead(Boss())
disk = json.load(open(save_path, encoding="utf-8"))
sealed = disk.get("bosses") and "louhi" in disk["bosses"] and disk.get("vellamo_unlocked") and disk["stats"]["str"] == 4 and disk["p2"]["souls"] == 77 and os.path.exists(save_path + ".bak")
g.enter_vellamo()
g.back_to_title()
g.begin_session(g.title_save)
g.up_loading()
report = {
    "sealed": bool(sealed),
    "bonfire": g.save["bonfire"],
    "visited": bool(g.save.get("vellamo_visited")),
    "x": g.players[0].x,
    "gate": any(item[2] == "vellamo_gate" for item in g.interactables()) if g.area == "pohjola" else False,
    "area": g.area,
    "ng": g.save.get("ng"),
    "ng_ready": bool(g.save.get("ng_ready")),
}
# A save already rewritten by 1.3.4 Continue: Louhi dead, bonfire Pohjola, flags either way.
stuck = ns["new_save"]("hunter")
stuck["bosses"] = ["louhi"]
stuck["bonfire"] = "b9"
stuck["done"] = True
stuck["vellamo_visited"] = False
stuck["vellamo_unlocked"] = False
fixed = ns["sanitize_save"](stuck, set(ns["BONFIRES"]))
report["migrated"] = fixed["bonfire"] == "b10" and fixed["vellamo_unlocked"] is True and fixed["vellamo_visited"] is False
json.dump(report, open(expect, "w", encoding="utf-8"))
"""


def run_probe(game_file):
    tmp = tempfile.mkdtemp(prefix="realm_")
    save_path = os.path.join(tmp, "save.json")
    expect = os.path.join(tmp, "out.json")
    script = os.path.join(tmp, "probe.py")
    open(script, "w", encoding="utf-8").write(PROBE)
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    proc = subprocess.run([sys.executable, script, str(game_file), save_path, expect], capture_output=True, text=True, env=env)
    if proc.returncode != 0 or not os.path.exists(expect):
        print(proc.stdout[-400:])
        print(proc.stderr[-800:])
        return None
    return json.load(open(expect, encoding="utf-8"))


def main():
    old = run_probe(OLD)
    req(old is not None, "1.3.4 probe ran")
    if old:
        req(old["sealed"], "1.3.4 does save Louhi immediately")
        req(old["bonfire"] == "b9" and old["area"] != "ranta", "1.3.4 Continue returns to Pohjola (%s %s)" % (old["bonfire"], old["area"]))
        req(old["visited"] and not old["gate"], "1.3.4 hides the gate after Vellamo was entered")
    from lib import G, new_game, ScriptPad
    fresh = run_probe(os.environ.get("TP_FILE") or str(ROOT / ("TuonelanPolku%s.pygame" % json.load(open(ROOT / "version.json"))["version"])))
    req(fresh is not None, "current probe ran")
    if fresh:
        req(fresh["sealed"], "Louhi defeat is saved at once with both characters and a backup")
        req(fresh["bonfire"] == "b10" and fresh["area"] == "ranta", "Continue resumes at the Vellamo entrance (%s %s)" % (fresh["bonfire"], fresh["area"]))
        req(fresh["ng"] == 0 and fresh["ng_ready"] is False, "NG+ is not started by Louhi")
        req(fresh["migrated"], "an old Pohjola save with Louhi defeated migrates to b10 without pretending it was visited")
    # Gate still works if a migrated player walks to Pohjola.
    g = new_game()
    sv = G["new_save"]("warrior")
    sv["bosses"] = ["louhi"]
    sv["bonfire"] = "b9"
    sv["vellamo_visited"] = True
    pad = ScriptPad("back")
    from lib import start
    start(g, save=sv, bonfire="b9", pad=pad)
    req(g.area == "pohjola" and any(item[2] == "vellamo_gate" for item in g.interactables()), "Pohjola keeps a working gate after Louhi")
    # Scare screenshots from the current build.
    g = new_game()
    sv = G["new_save"]("warrior")
    sv["bosses"] = ["hiisi", "turso", "tytti"]
    start(g, save=sv, bonfire="b8")
    g.start_ending()
    g.draw()
    import pygame
    pygame.image.save(g.canvas, "/tmp/louhi_teksti.png")
    g.end_page = 3
    g.end_t = 118
    g.up_ending()
    req(g.state_name == "ending", "119 frames into the last screen is not yet the scare")
    g.up_ending()
    req(g.state_name == "interrupt", "frame 120 of the last screen starts the scare")
    for _ in range(16):
        g.up_interrupt()
    g.dr_interrupt()
    pygame.image.save(g.canvas, "/tmp/louhi_sarkyma.png")
    req(g.canvas.get_at((20, 20)) != (0, 0, 0, 255), "shatter is visible")
    if FAIL:
        print("REALM FAIL", len(FAIL))
        sys.exit(1)
    print("OK realm continue")


if __name__ == "__main__":
    main()
