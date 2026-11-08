"""v1.1 co-op safe spawn: join, leash-teleport, respawn and boss-carry never place a player inside a wall/hazard."""
from lib import *
fails = []
def ok(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c: fails.append(m)

def inside(g, p):
    """True if the player's AABB overlaps a solid above the feet row."""
    hw = p.w / 2.0; top = int((p.y - p.h + 0.5) // 16); bot = int((p.y - 1.0) // 16)
    for ty in range(top, bot + 1):
        for tx in range(int((p.x - hw + 0.5) // 16), int((p.x + hw - 0.5) // 16) + 1):
            if g.wd.solid(tx, ty): return True
    return False

def hazard(g, p):
    return G["hazard_at"](g.wd, p)

g = new_game(); pad = start(g, "warrior", "b2"); step(g, 10)
p2 = ScriptPad("p2"); g.add_pad(p2)

# many join positions: walk P1 across the forest and join at each
bad_join = []
for tx in range(10, 140, 3):
    p = g.players[0]
    y = G["floor_row"](tx, 18) * 16
    p.spawn(tx * 16 + 8, y); p.face = 1; p.on_ground = True; p.safe = (p.x, p.y); g.snap_cam(); g.sep_t = 0
    if len(g.players) > 1: g.remove_p2()
    g.add_p2("hunter", p2); q = g.players[1]; step(g, 2)
    if inside(g, q) or hazard(g, q) or not g.standing_free(q.x, q.y):
        bad_join.append((tx, round(q.x), round(q.y), inside(g, q), hazard(g, q)))
ok(len(bad_join) == 0, "join spawn safe across forest (%d bad: %s)" % (len(bad_join), bad_join[:3]))

# leash teleport into cramped spots
bad_leash = []
spots = [(76, G["floor_row"](76, 18)), (118, G["floor_row"](118, 18)), (40, G["floor_row"](40, 18)),
         (200, G["floor_row"](200, 22)), (250, G["floor_row"](250, 22)), (310, G["floor_row"](310, 20)),
         (380, G["floor_row"](380, 20)), (430, G["floor_row"](430, 8))]
if len(g.players) < 2: g.add_p2("sage", p2)
for tx, ty in spots:
    a, b = g.players
    a.spawn(tx * 16 + 8, ty * 16); a.face = 1; a.safe = (a.x, a.y); a.on_ground = True
    # put partner far away so leash fires
    b.spawn(a.x - 400, a.y); b.on_ground = True
    g.sep_t = 200; g.arena = None
    for _ in range(5): g.update_camera()
    if inside(g, b) or hazard(g, b) or not g.standing_free(b.x, b.y):
        bad_leash.append((tx, round(b.x), round(b.y)))
ok(len(bad_leash) == 0, "leash teleport safe (%d bad: %s)" % (len(bad_leash), bad_leash[:3]))

# respawn at every bonfire with 2 players
bad_resp = []
for bid in G["BONFIRES"]:
    g.save["bonfire"] = bid
    for p in g.players: p.hp = 0; p.state = "dead"
    g.dying = 180; g.respawn()
    for p in g.players:
        if inside(g, p) or hazard(g, p) or not g.standing_free(p.x, p.y):
            bad_resp.append((bid, p.idx, round(p.x), round(p.y)))
ok(len(bad_resp) == 0, "bonfire respawn safe for 2p (%d bad: %s)" % (len(bad_resp), bad_resp[:3]))

# boss-door carry-in
bad_boss = []
for key in ("hiisi", "turso", "tytti"):
    a = G["ARENAS"][key]
    for p in g.players:
        p.spawn((a["x0"] - 5) * 16, a["ground"] * 16); p.state = "free"; p.hp = p.maxhp
    g.start_boss(key)
    for p in g.players:
        if inside(g, p) or hazard(g, p):
            bad_boss.append((key, p.idx, round(p.x), round(p.y)))
    g.reset_boss(); g.boss = None; g.arena = None
ok(len(bad_boss) == 0, "boss carry-in safe (%d bad: %s)" % (len(bad_boss), bad_boss[:3]))

# find_safe_xy itself: ask for a point deep inside solid rock, must return a free spot
bx, by = G["bonfire_pos"]("b2")
# a known solid cell above the floor
sx, sy = g.find_safe_xy(bx, by - 48, fallback=(bx, by))
ok(g.standing_free(sx, sy) and not hazard(g, type("B", (), {"x": sx, "y": sy, "w": G["PW_"], "h": G["PH_"]})()),
   "find_safe_xy escapes interior solid -> (%.0f,%.0f)" % (sx, sy))

# random spray near each bonfire
bad_rand = []; rnd = __import__("random").Random(0)
for bid, tx in G["BONFIRES"].items():
    by = G["floor_row"](tx, G["BF_START"][bid]) * 16
    for _ in range(40):
        x = tx * 16 + rnd.randint(-80, 80); y = by + rnd.randint(-64, 32)
        sx, sy = g.find_safe_xy(x, y, face=rnd.choice([-1, 1]), fallback=(tx * 16, by))
        body = type("B", (), {"x": sx, "y": sy, "w": G["PW_"], "h": G["PH_"]})()
        if not g.standing_free(sx, sy) or G["hazard_at"](g.wd, body):
            bad_rand.append((bid, round(x), round(y), round(sx), round(sy)))
ok(len(bad_rand) == 0, "find_safe_xy spray at bonfires (%d bad: %s)" % (len(bad_rand), bad_rand[:3]))

# camera edge pin must not shove anyone into a wall
g3 = new_game(); pad3 = start(g3, "warrior", "b4"); p2b = ScriptPad("c2"); g3.add_pad(p2b); g3.add_p2("sage", p2b)
a, b = g3.players
# place both well left of the camera so the pin fires
a.spawn(g3.cam[0] - 80, a.y); b.spawn(g3.cam[0] - 60, b.y); a.safe = (a.x, a.y); b.safe = (b.x, b.y)
for _ in range(10): g3.update_camera()
ok(not inside(g3, a) and not inside(g3, b) and g3.standing_free(a.x, a.y) and g3.standing_free(b.x, b.y),
   "camera pin stays in free space (a=%.0f,%.0f b=%.0f,%.0f)" % (a.x, a.y, b.x, b.y))
print("spawn:", "OK" if not fails else "FAIL %s" % fails)
sys.exit(1 if fails else 0)
