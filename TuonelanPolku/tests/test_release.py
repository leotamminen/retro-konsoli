#!/usr/bin/env python3
"""Run the built release as __main__ with a bounded real update/draw loop."""
import ctypes, hashlib, json, os, sys, time, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]
REAL = ROOT / ("TuonelanPolku%s.pygame" % VERSION)
OUT = Path("/tmp/tp134")
OUT.mkdir(exist_ok=True)
os.environ.update(
    SDL_VIDEODRIVER="dummy",
    SDL_AUDIODRIVER="dummy",
    SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS="1",
    SDL_GAMECONTROLLER_ALLOW_BACKGROUND_EVENTS="1",
    PYGAME_HIDE_SUPPORT_PROMPT="1",
    TUONELA_WINDOWED="1",
    TUONELA_SETTINGS=str(OUT / "settings.json"),
    TUONELA_SAVE=str(OUT / "save.json"),
    TUONELA_MUSIC_CACHE=str(OUT / "music"),
)
(OUT / "music").mkdir(exist_ok=True)
src = REAL.read_text(encoding="utf-8")
old = """    while g.running:\n        g.update(); g.draw()\n        pygame.display.flip()\n        clock.tick(60)\n"""
new = """    g.update(); g.draw(); PROBE(g)\n    while False:\n        pass\n        pass\n"""
assert src.count(old) == 1 and src.count('if __name__ == "__main__":') == 1
src2 = src.replace(old, new, 1).replace("    pygame.quit()\n", "    return\n", 1)
R = {"checks": []}

