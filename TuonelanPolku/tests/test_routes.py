"""Physics reachability of the built release. Loads the pygame file, does not teleport."""
import hashlib
from pathlib import Path
from lib import *
OLD = {
    "TuonelanPolku1.3.3.pygame": "a45e64ef4f6719488ff7296edceaec3ff37a341986fe57d3d75666fd00e192cc",
    "TuonelanPolku1.3.2.pygame": "0c11d1f41f1336ced887763bcf3d3e8d4648955929813c48be4ddb9dbbf7c09a",
    "TuonelanPolku1.2.pygame": "9fb3ee86127ece8d26e66e3c0817bf4476f5e537b222a22a251a4887f1169622",
    "TuonelanPolku1.3.1.pygame": "0af9d21b03899c5c01de5fc22192ea045c1aa71bf2a43b3a162443c86e9cce55",
    "TuonelanPolku1.3.pygame": "e2dfc11f0ef80874cb5311a31617de6e567f79c1a60435e8081c662680c16956",
}
root = Path(__file__).resolve().parents[1]
for name, expect in OLD.items():
    digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if digest != expect:
        raise SystemExit("old file changed: %s %s" % (name, digest))
print("old releases unchanged")
import collections, time
TILE = G["TILE"]; ROWS = G["ROWS"]; COLS = G["COLS"]
walk_step = G["walk_step"]; Body = G["Body"]; hazard_at = G["hazard_at"]; World = G["World"]
wd = World()
wd.set_open("d_vellamo", True)
for key in ("joukahainen", "ahti", "aino", "vellamo"):
    if "d_%s_in" % key in G["DYN"]:
        wd.set_open("d_%s_in" % key, True)

def key(x, y):
    return (int(x // 8), int(round(y / TILE)))

def sim_jump(x, y, dire, hold, steer):
    b = Body(x, y); b.on_ground = True; b.coyote = 6
    for f in range(90):
        ix = dire if f < steer else 0
        ev = walk_step(wd, b, ix, 0, f == 0, f < hold, False)
        if hazard_at(wd, b) or b.y > ROWS * TILE:
            return None
        if b.on_ground and f > 2:
            return (b.x, b.y)
    return None

def expand(x, y):
    out = []
    for d in (-1, 1):
        b = Body(x, y); b.on_ground = True; b.coyote = 6
        k0 = key(x, y)
        for f in range(50):
            walk_step(wd, b, d, 0, False, False, False)
            if hazard_at(wd, b) or b.y > ROWS * TILE:
                break
            if b.on_ground and key(b.x, b.y) != k0:
                out.append((b.x, b.y)); break
            if b.wall and b.on_ground:
                break
    for d in (-1, 0, 1):
        for hold, steer in ((99, 99), (10, 16)):
            if d == 0 and hold != 99:
                continue
            r = sim_jump(x, y, d, hold, steer)
            if r:
                out.append(r)
    b = Body(x, y); b.on_ground = True
    for f in range(80):
        walk_step(wd, b, 0, -1, False, False, False)
        if not b.climb and f > 4:
            break
        if b.climb and f % 8 == 0:
            out.append((b.x, b.y))
    return out

def bfs(seeds):
    seen = {}
    q = collections.deque()
    for s in seeds:
        k = key(*s)
        if k not in seen:
            seen[k] = s; q.append(s)
    while q:
        x, y = q.popleft()
        if x < 470 * TILE:
            continue
        for r in expand(x, y):
            k = key(*r)
            if k not in seen:
                seen[k] = r; q.append(r)
    return seen

def near(vis, tx, ty, rad=1.6):
    for x, y in vis.values():
        if abs(x - (tx * TILE + 8)) <= TILE * rad and abs(int(round(y / TILE)) - ty) <= 2:
            return True
    return False

t0 = time.time()
bx, by = G["bonfire_pos"]("b10")
vis = bfs([(bx, by)])
print("nodes", len(vis), "seconds", round(time.time() - t0, 1))
fail = []
for bid, tx in G["BONFIRES"].items():
    if int(bid[1:]) < 10:
        continue
    ty = G["floor_row"](tx, 0)
    if not near(vis, tx, ty):
        fail.append(bid)
for name, arena in G["ARENAS"].items():
    if name not in ("joukahainen", "ahti", "aino", "vellamo"):
        continue
    tx = arena["x0"] + 5
    ty = arena["ground"]
    if not near(vis, tx, ty):
        fail.append(name)
last = G["COLS"] - 3
if not near(vis, last, G["floor_row"](last, 0)):
    fail.append("last-column")
print("FAIL", fail if fail else "none")
if fail:
    raise SystemExit(1)
print("OK routes")
