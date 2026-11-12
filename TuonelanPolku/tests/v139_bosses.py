"""1.3.9 water bosses: wide arenas, pursuit, and a dodge for every telegraphed move."""
from lib import *
import collections
import os
import pygame

FAIL = []
ACTS = {
    "joukahainen": ["verse", "bog", "leap", "frost"],
    "ahti": ["dive", "charge", "geyser", "current"],
    "aino": ["arc", "drop", "stream", "frost"],
    "vellamo": ["lattice", "crown", "cage", "cross"],
}
SHOT = {"joukahainen": "verse", "ahti": "dive", "aino": "arc", "vellamo": "lattice"}
ART = "/opt/cursor/artifacts"


def ok(value, msg):
    print(("ok   " if value else "FAIL ") + msg)
    if not value:
        FAIL.append(msg)


def fresh(bf):
    g = new_game()
    sv = G["new_save"]("warrior")
    sv.update(vellamo_unlocked=True, bonfire=bf)
    SETTINGS["difficulty"] = "normal"
    pad = start(g, save=sv, bonfire=bf, diff="normal")
    return g, pad


def place(p, x, y):
    p.x = float(x)
    p.y = float(y)
    p.vx = p.vy = 0.0
    p.state = "free"
    p.st_t = 0
    p.stun = 0
    p.inv = 0
    p.hp = p.maxhp
    p.on_ground = True
    p.climb = False
    p.atk = None
    p.act = None


def smart(pad, g, p):
    c = pad.blank()
    boss = g.boss
    zones = [z for z in g.zones if z.dmg > 0 or z.style in ("rock", "geyser", "frost", "tidepike", "cage", "bog")]
    inside = [z for z in zones if abs(p.x - z.x) < z.w / 2 + 8 and p.y > z.y - z.h - 6]
    if inside:
        best = None
        for dx in range(-96, 97, 8):
            x = p.x + dx
            if any(abs(x - z.x) < z.w / 2 + 10 for z in zones):
                continue
            if best is None or abs(dx) < abs(best):
                best = dx
        if best:
            c["x"] = 1 if best > 0 else -1
    low = any(pr.enemy and abs(pr.x - p.x) < 72 and pr.y > p.y - 40 for pr in g.projs)
    rushing = boss.atk and abs(boss.x - p.x) < 72 and boss.y > p.y - 8
    if low or rushing:
        c["jump"] = True
    if c["x"]:
        c["left"] = c["x"] < 0
        c["right"] = c["x"] > 0
    pad.nextc = c


def trial(g, pad, act, x, y, mode):
    b = g.boss
    a = b.arena
    p = g.players[0]
    g.dying = 0
    g.state_name = "play"
    g.projs = []
    g.zones = []
    b.phase = 2
    b.hp = b.maxhp
    b.dead = False
    b.invuln = False
    b.stun = 0
    b.hold = False
    b.flow = 0
    b.atk = None
    b.armor = True
    b.vx = b.vy = 0
    b.x = (a["x0"] + a["x1"]) * 0.5 * G["TILE"]
    b.y = a["ground"] * G["TILE"]
    b.warn = 0
    place(p, x, y)
    b.gen = b.perform(act)
    for _ in range(170):
        if mode == "smart":
            smart(pad, g, p)
        elif mode == "still":
            pad.nextc = pad.blank()
        elif mode == "jump":
            c = pad.blank()
            c["jump"] = True
            pad.nextc = c
        elif mode == "away":
            c = pad.blank()
            c["x"] = -1 if p.x >= b.x else 1
            c["left"] = c["x"] < 0
            c["right"] = c["x"] > 0
            pad.nextc = c
        step(g, 1, False)
        if p.hp < p.maxhp - 0.1 or p.state in ("dead", "down"):
            pad.nextc = None
            return False
        if g.dying:
            pad.nextc = None
            return False
    pad.nextc = None
    return p.hp >= p.maxhp - 0.1 and p.state not in ("dead", "down")


def platforms(g, key):
    a = G["ARENAS"][key]
    found = []
    wd = g.wd
    for y in range(a["y0"], a["ground"]):
        x = a["x0"] + 1
        while x < a["x1"]:
            if wd.tile(x, y) == G["PLAT"]:
                x0 = x
                while x < a["x1"] and wd.tile(x, y) == G["PLAT"]:
                    x += 1
                found.append((x0, y, x - x0))
            else:
                x += 1
    return found


