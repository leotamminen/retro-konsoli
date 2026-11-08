
# ---------------- environment art: tiles, parallax, light ----------------
PAL={
 "forest": dict(sky=((10,20,36),(58,88,82)),lit=(84,62,46),deep=(46,34,30),top=(84,150,66),top2=(48,104,52),stone=(92,94,98),bw=(18,26,26),bwa=190,ambient=(172,186,190),fog=(120,160,150)),
 "swamp": dict(sky=((12,24,22),(70,96,62)),lit=(70,70,46),deep=(38,40,30),top=(112,130,58),top2=(70,96,46),stone=(80,88,78),bw=(16,24,20),bwa=190,ambient=(150,176,148),fog=(130,170,110)),
 "river": dict(sky=((8,6,24),(44,34,84)),lit=(76,76,104),deep=(36,34,58),top=(150,190,220),top2=(110,140,190),stone=(100,100,130),bw=(14,12,30),bwa=150,ambient=(136,136,186),fog=(110,110,190)),
 "pohjola":dict(sky=((5,7,17),(17,12,30)),lit=(57,65,87),deep=(20,25,43),top=(95,113,139),top2=(86,104,131),stone=(64,76,102),bw=(9,11,23),bwa=150,ambient=(33,33,50),fog=(61,68,104))}
def _h(x, y, s=0):
    n = (x * 374761393 + y * 668265263 + s * 1274126177) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFFFF

_TILE_EXPOSED = None
def _exposed_table():
    """sky exposure: air tile with no solid tile above it in its column"""
    global _TILE_EXPOSED
    if _TILE_EXPOSED is None:
        ex = [[False] * COLS for _ in range(ROWS)]
        for x in range(COLS):
            for y in range(ROWS):
                if GRID[y][x] == SOLID: break
                ex[y][x] = True
        _TILE_EXPOSED = ex
    return _TILE_EXPOSED

