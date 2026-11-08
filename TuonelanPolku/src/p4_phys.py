
# ---------------- world runtime + shared physics ----------------
class World:
    def __init__(s):
        s.g = GRID
        s.state = {k: d["active"] for k, d in DYN.items()}
        s.dmap = {}
        s._rebuild()
    def _rebuild(s):
        s.dmap = {}
        for k, d in DYN.items():
            if s.state[k]:
                for t in d["tiles"]: s.dmap[t] = d["code"]
            elif d["code"] == SOLID:
                for t in d["tiles"]: s.dmap[t] = AIR       # an opened gate also clears the grid tile under it
    def opened(s, k):
        d = DYN[k]
        return (not s.state[k]) if d["code"] == SOLID else s.state[k]
    def set_open(s, k, opened):
        d = DYN[k]
        s.state[k] = (not opened) if d["code"] == SOLID else bool(opened)
        s._rebuild()
    def tile(s, tx, ty):
        if tx < 0 or tx >= COLS or ty >= ROWS: return SOLID
        if ty < 0: return SOLID if (tx, ty) not in s.dmap else AIR
        v = s.dmap.get((tx, ty))
        return s.g[ty][tx] if v is None else v
    def solid(s, tx, ty): return s.tile(tx, ty) == SOLID
    def is_ladder(s, tx, ty): return s.tile(tx, ty) == LADDER
    def ladder_top(s, tx, ty): return s.tile(tx, ty) == LADDER and s.tile(tx, ty - 1) != LADDER
    def surface(s, tx, ty, climbing=False):
        t = s.tile(tx, ty)
        if t == SOLID or t == PLAT: return True
        if t == LADDER and s.tile(tx, ty - 1) != LADDER and not climbing: return True
        return False

class Body:
    def __init__(s, x=0.0, y=0.0, w=PW_, h=PH_):
        s.x, s.y, s.w, s.h = float(x), float(y), w, h
        s.vx = s.vy = 0.0
        s.on_ground = False; s.wall = 0; s.coyote = 0; s.jbuf = 0; s.climb = False
        s.dj_used = False; s.drop_t = 0; s.run_speed = RUN; s.grav = GRAV; s.head = False

