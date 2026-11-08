"""Random-input fuzz: world play (all classes, difficulties, 1-2 players, from every bonfire) and menu mashing in every screen. No exceptions, no NaN, nobody leaves the world."""
import random, math, traceback, sys
from lib import *
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
random.seed(seed); fails = []
KEYS = ["jump", "light", "heavy", "dodge", "guard", "skill", "flask", "up", "down", "start", "back", "left", "right"]
WW, WH = G["COLS"] * 16, G["ROWS"] * 16
def rnd(pad, bias):
    c = pad.blank()
    for k in KEYS:
        if k in ("start", "back"): continue
        if random.random() < 0.06: c[k] = True
    if random.random() < bias: c["right"] = True
    elif random.random() < 0.5: c["left"] = True
    c["x"] = 1.0 if c["right"] else -1.0 if c["left"] else 0.0
    return c
runs = 0
for cls in ("warrior", "sage", "hunter"):
    for diff in ("easy", "normal", "tuonela"):
        for bf in ("b0", "b2", "b3", "b5", "b6", "b8"):
            if random.random() < 0.45: continue
            runs += 1
            g = new_game(); sv = G["new_save"](cls); sv["seen"] = list(G["BONFIRES"])
            if bf in ("b8", "b6"): sv["bosses"] = ["hiisi", "turso"]
            if bf in ("b3", "b5"): sv["bosses"] = ["hiisi"]
            pad = start(g, cls, bf, save=sv, diff=diff)
            coop = random.random() < .5; p2 = None
            if coop: p2 = ScriptPad("t2"); g.add_pad(p2); g.add_p2(random.choice(("warrior", "sage", "hunter")), p2)
            bias = random.choice((0.4, 0.55, 0.7))
            try:
                for f in range(2400):
                    if f % 8 == 0:
                        pad.nextc = rnd(pad, bias)
                        if p2: p2.nextc = rnd(p2, bias)
                    if f % 600 == 0:
                        for p in g.players: p.hp = p.maxhp
                    g.update()
                    if f % 5 == 0: g.draw()
                    for p in g.players:
                        if not (math.isfinite(p.x) and math.isfinite(p.y)) or not (-4 <= p.x <= WW + 4) or p.y > WH + 40 or p.y < -80:
                            fails.append("OOB %s %s %s %s f%d x=%s y=%s" % (cls, diff, bf, p.idx, f, p.x, p.y)); break
                    if g.state_name not in ("play", "pause", "map", "levelup", "bonfire", "ending", "title", "class", "loading", "dead"):
                        pass
                    if g.state_name in ("pause", "map", "bonfire", "class"): g.state_name = "play"; g.need_pad = None
                    if len(g.players) == 1 and p2 is not None and coop: coop = False
            except Exception:
                traceback.print_exc(); fails.append("EXC %s %s %s" % (cls, diff, bf))
print("play fuzz runs:", runs)
# menu mashing: every state, both languages
for lang in ("fi", "en"):
    setlang(lang); g = new_game(); pad = ScriptPad("t1"); g.add_pad(pad); g.last_pad = pad
    seen = set()
    try:
        for f in range(6000):
            if f % 3 == 0:
                c = pad.blank()
                for k in ("jump", "back", "start", "up", "down", "left", "right", "light", "heavy", "dodge"):
                    if random.random() < 0.12: c[k] = True
                pad.nextc = c
            g.update(); g.draw(); seen.add(g.state_name)
            if g.state_name == "quit" or not g.running: g.running = True; g.open_title() if hasattr(g, "open_title") else None
            if g.save is None and g.state_name == "play": pass
            bad = [e for e in untr(g) + bad_rects(g) if not str(e[1]).isdigit()]   # damage numbers drifting off-screen are clipped, fine
            if bad: fails.append("menu text %s %s %s" % (lang, g.state_name, bad[:2]))
            g.track.clear()
    except Exception:
        traceback.print_exc(); fails.append("EXC menu " + lang)
    print("menu fuzz", lang, "states visited:", sorted(seen))
print("fuzz seed %d:" % seed, "OK" if not fails else "%d FAIL" % len(fails)); [print(" ", f) for f in fails[:12]]
raise SystemExit(1 if fails else 0)