def render_chunk(cx, wd):
    """Static tiles for a 20-column chunk -> SRCALPHA surface (full world height)."""
    x0 = cx * 20; surf = mk(320, ROWS * TILE); ex = _exposed_table()
    G = GRID
    def t(x, y):
        if x < 0 or x >= COLS or y < 0: return SOLID
        if y >= ROWS: return SOLID
        return G[y][x]
    for tx in range(x0, min(COLS, x0 + 20)):
        area = area_at(tx); pal = PAL[area]; px = (tx - x0) * TILE
        for ty in range(ROWS):
            v = G[ty][tx]; py = ty * TILE; hh = _h(tx, ty)
            if v == SOLID:
                up, dn, lf, rt = t(tx, ty - 1), t(tx, ty + 1), t(tx - 1, ty), t(tx + 1, ty)
                exposed = not (up == SOLID and dn == SOLID and lf == SOLID and rt == SOLID)
                base = pal["lit"] if exposed else pal["deep"]
                var = 0.9 + (hh % 7) * 0.03
                _rc(surf, _mul(base, var), (px, py, TILE, TILE))
                for k in range(5):      # speckles
                    hk = _h(tx, ty, k + 1)
                    c = _mul(base, 1.35 if hk & 1 else 0.7)
                    _rc(surf, c, (px + (hk >> 1) % 14, py + (hk >> 5) % 14, 1 + (hk >> 9) % 2, 1))
                if area == "river" or (hh % 11 == 0):      # stone blocks
                    _ln(surf, _mul(base, 0.6), (px, py + 7 + hh % 3), (px + 15, py + 7 + hh % 3))
                    _ln(surf, _mul(base, 0.6), (px + 5 + hh % 6, py), (px + 5 + hh % 6, py + 7))
                if up != SOLID:           # lit top lip
                    _rc(surf, pal["top2"], (px, py, TILE, 4)); _rc(surf, pal["top"], (px, py, TILE, 2))
                    for k in range(5):
                        hk = _h(tx, ty, 20 + k)
                        hx = px + (hk % 15); hl = 1 + (hk >> 4) % 3
                        _rc(surf, pal["top"], (hx, py - hl + 1, 1, hl + 1))
                    _rc(surf, _mul(pal["top"], 1.3), (px + (hh % 12), py, 3, 1))
                if dn != SOLID:           # underside shadow and roots / icicles
                    _rc(surf, _mul(base, 0.45), (px, py + 13, TILE, 3))
                    if hh % 3 == 0:
                        _ln(surf, _mul(pal["top2"], 0.6) if area != "river" else (170, 200, 230), (px + 4 + hh % 8, py + 15), (px + 4 + hh % 8, py + 19 + hh % 4))
                if lf != SOLID: _rc(surf, _mul(base, 0.55), (px, py, 1, TILE))
                if rt != SOLID: _rc(surf, _mul(base, 0.55), (px + 15, py, 1, TILE))
            elif v == PLAT:
                _rc(surf, (104, 74, 46), (px, py, TILE, 5)); _rc(surf, (140, 100, 60), (px, py, TILE, 2))
                _rc(surf, (60, 40, 28), (px, py + 4, TILE, 1)); _rc(surf, (60, 40, 28), (px + 7, py, 1, 4))
                if area == "river": _rc(surf, (160, 190, 220), (px, py, TILE, 1))
                if hh % 2 == 0: _rc(surf, (80, 56, 38), (px + 2, py + 5, 2, 5))
            elif v == LADDER:
                _rc(surf, (110, 76, 46), (px + 3, py, 2, TILE)); _rc(surf, (110, 76, 46), (px + 11, py, 2, TILE))
                for k in (1, 5, 9, 13): _rc(surf, (150, 108, 64), (px + 3, py + k, 10, 2))
            elif v == THORN:
                c1, c2 = ((70, 40, 60), (190, 50, 70)) if area != "river" else ((160, 190, 210), (230, 240, 255))
                for k in range(4):
                    bx = px + 1 + k * 4
                    _poly(surf, c1, [(bx, py + 15), (bx + 2, py + 3 + (hh >> k) % 4), (bx + 4, py + 15)])
                    _rc(surf, c2, (bx + 2, py + 3 + (hh >> k) % 4, 1, 3))
            elif v == WATER:
                wc = {"forest": (40,90,120), "swamp": (50,100,70), "river": (50,70,170), "pohjola": (48,72,128), "ranta": (40,133,126), "syvanne": (35,70,128), "katedraali": (81,113,97)}[area]
                surf.fill(wc + (190,), (px, py, TILE, TILE))
                if t(tx, ty - 1) != WATER: surf.fill(_mul(wc, 1.8) + (230,), (px, py, TILE, 2))
            else:
                if not ex[ty][tx]:
                    b = pal["bw"]; a = pal["bwa"]
                    surf.fill(b + (a,), (px, py, TILE, TILE))
                    if (tx + ty) % 2 == 0: surf.fill(_mul(b, 1.5) + (a,), (px + 1, py + 8, 14, 1))
                    surf.fill(_mul(b, 1.5) + (a,), (px + (8 if ty % 2 else 0), py, 1, 8))
    return surf