def check(name, ok, detail=None):
    R["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
    print(("PASS" if ok else "FAIL"), name, "" if detail is None else detail, flush=True)

def PROBE(g):
    import pygame
    ns = sys._getframe(1).f_globals
    check("version on first frame", ns["VERSION"] == VERSION)
    check("expanded map before the loop", ns["COLS"] == 1326 and len(ns["GRID"][0]) == 1326)
    check("entrypoint is the module call", sys._getframe(2).f_lineno > ns["main"].__code__.co_firstlineno)
    texts = []
    orig = g.text
    def wrap(t, x, y, *a, **k):
        texts.append(str(t)); return orig(t, x, y, *a, **k)
    g.text = wrap; g.draw(); g.text = orig
    pygame.image.save(g.canvas, str(OUT / "title.png"))
    check("title draws the version", ("VERSION " + VERSION) in texts)
    check("test weapon defaults off", ns["SETTINGS"].get("test_weapon") is False)

    sdl = ctypes.CDLL("/home/ubuntu/.local/lib/python3.12/site-packages/pygame.libs/libSDL2-2-1667c208.0.so.0.2800.4")
    sdl.SDL_JoystickAttachVirtual.argtypes = [ctypes.c_int] * 4
    sdl.SDL_JoystickAttachVirtual.restype = ctypes.c_int
    sdl.SDL_JoystickOpen.argtypes = [ctypes.c_int]
    sdl.SDL_JoystickOpen.restype = ctypes.c_void_p
    class GUID(ctypes.Structure):
        _fields_ = [("data", ctypes.c_uint8 * 16)]
    sdl.SDL_JoystickGetGUID.argtypes = [ctypes.c_void_p]
    sdl.SDL_JoystickGetGUID.restype = GUID
    sdl.SDL_JoystickGetGUIDString.argtypes = [GUID, ctypes.c_char_p, ctypes.c_int]
    sdl.SDL_GameControllerAddMapping.argtypes = [ctypes.c_char_p]
    sdl.SDL_GameControllerAddMapping.restype = ctypes.c_int
    sdl.SDL_JoystickSetVirtualButton.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint8]
    sdl.SDL_JoystickSetVirtualButton.restype = ctypes.c_int
    sdl.SDL_JoystickSetVirtualAxis.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int16]
    sdl.SDL_JoystickSetVirtualAxis.restype = ctypes.c_int
    sdl.SDL_JoystickDetachVirtual.argtypes = [ctypes.c_int]
    sdl.SDL_JoystickDetachVirtual.restype = ctypes.c_int

    def attach(kind=1):
        idx = sdl.SDL_JoystickAttachVirtual(kind, 6, 16, 1)
        raw = sdl.SDL_JoystickOpen(idx)
        buf = ctypes.create_string_buffer(40)
        sdl.SDL_JoystickGetGUIDString(sdl.SDL_JoystickGetGUID(raw), buf, 40)
        guid = buf.value.decode()
        mapping = (f"{guid},PS4 Compatible,a:b0,b:b1,x:b2,y:b3,back:b8,start:b9,"
                   "leftshoulder:b4,rightshoulder:b5,lefttrigger:b6,righttrigger:b7,"
                   "leftstick:b10,rightstick:b11,dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,"
                   "leftx:a0,lefty:a1,platform:Linux,")
        if kind == 1:
            sdl.SDL_GameControllerAddMapping(mapping.encode())
        return idx, raw

    def buttons(raw, down):
        for i in range(16):
            sdl.SDL_JoystickSetVirtualButton(raw, i, 1 if i in down else 0)

    def pump():
        g.poll_events(); g.poll()

    a_idx, a_raw = attach(1)
    b_idx, b_raw = attach(1)
    pump()
    ap = next(p for p in g.pads.values() if p.kind == "gc")
    bp = next(p for p in g.pads.values() if p.kind == "gc" and p is not ap)
    check("two distinct controllers and one keyboard", ap.id != bp.id and g.kb in g.pads.values())
    ids = [p.id for p in g.pads.values() if str(p.id).startswith("js")]
    check("no duplicate pad per controller", len(ids) == len(set(ids)) == 2)

    # One shared press moves a menu by one entry even if both pads report it.
    g.state_name = "title"; g.menu_i["title"] = 0
    for pad in (ap, bp):
        pad.prev = pad.blank(); c = pad.blank(); c["down"] = True; pad.cur = c
    before = g.menu_i["title"]
    g.up_title()
    check("one press moves one menu entry", g.menu_i["title"] == before + 1, g.menu_i["title"])
    g.up_title()
    check("holding does not immediately repeat", g.menu_i["title"] == before + 1)

    sv = ns["new_save"]("warrior")
    g.start_session(sv, ap)
    buttons(b_raw, {9}); g.state_name = "play"; g.true_end_delay = 0; g.dying = 0
    g.update(); buttons(b_raw, set())
    check("late join uses the second controller", g.state_name == "class" and g.cs_pad is bp)
    buttons(b_raw, {0}); g.update(); buttons(b_raw, set()); g.update()
    check("P2 stays on the physical pad", len(g.players) == 2 and g.players[1].pad is bp)
    sdl.SDL_JoystickDetachVirtual(b_idx); g.update()
    check("disconnect does not bind the keyboard", len(g.players) == 1 and g.players[0].pad is ap)
    b_idx, b_raw = attach(1); g.update()
    bp = next(p for p in g.pads.values() if p.kind == "gc" and p is not ap and p.id != ap.id)
    buttons(b_raw, {9}); g.update(); buttons(b_raw, set())
    check("reconnect can join again", g.state_name == "class" and g.cs_pad is bp)

    # Cutscene ignores an X that is already held, then accepts a later press.
    fight = ns["new_save"]("warrior"); fight["bosses"] = ["hiisi", "turso", "tytti"]
    g.start_session(fight, ap)
    buttons(a_raw, {0}); pump()
    g.start_ending()
    g.end_t = 80
    g.up_ending()
    check("held X does not skip the ending", g.end_page == 0 and g.state_name == "ending", g.end_page)
    buttons(a_raw, set()); pump(); g.up_ending()
    buttons(a_raw, {0}); pump()
    g.end_t = 50
    g.up_ending()
    check("a released-then-pressed X advances one page", g.end_page == 1, g.end_page)
    buttons(a_raw, set()); pump()

    # Louhi scare stays on screen instead of jumping straight to black.
    g.state_name = "interrupt"; g.interrupt_t = 40; g._arm_cut()
    g.dr_interrupt()
    pygame.image.save(g.canvas, str(OUT / "louhi_cutscene.png"))
    check("jumpscare is still drawing at frame 40", g.canvas.get_at((160, 90)) != (0, 0, 0, 255))

    # Gate and old save.
    stale = ns["new_save"]("sage")
    stale["vellamo_unlocked"] = True
    stale["bosses"] = ["hiisi"]
    clean = ns["sanitize_save"](stale, set(ns["BONFIRES"]))
    check("stale unlock without Louhi does not open the realm", clean["vellamo_unlocked"] is False)
    legacy = ns["new_save"]("sage")
    legacy["bosses"] = ["louhi"]; legacy["done"] = True; legacy["louhi_unlocked"] = True
    legacy["stats"]["vit"] = 4
    legacy = ns["sanitize_save"](legacy, set(ns["BONFIRES"]))
    check("Louhi save still unlocks", legacy["vellamo_unlocked"] is True and legacy["vellamo_visited"] is False)
    g.start_session(ns["new_save"]("warrior"), ap)
    check("gate hidden before Louhi", "vellamo_gate" not in {k for *_, k, i in g.interactables()})
    g.save["bosses"].append("louhi"); g.save["vellamo_unlocked"] = True
    check("gate appears after Louhi", "vellamo_gate" in {k for *_, k, i in g.interactables()})

    # Bosses are inside the camera for every water fight.
    shots = []
    for key in ("joukahainen", "ahti", "aino", "vellamo"):
        g.start_boss(key)
        for phase, pose in ((1, "idle"), (2, "windup"), (3, "attack")):
            g.boss.phase = phase
            g.boss.vb = pose
            g.players[0].x = max(g.boss.L + 20, g.boss.x - 90)
            g.players[0].face = 1
            for _ in range(6):
                g.update_camera()
            sx = g.boss.x - g.cam[0]
            px = g.players[0].x - g.cam[0]
            shots.append((key, phase, round(sx, 1), round(px, 1)))
            if phase == 1:
                g.draw_world(g.canvas, phase)
                pygame.image.save(g.canvas, str(OUT / f"boss_{key}.png"))
        g.reset_boss()
    R["boss_screen_x"] = shots
    check("bosses stay on screen in every phase while the player moves",
          all(20 < sx < ns["W"] - 20 and 12 < px < ns["W"] - 12 for _, _, sx, px in shots), shots)

    # Shore is traversable for a quiet stretch.
    shore = ns["new_save"]("warrior")
    shore["bonfire"] = "b10"; shore["seen"] = ["b10"]; shore["bosses"] = ["louhi"]; shore["vellamo_unlocked"] = True
    g.start_session(shore, ap)
    x0 = g.players[0].x
    seen_areas = set()
    samples = []
    goal = x0 + 220
    for i in range(5200):
        blocked = g.players[0].wall or (i > 20 and g.players[0].x < x0 + i * 0.15 and g.players[0].on_ground)
        buttons(a_raw, {0} if blocked and i % 18 == 0 else set())
        sdl.SDL_JoystickSetVirtualAxis(a_raw, 0, 28000)
        g.state_name = "play"; g.true_end_delay = 0; g.dying = 0
        g.players[0].inv = 999
        t0 = time.perf_counter()
        g.update(); g.draw()
        samples.append((time.perf_counter() - t0) * 1000.0)
        seen_areas.add(g.area)
        x0 = min(x0, g.players[0].x)
        if g.players[0].x >= goal and g.players[0].alive():
            break
    sdl.SDL_JoystickSetVirtualAxis(a_raw, 0, 0)
    samples.sort()
    def pct(p):
        return round(samples[min(len(samples) - 1, int(round((len(samples) - 1) * p)))], 2)
    R["traversal"] = {"frames": len(samples), "x": round(g.players[0].x, 1), "goal": goal,
                      "areas": sorted(seen_areas), "alive": g.players[0].alive(),
                      "p99": pct(0.99), "worst": round(samples[-1], 2)}
    print("TRAVERSAL", R["traversal"], flush=True)
    check("real loop stays alive and moves along the shore", g.players[0].alive() and g.players[0].x >= goal, R["traversal"])
    check("the walk is on the Vellamo shore", "ranta" in seen_areas, sorted(seen_areas))
    g.players[0].inv = 0
    g.players[0].die()
    for _ in range(220):
        g.update()
        if g.dying == 0 and g.players[0].hp > 0:
            break
    home = ns["bonfire_pos"](g.save["bonfire"])
    check("death respawns at the current bonfire", abs(g.players[0].x - home[0]) < 80, (round(g.players[0].x, 1), g.save["bonfire"]))
    g.draw(); pygame.image.save(g.canvas, str(OUT / "shore.png"))

    names = {}
    for i in range(14):
        bid = "b%d" % i
        g.save["bonfire"] = bid
        g.state_name = "bonfire"; g.menu_i["bonfire"] = 0
        got = []
        orig = g.text
        def cap(t, x, y, *a, **k):
            got.append(str(t)); return orig(t, x, y, *a, **k)
        g.text = cap; g.dr_bonfire(); g.text = orig
        names[bid] = got
        ap.prev = ap.blank(); c = ap.blank(); c["jump"] = True; ap.cur = c
        g.up_bonfire()
        if g.state_name != "play":
            check("bonfire %s leave" % bid, False, g.state_name)
            break
    else:
        check("all bonfire menus draw and leave", all(any(len(t) > 3 for t in names[f"b{i}"]) for i in range(14)))
    R["bonfires"] = {k: v[2] if len(v) > 2 else v[:1] for k, v in names.items()}
    if "b13" in names:
        g.save["bonfire"] = "b13"; g.state_name = "bonfire"; g.dr_bonfire()
        pygame.image.save(g.canvas, str(OUT / "bonfire_b13.png"))

    # NG+ keeps the character and resets the world.
    hero = ns["new_save"]("hunter")
    hero["stats"]["str"] = 6
    hero["souls"] = 2500
    hero["taken"] = ["c_moss"]
    hero["p2"] = {"cls": "sage", "level": 4, "stats": {"vit": 1, "end": 1, "str": 1, "foc": 0}, "souls": 40}
    hero["bosses"] = ["vellamo", "louhi", "aino"]
    hero["vellamo_done"] = True
    hero["ng_ready"] = True
    hero["done"] = True
    hero = ns["sanitize_save"](hero, set(ns["BONFIRES"]))
    g.title_save = hero
    g.state_name = "title"
    keys = [k for k, _ in g.title_items()]
    check("menu offers credits and NG+", "info" in keys and "ng" in keys, keys)
    g.begin_ng(hero)
    if g.state_name == "loading":
        g.up_loading()
    check("NG+ keeps level and gear", g.save["stats"]["str"] == 6 and "c_moss" in g.save["taken"] and g.save["souls"] == 2500 and g.save["p2"]["cls"] == "sage" and g.save["p2"]["stats"]["vit"] == 1)
    check("NG+ resets bosses and raises the cycle", g.save["bosses"] == [] and g.save["ng"] == 1 and g.save["vellamo_unlocked"] is False)

    taken = list(g.save["taken"])
    ns["SETTINGS"]["test_weapon"] = True
    g.players[0].recalc()
    g.state_name = "play"; g.draw()
    pygame.image.save(g.canvas, str(OUT / "test_weapon.png"))
    ns["SETTINGS"]["test_weapon"] = False
    g.players[0].recalc()
    check("test weapon is not written into equipment", g.save["taken"] == taken and g.players[0].dmgm < 10)

    samples = []
    g.state_name = "play"; g.true_end_delay = 0
    for _ in range(30):
        t0 = time.perf_counter(); g.update(); g.draw(); samples.append((time.perf_counter() - t0) * 1000)
    samples.sort()
    R["perf_ms"] = {"min": round(samples[0], 2), "median": round(samples[len(samples)//2], 2), "max": round(samples[-1], 2),
                    "note": "Dummy video. Frame time, not input latency, not a Pi or a physical pad."}
    print("PERF", R["perf_ms"])
    g.running = False
    json.dump(R, open(OUT / "report.json", "w"), indent=2, default=str)
    bad = [c["name"] for c in R["checks"] if not c["ok"]]
    print("FAILED", bad)
    if bad:
        raise SystemExit(1)

globs = {"__name__": "__main__", "__file__": str(REAL), "PROBE": PROBE}
try:
    exec(compile(src2, str(REAL), "exec"), globs)
except SystemExit:
    raise
except Exception:
    traceback.print_exc()
    raise