def move_body(wd, b, ghost_ok=False):
    """Axis-separated AABB move. b.x = centre, b.y = feet. Handles one-way platforms and ladder tops."""
    hw = b.w / 2.0
    b.wall = 0
    # --- horizontal ---
    nx = b.x + b.vx
    top = int((b.y - b.h) // TILE); bot = int((b.y - 0.01) // TILE)
    if b.vx > 0:
        tx = int((nx + hw) // TILE)
        for ty in range(top, bot + 1):
            if wd.solid(tx, ty): nx = tx * TILE - hw - 0.001; b.vx = 0; b.wall = 1; break
    elif b.vx < 0:
        tx = int((nx - hw) // TILE)
        for ty in range(top, bot + 1):
            if wd.solid(tx, ty): nx = (tx + 1) * TILE + hw + 0.001; b.vx = 0; b.wall = -1; break
    b.x = nx
    # --- vertical ---
    prev = b.y
    ny = b.y + b.vy
    l = int((b.x - hw + 0.5) // TILE); r = int((b.x + hw - 0.5) // TILE)
    b.on_ground = False; b.head = False
    if b.vy >= 0:
        row = int(ny // TILE)
        for ty in (row,):
            for tx in range(l, r + 1):
                t = wd.tile(tx, ty)
                if t == SOLID or ((t == PLAT or (t == LADDER and wd.tile(tx, ty - 1) != LADDER and not b.climb)) and b.drop_t <= 0 and prev <= ty * TILE + 0.001):
                    if t == SOLID and prev > ty * TILE + 0.001 and ny - ty * TILE > 8:
                        continue                      # already well inside (should not happen)
                    ny = ty * TILE; b.vy = 0; b.on_ground = True; break
            if b.on_ground: break
    else:
        row = int((ny - b.h) // TILE)
        for tx in range(l, r + 1):
            if wd.solid(tx, row):
                ny = (row + 1) * TILE + b.h + 0.001; b.vy = 0; b.head = True; break
    b.y = ny
    if b.drop_t > 0: b.drop_t -= 1
    return b.on_ground

def hazard_at(wd, b):
    """Thorn or water touching the feet area."""
    hw = b.w / 2.0
    for tx in range(int((b.x - hw + 1) // TILE), int((b.x + hw - 1) // TILE) + 1):
        for ty in (int((b.y - 3) // TILE), int((b.y - b.h * 0.5) // TILE)):
            if wd.tile(tx, ty) in (THORN, WATER): return True
    return False

def ladder_overlap(wd, b, below=False):
    tx = int(b.x // TILE)
    if below: return wd.is_ladder(tx, int((b.y + 1) // TILE)) and wd.ladder_top(tx, int((b.y + 1) // TILE))
    return wd.is_ladder(tx, int((b.y - b.h * 0.4) // TILE)) or wd.is_ladder(tx, int((b.y - 2) // TILE))

def walk_step(wd, b, ix, iy, jp, jh, dj_ok, drop=False, accel_g=0.55, accel_a=0.28):
    """One frame of free movement shared by the game and the traversal tester.
    ix/iy -1..1, jp = jump pressed this frame, jh = jump held. Returns dict of events."""
    ev = {}
    # ladders
    if not b.climb:
        if iy < -0.5 and ladder_overlap(wd, b) and not jp:
            b.climb = True; b.vx = b.vy = 0; b.x = int(b.x // TILE) * TILE + TILE / 2
        elif iy > 0.5 and b.on_ground and ladder_overlap(wd, b, below=True):
            b.climb = True; b.vx = b.vy = 0; b.x = int(b.x // TILE) * TILE + TILE / 2; b.y += 2
    if b.climb:
        if jp:
            b.climb = False; b.vy = JUMP_V * 0.7; b.vx = ix * 1.2; b.coyote = 0; ev["jump"] = True
            move_body(wd, b); return ev
        b.vx = 0; b.vy = iy * 1.15; b.dj_used = False
        tx = int(b.x // TILE)
        move_body(wd, b)
        if b.on_ground and iy > 0: b.climb = False
        elif not ladder_overlap(wd, b):
            # climbed over the top?
            if iy < 0 and wd.is_ladder(tx, int((b.y + 1) // TILE)):
                b.y = (int((b.y + 1) // TILE)) * TILE; b.climb = False; b.vy = 0; b.on_ground = True
            else:
                b.climb = False
        return ev
    sp = b.run_speed
    tgt = ix * sp
    a = accel_g if b.on_ground else accel_a
    if ix == 0 and b.on_ground: a = 0.7
    if b.vx < tgt: b.vx = min(tgt, b.vx + a)
    elif b.vx > tgt: b.vx = max(tgt, b.vx - a)
    if jp: b.jbuf = 6
    elif b.jbuf > 0: b.jbuf -= 1
    if b.on_ground: b.coyote = 6; b.dj_used = False
    elif b.coyote > 0: b.coyote -= 1
    if drop and b.on_ground and wd.tile(int(b.x // TILE), int((b.y + 1) // TILE)) in (PLAT, LADDER):
        b.drop_t = 10; b.y += 1.5; b.on_ground = False; b.jbuf = 0; b.coyote = 0
    elif b.jbuf > 0 and b.coyote > 0:
        b.vy = JUMP_V; b.coyote = 0; b.jbuf = 0; b.on_ground = False; ev["jump"] = True
    elif jp and dj_ok and not b.on_ground and b.coyote == 0 and not b.dj_used:
        b.vy = DJ_V; b.dj_used = True; b.jbuf = 0; ev["djump"] = True
    if not jh and b.vy < -2.4: b.vy = -2.4
    b.vy = min(MAX_FALL, b.vy + b.grav)
    was = b.on_ground
    move_body(wd, b)
    if b.on_ground and not was: ev["land"] = True
    return ev