def dyn_tile_surf(kind, w=1, h=1):
    """Surfaces for dynamic tiles; w,h in tiles."""
    key = ("dyn", kind, w, h)
    f = _DCACHE.get(key)
    if f: return f
    s = mk(w * TILE, h * TILE)
    if kind == "gate":
        for i in range(w * 2):
            _rc(s, (96, 70, 50), (i * 8 + 1, 0, 5, h * TILE)); _rc(s, (60, 44, 34), (i * 8 + 5, 0, 1, h * TILE))
        for j in range(0, h * TILE, 20): _rc(s, (50, 50, 56), (0, j + 4, w * TILE, 3)); _rc(s, (120, 120, 130), (0, j + 4, w * TILE, 1))
        for i in range(0, h * TILE, 5): _rc(s, (150, 150, 160), (w * TILE // 2, i, 1, 1))
    elif kind == "bridge":
        _rc(s, (110, 78, 48), (0, 0, w * TILE, 6)); _rc(s, (150, 106, 62), (0, 0, w * TILE, 2))
        for i in range(0, w * TILE, 8): _rc(s, (60, 40, 28), (i, 0, 1, 6))
        _rc(s, (70, 50, 34), (0, 6, w * TILE, 1))
    elif kind == "wall":
        s.fill((84, 84, 98, 255))
        for k in range(30): s.fill((60, 60, 76, 255), (_h(k, 3) % (w * TILE - 1), _h(k, 4) % (h * TILE - 1), 2, 1))
        _ln(s, (36, 34, 46), (2, 2), (w * TILE // 2, h * TILE // 2)); _ln(s, (36, 34, 46), (w * TILE // 2, h * TILE // 2), (w * TILE - 3, h * TILE // 2 + 6))
        _ln(s, (170, 170, 190), (4, 3), (w * TILE // 2 + 1, h * TILE // 2 - 1))
    elif kind == "lad":
        for j in range(h):
            _rc(s, (110, 76, 46), (3, j * TILE, 2, TILE)); _rc(s, (110, 76, 46), (11, j * TILE, 2, TILE))
            for k in (1, 5, 9, 13): _rc(s, (150, 108, 64), (3, j * TILE + k, 10, 2))
    _DCACHE[key] = s
    return s
_DCACHE = {}

FOG_DOORS={}
def fog_door(w, h, t):
    """Cached white mist wall: cheap animation, no per-frame surface allocation."""
    key=(w,h,t%120)
    if key in FOG_DOORS:return FOG_DOORS[key]
    s = mk(w * TILE, h * TILE)
    for i in range(0, h * TILE, 3):
        a = 120 + int(60 * math.sin(t * 0.07 + i * 0.3))
        x = int(4 * math.sin(t * 0.05 + i * 0.17))
        s.fill((220, 235, 245, a), (w * TILE // 2 - 6 + x, i, 12 + int(4 * math.sin(i * 0.4 + t * 0.09)), 3))
    FOG_DOORS[key]=s
    return s

# ---- parallax ----
_LAYERS = {}
CK = (255, 0, 255)
def _layer(w, h, draw):
    s = pygame.Surface((w, h)); s.fill(CK); s.set_colorkey(CK); draw(s, random.Random(w * 7 + h)); return s
def layers_for(area):
    if area in ("ranta", "syvanne", "katedraali"):
        return water_layers(area)
    if area in _LAYERS: return _LAYERS[area]
    sk = PAL[area]["sky"][1]
    if area == "forest":
        def far(s, r):
            pts = [(0, 90)]; x = 0
            while x < 480: x += 24; pts.append((x, 40 + r.randint(0, 40)))
            pts += [(480, 140), (0, 140)]; _poly(s, (36, 62, 66), pts)
        def mid(s, r):
            x = 0
            while x < 480:
                hgt = r.randint(40, 80); w2 = r.randint(14, 22)
                for k in range(4):
                    yy = 140 - hgt + k * hgt // 4; ww = w2 * (k + 1) // 3
                    _poly(s, (22, 44, 48), [(x, yy + hgt // 3), (x + ww // 2 + 3, yy - 8), (x + ww + 6, yy + hgt // 3)])
                _rc(s, (18, 34, 38), (x + w2 // 2 + 1, 140 - 12, 3, 12)); x += r.randint(14, 24)
        def near(s, r):
            x = 10
            while x < 480:
                tw = r.randint(8, 13); _rc(s, (14, 28, 32), (x, 0, tw, 180)); _rc(s, (22, 40, 44), (x, 0, 2, 180))
                by = r.randint(40, 120); _ln(s, (14, 28, 32), (x + tw, by), (x + tw + 20, by - 20), 3); _ln(s, (14, 28, 32), (x, by + 20), (x - 18, by), 3)
                x += r.randint(70, 130)
        L = [(_layer(480, 140, far), 0.12, 30), (_layer(480, 140, mid), 0.3, 50), (_layer(480, 180, near), 0.7, 0)]
    elif area == "swamp":
        def far(s, r):
            pts = [(0, 100)]; x = 0
            while x < 480: x += 20; pts.append((x, 70 + r.randint(0, 30)))
            pts += [(480, 140), (0, 140)]; _poly(s, (44, 70, 56), pts)
            x = 0
            while x < 480:
                th = r.randint(30, 60); _rc(s, (30, 52, 44), (x, 140 - th, 2, th)); _ln(s, (30, 52, 44), (x + 1, 140 - th + 8), (x + 7, 140 - th), 1); _ln(s, (30, 52, 44), (x + 1, 140 - th + 14), (x - 6, 140 - th + 8), 1); x += r.randint(18, 40)
        def mid(s, r):
            x = 0
            while x < 480:
                th = r.randint(60, 100); tw = r.randint(5, 8); _rc(s, (24, 40, 34), (x, 140 - th, tw, th))
                for k in range(3): _ln(s, (24, 40, 34), (x + tw // 2, 140 - th + 6 + k * 8), (x + r.randint(-16, 20), 140 - th - 6 + k * 6), 2)
                for k in range(4):
                    mx = x + r.randint(-14, 14); _ln(s, (36, 62, 46), (mx, 140 - th + 10), (mx + r.randint(-1, 1), 140 - th + 10 + r.randint(10, 26)), 1)
                x += r.randint(40, 80)
        def near(s, r):
            x = 20
            while x < 480:
                tw = r.randint(8, 12); _rc(s, (12, 24, 20), (x, 0, tw, 180))
                for k in range(3): _ln(s, (12, 24, 20), (x + tw // 2, r.randint(20, 100)), (x + r.randint(-30, 30), r.randint(-10, 20)), 3)
                for k in range(3):
                    vx = x + r.randint(-14, 20); _ln(s, (22, 44, 32), (vx, 0), (vx, r.randint(30, 80)), 1)
                x += r.randint(90, 150)
        L = [(_layer(480, 140, far), 0.1, 30), (_layer(480, 140, mid), 0.28, 50), (_layer(480, 180, near), 0.65, 0)]
    elif area == "pohjola":
        def far(s,r):
            for x in range(-15,520,38): _poly(s,(20,24,45),[(x,140),(x+34,r.randint(10,65)),(x+68,140)])
        def mid(s,r):
            for x in range(0,520,27):
                h=r.randint(40,93);_poly(s,(13,17,29),[(x,140),(x+9,140-h),(x+18,140)]);_rc(s,(10,14,25),(x+6,140-h,3,h))
        def near(s,r):
            for x in range(0,520,67):
                _ln(s,(10,13,22),(x,180),(x+8,r.randint(70,108)),3);_ln(s,(10,13,22),(x+8,112),(x+35,r.randint(45,87)),2)
                _ln(s,(10,13,22),(x,35),(x+18,90+r.randint(0,35)),2)
        L=[(_layer(480,140,far),0.09,25),(_layer(480,140,mid),0.25,40),(_layer(480,180,near),0.55,0)]
    else:
        def far(s, r):
            x = 0
            while x < 480:
                th = r.randint(20, 70); _poly(s, (30, 24, 60), [(x, 0), (x + 10, th), (x + 20, 0)]); x += r.randint(10, 24)
            pts = [(0, 140)]; x = 0
            while x < 480: x += 22; pts.append((x, 80 + r.randint(0, 50)))
            pts.append((480, 140)); _poly(s, (30, 24, 60), pts)
        def mid(s, r):
            x = 0
            while x < 480:
                hh = r.randint(60, 110); _rc(s, (26, 22, 52), (x, 140 - hh, 10, hh)); _rc(s, (26, 22, 52), (x + 50, 140 - hh, 10, hh))
                pygame.draw.arc(s, (26, 22, 52), (x, 140 - hh - 24, 60, 50), 0, 3.1416, 8)
                for k in range(3): pygame.draw.circle(s, (80, 90, 160), (x + 30 + r.randint(-8, 8), 140 - hh + 6 + r.randint(0, 20)), 1)
                x += r.randint(100, 170)
        def near(s, r):
            x = 5
            while x < 480:
                bh = r.randint(30, 80); _poly(s, (10, 8, 24), [(x, 180), (x + 7, 180 - bh), (x + 14, 180)])
                _poly(s, (10, 8, 24), [(x + 10, 0), (x + 16, r.randint(30, 80)), (x + 22, 0)]); x += r.randint(30, 70)
        L = [(_layer(480, 140, far), 0.1, 20), (_layer(480, 140, mid), 0.3, 40), (_layer(480, 180, near), 0.6, 0)]
    _LAYERS[area] = L
    return L

_SKY = {}
def sky_surface(area):
    if area in ("ranta", "syvanne", "katedraali"):
        return vellamo_bg(area)
    if area not in _SKY:
        s = pygame.Surface((W, H)); a, b = PAL[area]["sky"]
        for y in range(H):
            f = (y / H) ** 1.3
            _ln(s, tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3)), (0, y), (W, y))
        if area != "river":
            pygame.draw.circle(s, (230, 235, 210), (278, 62), 11); pygame.draw.circle(s, _mul(a, 1.3), (283, 59), 10)
            pygame.draw.circle(s, (230, 235, 210), (278, 62), 9); pygame.draw.circle(s, (205, 210, 190), (275, 59), 2)
            r = random.Random(3)
            for _ in range(40):
                x, y = r.randrange(W), r.randrange(H // 2); s.set_at((x, y), (200 + r.randrange(55),) * 3)
        else:
            r = random.Random(5)
            for _ in range(30):
                x, y = r.randrange(W), r.randrange(H); s.set_at((x, y), (90, 100 + r.randrange(100), 180))
        _SKY[area] = s
    return _SKY[area]

# ---- light and fog ----
_GLOW = {}
def glow(radius, color):
    k = (radius, color)
    if k not in _GLOW:
        s = pygame.Surface((radius * 2, radius * 2)); s.fill((0, 0, 0))
        for r in range(radius, 0, -2):
            f = (1 - r / radius) ** 1.8
            pygame.draw.circle(s, (int(color[0] * f), int(color[1] * f), int(color[2] * f)), (radius, radius), r)
        _GLOW[k] = s
    return _GLOW[k]
_VIG = None
def vignette():
    global _VIG
    if _VIG is None:
        s = pygame.Surface((W, H)); s.fill((255, 255, 255))
        for i in range(34):
            v = max(0, int(255 - (34 - i) ** 1.45 * 0.55))
            pygame.draw.rect(s, (v, v, v), (i, i * 180 // 320, W - 2 * i, H - 2 * (i * 180 // 320)), 1)
        _VIG = s
    return _VIG
_FOGS = {}
def fog_surface(area):
    if area in ("ranta", "syvanne", "katedraali"):
        return water_fog(area)
    if area not in _FOGS:
        s = mk(640, 64); r = random.Random(8); c = PAL[area]["fog"]
        for _ in range(26):
            x = r.randrange(640); y = r.randrange(10, 54); w = r.randint(60, 140); h = r.randint(10, 26)
            for k in range(3):
                e = mk(w, h); pygame.draw.ellipse(e, c + (10,), (0, 0, w, h)); pygame.draw.ellipse(e, c + (14,), (w // 6, h // 6, w * 2 // 3, h * 2 // 3))
                s.blit(e, (x - w // 2 + k * 3, y)); s.blit(e, (x - w // 2 - 640, y)) if x - w // 2 < 0 else None
                if x + w // 2 > 640: s.blit(e, (x - w // 2 - 640, y))
        _FOGS[area] = s
    return _FOGS[area]
