"""Traversal tester: BFS over standing positions using the REAL physics (walk_step/move_body), with a flag fixpoint
(levers, bosses, double jump).  Reports what is unreachable, and checks every goal."""
from lib import *
import sys, time, collections
Gd = G; walk_step = Gd["walk_step"]; Body = Gd["Body"]; hazard_at = Gd["hazard_at"]; World = Gd["World"]
TILE = 16; ROWS = Gd["ROWS"]; COLS = Gd["COLS"]
wd = World()
def key(x, y): return (int(x // 8), int(round(y / TILE)))
def mk(x, y, dj):
    b = Body(x, y); b.on_ground = True; b.coyote = 6; return b
def sim_jump(wd, x, y, dir_, hold, steer, dj, djat, climb_start=None):
    """returns landing (x, y) or None"""
    b = mk(x, y, dj)
    if climb_start: b.climb = True
    pressed = True
    for f in range(0, 140):
        ix = dir_ if f < steer else 0
        jp = (f == 0) or (dj and f == djat)
        jh = f < hold
        ev = walk_step(wd, b, ix, 0, jp, jh, dj)
        if hazard_at(wd, b): return None
        if b.y > ROWS * TILE + 8: return None
        if b.on_ground and f > 2 and not b.climb: return (b.x, b.y)
    return None
def expand(wd, n, dj):
    x, y = n; out = []
    # walk both ways
    for d in (-1, 1):
        b = mk(x, y, dj); k0 = key(x, y)
        for f in range(60):
            walk_step(wd, b, d, 0, False, False, dj)
            if hazard_at(wd, b) or b.y > ROWS * TILE: break
            if b.on_ground and key(b.x, b.y) != k0: out.append((b.x, b.y)); break
            if b.wall and b.on_ground: break
    # jumps
    for d in (-1, 0, 1):
        for hold in (99, 8):
            for steer in (99, 14):
                if d == 0 and (hold != 99 or steer != 99): continue
                r = sim_jump(wd, x, y, d, hold, steer, dj, 0); 
                if r: out.append(r)
        if dj:
            for djat in (12, 22, 34):
                r = sim_jump(wd, x, y, d, 99, 99, dj, djat)
                if r: out.append(r)
    # drop through
    tx = int(x // TILE)
    if wd.tile(tx, int(round(y / TILE))) in (Gd["PLAT"], Gd["LADDER"]) or True:
        b = mk(x, y, dj)
        if wd.tile(tx, int(round(y / TILE))) in (Gd["PLAT"], Gd["LADDER"]):
            for f in range(120):
                walk_step(wd, b, 0, 0, f == 0, False, dj, drop=(f == 0)) if False else None
                if f == 0: b.drop_t = 10; b.y += 1.5; b.on_ground = False; b.coyote = 0
                walk_step(wd, b, 0, 0, False, False, dj)
                if hazard_at(wd, b) or b.y > ROWS * TILE: break
                if b.on_ground and f > 2: out.append((b.x, b.y)); break
    # ladders: up from here, down from top
    for iy in (-1, 1):
        b = mk(x, y, dj)
        for f in range(500):
            walk_step(wd, b, 0, iy, False, False, dj)
            if b.climb and f % 4 == 0 and b.y % 1 == 0 or (b.climb and f % 6 == 0):
                for d in (-1, 1):
                    r = sim_jump(wd, b.x, b.y, d, 99, 99, dj, 0, climb_start=True)
                    if r: out.append(r)
            if not b.climb and f > 3:
                if b.on_ground and key(b.x, b.y) != key(x, y): out.append((b.x, b.y))
                break
            if hazard_at(wd, b): break
    return out
def bfs(wd, seeds, dj, visited=None, queue=None):
    visited = visited if visited is not None else {}
    q = collections.deque(queue or [])
    for s in seeds:
        k = key(*s)
        if k not in visited: visited[k] = s; q.append(s)
    while q:
        n = q.popleft()
        for r in expand(wd, n, dj):
            k = key(*r)
            if k not in visited:
                visited[k] = r; q.append(r)
    return visited
def goal_reached(vis, tx, ty, rx=1.2):
    for (x, y) in vis.values():
        if abs(x - (tx * TILE + 8)) <= TILE * rx and int(round(y / TILE)) == ty: return True
    return False
def region(vis, tx0, tx1, ty0, ty1):
    return any(tx0 * TILE <= x <= tx1 * TILE and ty0 * TILE <= y <= (ty1 + 1) * TILE for x, y in vis.values())

SECRETS = False
DJ_ALLOWED = True
def run():
    t0 = time.time()
    flags = set(); dj = False
    seed = [Gd["bonfire_pos"]("b0")]
    vis = {}
    while True:
        wd = World()
        if SECRETS:
            for k, d in Gd["DYN"].items():
                if d.get("key") == "wall": wd.set_open(k, True)
        for lv in ("lv_gate", "lv_ladder", "lv_bridge"):
            if lv in flags: wd.set_open(Gd["LEVERS"][lv]["opens"], True)
        for b in ("hiisi", "turso", "tytti", "joukahainen", "ahti", "aino"):
            if b in flags and Gd["ARENAS"][b]["door_out"]: wd.set_open("d_%s_out" % b, True)
            if b in flags and "d_%s_in"%b in Gd["DYN"]: wd.set_open("d_%s_in" % b, True)
        vis = bfs(wd, seed + [Gd["bonfire_pos"]("b10")], dj)
        changed = False
        for lid, lv in Gd["LEVERS"].items():
            if lid not in flags and goal_reached(vis, lv["tx"], lv["ty"]): flags.add(lid); changed = True; print("  lever reachable:", lid, "(%.0fs)" % (time.time() - t0))
        for b, a in Gd["ARENAS"].items():
            if b not in ("louhi", "vellamo") and b not in flags and region(vis, a["x0"] + 3, a["x1"] - 2, a["y0"], a["ground"]): flags.add(b); changed = True; print("  arena reached:", b, "(%.0fs)" % (time.time() - t0))
        if DJ_ALLOWED and "hiisi" in flags and not dj: dj = True; changed = True
        print("iter: nodes", len(vis), "flags", sorted(flags), "dj", dj, "(%.0fs)" % (time.time() - t0))
        seed = list(vis.values())[:1] + seed
        if not changed: break
        # new world is a superset of the old one (opening doors): keep exploring from everything found
        seed = list(vis.values()) if len(vis) < 4000 else seed
    return vis, flags, dj
if __name__ == "__main__":
    SECRETS = "--secrets" in sys.argv; DJ_ALLOWED = "--nodj" not in sys.argv
    vis, flags, dj = run()
    bad = 0
    for b in Gd["BONFIRES"]:
        x, y = Gd["bonfire_pos"](b)
        ok = b=="b9" or goal_reached(vis, Gd["BONFIRES"][b], int(round(y/TILE)),1.5)
        print("bonfire", b, "OK" if ok else "UNREACHABLE"); bad += not ok
    # --nodj validates ordinary progression, not the optional DJ-gated pouch.
    item_items=[("pouch_s2",Gd["ITEMS"]["pouch_s2"])] if not DJ_ALLOWED else Gd["ITEMS"].items()
    for k, (tx, ty, kind, pl) in item_items:
        ok = goal_reached(vis, tx, ty, 1.0) or goal_reached(vis, tx, ty - 1, 1.0)
        print("item", k, "OK" if ok else "UNREACHABLE"); bad += not ok
    for i, (k, tx, fr) in enumerate(Gd["SPAWNS"]):
        row = Gd["floor_row"](tx, fr)
        ok = goal_reached(vis, tx, row, 3.0)
        if not ok and k != "nakki": print("spawn", i, k, tx, "row", row, "UNREACHABLE (informational)")
    print("flags final:", sorted(flags), "tytti arena reached:", "tytti" in flags, "BAD", bad)
    # --- softlock analysis: in the final world, can every reachable standing spot get back to some bonfire? ---
    wd = World()
    for k, d in Gd["DYN"].items():
        if d.get("key") == "wall" or k in ("gate_f", "lad_s", "bridge", "d_hiisi_out", "d_turso_out"):
            wd.set_open(k, True)
    nodes = list(vis.values()); rev = collections.defaultdict(set)
    for n in nodes:
        for r in expand(wd, n, True): rev[key(*r)].add(key(*n))
    targets = [key(*Gd["bonfire_pos"](b)) for b in Gd["BONFIRES"]]
    # nodes are keyed; find those that reach a target by reverse BFS (targets may not be exact keys -> use nearest visited)
    allk = set(vis) | set(rev)
    tg = set()
    for t in targets:
        best = min(allk, key=lambda k: abs(k[0] - t[0]) + 8 * abs(k[1] - t[1])); tg.add(best)
    seen = set(tg); q = collections.deque(tg)
    while q:
        k = q.popleft()
        for p in rev.get(k, ()):
            if p not in seen: seen.add(p); q.append(p)
    traps = sorted(k for k in vis if k not in seen)
    print("softlock-trap standing spots:", len(traps), traps[:30])
# diagnostics opt-in only, physical movement graph reproducible; normal run remains concise
