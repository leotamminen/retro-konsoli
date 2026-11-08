"""Frame-time budget: update+draw with 2 players and many enemies, in every area and during boss fights. Prints avg / p99 / max in ms."""
import time, random
from lib import *
random.seed(3)
def run(name, bf, boss=None, frames=360, diff="normal"):
    g = new_game(); p1 = start(g, "warrior", bf, diff=diff); p2 = ScriptPad("t2"); g.add_pad(p2); g.add_p2("hunter", p2)
    if boss: g.start_boss(boss)
    # crowd: wake every enemy within a screen of the players
    for e in g.enemies:
        e.awake = True if hasattr(e, "awake") else None
    ts = []
    for f in range(frames):
        c = p1.blank(); c["right"] = (f // 90) % 2 == 0; c["left"] = not c["right"]; c["x"] = 1.0 if c["right"] else -1.0
        c["light"] = f % 20 < 2; c["jump"] = f % 70 == 0; p1.nextc = c
        d = p2.blank(); d["right"] = True; d["x"] = 1.0; d["skill"] = f % 50 < 30; p2.nextc = d
        for p in g.players: p.hp = p.maxhp
        t = time.perf_counter(); g.update(); g.draw(); ts.append((time.perf_counter() - t) * 1000)
    ts.sort(); n = len(ts)
    print("%-22s avg %.2f  p99 %.2f  max %.2f ms  (enemies %d, projs %d, parts %d)" % (name, sum(ts) / n, ts[int(n * .99)], ts[-1], len(g.enemies), len(g.projs), len(g.parts.p) if hasattr(g.parts, "p") else -1))
    return ts[int(n * .99)], sum(ts) / n
worst = 0
for nm, bf, b in (("forest", "b1", None), ("swamp", "b4", None), ("river", "b7", None), ("hiisi", "b2", "hiisi"), ("turso", "b5", "turso"), ("tytti", "b8", "tytti")):
    p99, avg = run(nm, bf, b); worst = max(worst, avg)
# stress: drag 20 enemies along with the players, particles + shake on
G["SETTINGS"]["shake"] = True
for diff in ("normal", "tuonela"):
    g = new_game(); p1 = start(g, "sage", "b4", diff=diff); p2 = ScriptPad("t2"); g.add_pad(p2); g.add_p2("warrior", p2)
    ens = [e for e in g.enemies if not getattr(e, "boss", False)][:20]
    ts = []
    for f in range(480):
        for i, e in enumerate(ens):
            if f % 60 == 0 and not e.dead:
                e.x = g.players[0].x + (i - 10) * 14; e.y = g.players[0].y - 2; e.vx = e.vy = 0
        for p in g.players: p.hp = p.maxhp; p.stam = p.maxst
        c = p1.blank(); c["light"] = f % 12 < 2; c["heavy"] = f % 50 == 30; p1.nextc = c
        d = p2.blank(); d["light"] = f % 14 < 2; p2.nextc = d
        t = time.perf_counter(); g.update(); g.draw(); ts.append((time.perf_counter() - t) * 1000)
    ts.sort(); n = len(ts)
    print("stress 20 enemies %-8s avg %.2f  p99 %.2f  max %.2f ms" % (diff, sum(ts) / n, ts[int(n * .99)], ts[-1]))
    worst = max(worst, sum(ts) / n)
print("budget: 16.7 ms/frame. On a Pi 5 expect roughly 4-6x these desktop numbers (unverified)")
raise SystemExit(0 if worst < 5 else 1)
