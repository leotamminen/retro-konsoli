"""Boss harness: an (invulnerable) bot fights each boss with each class; checks attack patterns run without exceptions,
phase 2 triggers, the boss dies, doors open and the ending starts."""
import random, traceback
from lib import *
res = []
def bot_frame(g, pad, p, boss, t):
    c = pad.blank(); dx = boss.x - p.x
    if getattr(boss, "key", "") == "turso": tx = boss.x   # head only comes down in its opening
    can = (not boss.invuln) and (not boss.hidden) and (boss.key != "turso" or boss.y > boss.gy - 60)
    keep = {"warrior": 20, "sage": 70, "hunter": 60}[p.cls]
    c["x"] = 1.0 if dx > keep + 10 else -1.0 if dx < -(keep + 10) else 0.0
    if boss.key == "turso" and not can: c["x"] = 0.0
    c["right"] = c["x"] > 0.5; c["left"] = c["x"] < -0.5
    reach = {"warrior": 36, "sage": 140, "hunter": 110}[p.cls]
    if can and abs(dx) < reach:
        ph = t % 40
        if p.cls == "hunter":
            if ph < 32: c["skill"] = True
        elif ph < 2: c["light"] = True
        elif ph == 20 and p.cls == "warrior": c["heavy"] = True
    if t % 97 == 0: c["jump"] = True
    pad.nextc = c
for key, bf in (("hiisi", "b2"), ("turso", "b5"), ("tytti", "b8")):
    for cls in ("warrior", "sage", "hunter"):
        for ncoop in (1, 2):
            g = new_game(); sv = G["new_save"](cls); sv["bonfire"] = bf
            pad = ScriptPad("t1"); g.add_pad(pad); g.last_pad = pad
            sv["bosses"] = [b for b in ("hiisi", "turso") if b != key and list(G["ARENAS"]).index(b) < list(G["ARENAS"]).index(key)]
            try:
                g.start_session(sv, pad)
                if ncoop == 2:
                    p2 = ScriptPad("t2"); g.add_pad(p2); g.add_p2("hunter", p2)
                a = G["ARENAS"][key]
                for p in g.players: p.spawn((a["x0"] + 4) * 16, a["ground"] * 16)
                phases = set(); t = 0; done = False; seen = False; cheat = None
                while t < 60 * 200:
                    t += 1
                    for p in g.players:
                        p.hp = p.maxhp; p.stam = p.maxst
                        if p.cls == "sage": p.focus = p.maxfoc
                    if g.boss is not None and not g.boss.dead:
                        bot_frame(g, pad, g.players[0], g.boss, t)
                        if ncoop == 2:
                            q = p2.blank(); q["x"] = 1.0 if g.boss.x > g.players[1].x else -1.0
                            if t % 30 < 2: q["light"] = True
                            p2.nextc = q
                        phases.add(getattr(g.boss, "phase", 0)); seen = True
                        if t > 5400 and cheat is None: cheat = t
                        if cheat and g.boss.hp > 30: g.boss.hp = 30
                    else:
                        pad.nextc = None
                    step(g, 1, draw=(t % 7 == 0))
                    if seen and (g.boss is None or g.boss.dead) and g.state_name == 'play' and key != 'tytti' and t > 0: done = True; break
                    if g.state_name == "ending": done = True; break
                od = key == "tytti" or not G["ARENAS"][key]["door_out"] or g.wd.opened("d_%s_out" % key)
                res.append((key, cls, ncoop, done, 'ttk=%ds' % (t // 60), 'CHEATED' if cheat else 'honest', round(g.boss.hp) if g.boss else None, sorted(phases), "door_out_open" if od else "DOOR CLOSED", g.state_name))
            except Exception:
                traceback.print_exc(); res.append((key, cls, ncoop, "EXC"))
for r in res: print(r)