def dodge_all(g, pad, key):
    a = G["ARENAS"][key]
    tile = G["TILE"]
    floor_y = a["ground"] * tile
    spots = [
        ((a["x0"] + 4) * tile, floor_y, "left"),
        ((a["x0"] + a["x1"]) * 0.5 * tile, floor_y, "mid"),
        ((a["x1"] - 4) * tile, floor_y, "right"),
    ]
    for x, y, w in platforms(g, key):
        spots.append(((x + w * 0.5) * tile, y * tile, "plat%d" % y))
    for act in ACTS[key]:
        won = None
        for x, y, name in spots:
            for mode in ("smart", "still", "jump", "away"):
                if trial(g, pad, act, x, y, mode):
                    won = "%s@%s" % (mode, name)
                    break
            if won:
                break
        ok(won is not None, "%s %s dodgeable (%s)" % (key, act, won or "none"))


def movement(g, pad):
    b = g.boss
    p = g.players[0]
    a = b.arena
    g.dying = 0
    g.state_name = "play"
    p.hp = p.maxhp
    p.inv = 9999
    p.state = "free"
    place(p, (a["x0"] + 5) * G["TILE"], a["ground"] * G["TILE"])
    p.inv = 9999
    b.phase = 1
    b.hp = b.maxhp
    b.dead = False
    b.gen = None
    b.stun = 0
    b.hold = False
    b.engaged = True
    xs = []
    for i in range(420):
        # Keep a target on the floor and step aside so pursuit has somewhere to go.
        if i % 140 == 0:
            place(p, (a["x0"] + (6 if (i // 140) % 2 == 0 else 20)) * G["TILE"], a["ground"] * G["TILE"])
            p.inv = 9999
        pad.nextc = pad.blank()
        step(g, 1, False)
        xs.append(b.x)
    span = max(xs) - min(xs)
    ok(span > 48, "%s moves (%.0f px)" % (b.key, span))
    return span


def traverse(key):
    tile = G["TILE"]
    wd = G["World"]()
    for door in ("d_%s_in" % key, "d_%s_out" % key):
        if door in G["DYN"]:
            wd.set_open(door, False)
    a = G["ARENAS"][key]
    Body = G["Body"]
    walk_step = G["walk_step"]
    hazard_at = G["hazard_at"]

    def sim_jump(x, y, dire, hold, steer):
        b = Body(x, y)
        b.on_ground = True
        b.coyote = 6
        for f in range(90):
            ix = dire if f < steer else 0
            walk_step(wd, b, ix, 0, f == 0, f < hold, False)
            if hazard_at(wd, b) or b.y > G["ROWS"] * tile:
                return None
            if b.on_ground and f > 2:
                rise = y - b.y
                drop = b.y - y
                if rise > 34 or drop > 120:
                    return None
                if not (a["x0"] * tile < b.x < a["x1"] * tile):
                    return None
                return (b.x, b.y)
        return None

    def expand(x, y):
        out = []
        for d in (-1, 1):
            b = Body(x, y)
            b.on_ground = True
            b.coyote = 6
            k0 = (int(x // 8), int(round(y / tile)))
            for f in range(40):
                walk_step(wd, b, d, 0, False, False, False)
                if hazard_at(wd, b) or b.y > G["ROWS"] * tile:
                    break
                if not (a["x0"] * tile < b.x < a["x1"] * tile):
                    break
                rise = y - b.y
                drop = b.y - y
                if rise > 34 or drop > 120:
                    break
                if b.on_ground and (int(b.x // 8), int(round(b.y / tile))) != k0:
                    out.append((b.x, b.y))
                    break
        for d in (-1, 0, 1):
            for hold, steer in ((99, 99), (12, 18)):
                if d == 0 and hold != 99:
                    continue
                r = sim_jump(x, y, d, hold, steer)
                if r:
                    out.append(r)
        return out

    seeds = [((a["x0"] + 3) * tile + 8, a["ground"] * tile)]
    seen = {}
    q = collections.deque()
    for s in seeds:
        k = (int(s[0] // 8), int(round(s[1] / tile)))
        seen[k] = s
        q.append(s)
    while q:
        x, y = q.popleft()
        for r in expand(x, y):
            k = (int(r[0] // 8), int(round(r[1] / tile)))
            if k not in seen:
                seen[k] = r
                q.append(r)

    def reached(tx, ty):
        for x, y in seen.values():
            if abs(x - (tx * tile + 8)) <= tile * 1.2 and abs(y - ty * tile) <= 2:
                return True
        return False

    floor_ok = reached(a["x0"] + 4, a["ground"]) and reached(a["x1"] - 3, a["ground"])
    ok(floor_ok, "%s floor crosses the closed arena" % key)
    missing = []
    for x in range(a["x0"] + 1, a["x1"]):
        for y in range(a["y0"], a["ground"]):
            if wd.tile(x, y) == G["PLAT"] and not reached(x, y):
                missing.append((x, y))
    ok(not missing, "%s platforms reachable at 2-tile rise (%s)" % (key, missing or "all"))
    # One jump from the floor itself cannot clear a 4-tile platform. The upper step is a second 2-tile hop.
    floor_y = a["ground"] * tile
    direct = 0
    for tx in range(a["x0"] + 2, a["x1"] - 1, 2):
        for dire, hold, steer in ((-1, 99, 99), (1, 99, 99), (0, 99, 99), (1, 12, 18)):
            b = Body((tx + 0.5) * tile, floor_y)
            b.on_ground = True
            b.coyote = 6
            landed = None
            for f in range(70):
                ix = dire if f < steer else 0
                walk_step(wd, b, ix, 0, f == 0, f < hold, False)
                if b.on_ground and f > 2:
                    landed = floor_y - b.y
                    break
            if landed:
                direct = max(direct, landed)
    ok(direct <= 34, "%s one jump from the floor rises %.0f px" % (key, direct))


def shoot(g, key):
    os.makedirs(ART, exist_ok=True)
    g.draw()
    img = pygame.transform.scale(g.canvas, (G["W"] * 3, G["H"] * 3))
    path = os.path.join(ART, "139_%s.png" % key)
    pygame.image.save(img, path)
    print("shot", path)


for key, bf in (("joukahainen", "b10"), ("ahti", "b11"), ("aino", "b12"), ("vellamo", "b13")):
    a = G["ARENAS"][key]
    ok(a["x1"] - a["x0"] == 28, "%s arena is 28 tiles" % key)
    g, pad = fresh(bf)
    g.start_boss(key)
    ok(g.wd.solid(a["x0"], a["ground"] - 2) and g.wd.solid(a["x1"], a["ground"] - 2), "%s both doors shut" % key)
    p = g.players[0]
    b = g.boss
    place(p, (a["x0"] + 4) * G["TILE"], a["ground"] * G["TILE"])
    b.x = (a["x0"] + 18) * G["TILE"]
    g.snap_cam()
    cx = g.cam[0]
    ok(cx - 4 <= p.x <= cx + G["W"] + 4 and cx - 4 <= b.x <= cx + G["W"] + 4, "%s camera holds player and boss" % key)
    want_y = max(0, min(G["ROWS"] * G["TILE"] - G["H"], a["ground"] * G["TILE"] + 8 - G["H"]))
    floor_screen = a["ground"] * G["TILE"] - g.cam[1]
    ok(abs(g.cam[1] - want_y) < 1 and 8 <= floor_screen <= G["H"] - 4, "%s camera keeps the floor on screen" % key)
    movement(g, pad)
    # Picture the fight once a telegraph is on screen.
    g.projs = []
    g.zones = []
    b.hold = False
    b.stun = 0
    b.atk = None
    b.phase = 1
    b.x = (a["x0"] + 14) * G["TILE"]
    b.y = a["ground"] * G["TILE"]
    b.gen = b.perform(SHOT[key])
    place(p, (a["x0"] + 8) * G["TILE"], a["ground"] * G["TILE"])
    p.inv = 999
    for _ in range(120):
        pad.nextc = pad.blank()
        step(g, 1, False)
        if g.projs or g.zones or b.atk:
            step(g, 4, False)
            break
    g.snap_cam()
    shoot(g, key)
    dodge_all(g, pad, key)
    traverse(key)

# The cage follows whoever is nearer. P2 is not a softer copy of P1.
g, pad = fresh("b13")
p2 = G["ScriptPad"]("p2")
g.add_pad(p2)
g.add_p2("warrior", p2)
g.start_boss("vellamo")
b = g.boss
g.players[0].x = b.x - 140
g.players[1].x = b.x + 24
g.players[1].y = b.gy
b.phase = 2
b.gen = b.perform("cage")
for _ in range(8):
    step(g, 1, False)
cages = [z for z in g.zones if z.style == "cage"]
ok(bool(cages) and abs(cages[0].x - g.players[1].x) < abs(cages[0].x - g.players[0].x), "cage picks the nearer player, P2 same rule as P1")

# Aino still calms.
g, pad = fresh("b12")
g.start_boss("aino")
g.boss.invuln = False
g.boss.hp = 1
g.boss.take(500)
ok(g.state_name == "aino_reveal", "Aino calms instead of dying")

# One phase only, including after the roar.
g, pad = fresh("b10")
g.start_boss("joukahainen")
g.boss.phase = 1
g.boss.hp = g.boss.maxhp * 0.5
g.boss.gen = None
g.boss.invuln = False
g.players[0].inv = 999
step(g, 80, False)
ok(g.boss.phase == 2, "half health ends on phase 2")
g.boss.hp = 1
g.boss.gen = None
step(g, 30, False)
ok(g.boss.phase == 2, "quarter health does not open another phase")

print("FAILURES", FAIL)
raise SystemExit(bool(FAIL))
