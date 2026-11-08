
# ---------------- boss art ----------------
_BSPR = {}
def hiisi_frame(pose, t, flip=False, flash=False, enraged=False):
    key = ("hiisi", pose, t, flip, flash, enraged)
    f = _BSPR.get(key)
    if f: return f
    s = mk(72, 70)
    club_a, lean, cr, mouth = {"idle": (50, 0, 0, 0), "walk": (40, 2, 0, 0), "slam_w": (-110, -4, 0, 1), "slam": (70, 6, 3, 0),
        "sweep_w": (-170, -6, 2, 1), "sweep": (10, 7, 2, 0), "charge_w": (60, -5, 4, 1), "charge": (20, 9, 2, 1), "roar": (-30, -3, 0, 2),
        "stagger": (80, -6, 5, 1), "hurt": (60, -3, 2, 0), "die": (90, -8, 8, 0), "rock": (-80, -2, 0, 1)}.get(pose, (50, 0, 0, 0))
    bob = (t // 8) % 2 if pose == "idle" else 0
    skin = (92, 86, 70) if not enraged else (110, 70, 58); moss = (60, 100, 56); dk = _mul(skin, 0.6)
    gx = 34 + lean; base = 66; hip = base - 22 + cr
    # legs
    for k, dx in enumerate((-8, 8)):
        ph = (t // 5 + k) % 2 if pose in ("walk", "charge") else 0
        _rc(s, dk if k == 0 else skin, (34 + dx - 4, hip, 9, base - hip - (2 if ph else 0)))
        _rc(s, _mul(skin, 0.5), (34 + dx - 5, base - 3 - (2 if ph else 0), 11, 3))
    # body
    _poly(s, skin, [(gx - 14, hip + 2), (gx - 17, hip - 20 - bob), (gx - 8, hip - 30 - bob), (gx + 8, hip - 30 - bob), (gx + 17, hip - 20 - bob), (gx + 14, hip + 2)])
    _poly(s, moss, [(gx - 17, hip - 20 - bob), (gx - 8, hip - 30 - bob), (gx + 4, hip - 30 - bob), (gx - 4, hip - 21 - bob), (gx - 10, hip - 14)])
    for k in range(6): _rc(s, _mul(skin, 1.2), (gx - 10 + k * 3, hip - 14 + (k * 5) % 9, 2, 1))
    # head with antlers
    hx, hy = gx + 3, hip - 36 - bob
    pygame.draw.circle(s, skin, (hx, hy), 8)
    _rc(s, (20, 14, 14), (hx - 2, hy + 2, 8, 2 + mouth * 2))
    ey = (255, 120, 40) if not enraged else (255, 50, 40)
    _rc(s, ey, (hx - 4, hy - 3, 3, 2)); _rc(s, ey, (hx + 2, hy - 3, 3, 2))
    for sx_, dr in ((-1, -1), (1, 1)):
        bx = hx + sx_ * 5
        _ln(s, (150, 130, 100), (bx, hy - 6), (bx + dr * 6, hy - 16), 2); _ln(s, (150, 130, 100), (bx + dr * 3, hy - 11), (bx + dr * 10, hy - 12), 1); _ln(s, (150, 130, 100), (bx + dr * 5, hy - 14), (bx + dr * 4, hy - 20), 1)
    # arm + club
    shx, shy = gx + 12, hip - 24 - bob
    a = math.radians(club_a); hx2 = shx + math.cos(a) * 14; hy2 = shy + math.sin(a) * 14
    _ln(s, skin, (shx, shy), (hx2, hy2), 6)
    ex, ey2 = hx2 + math.cos(a) * 22, hy2 + math.sin(a) * 22
    _ln(s, (96, 70, 44), (hx2, hy2), (ex, ey2), 5); pygame.draw.circle(s, (74, 54, 34), (int(ex), int(ey2)), 7)
    for k in range(3): _rc(s, (170, 170, 160), (int(ex) - 5 + k * 4, int(ey2) - 5 + (k % 2) * 6, 2, 2))
    off = (-12 + 0, hip - 24 - bob)
    _ln(s, dk, (gx - 12, hip - 24 - bob), (gx - 18, hip - 8 + (t // 8) % 2), 5)
    f = _outline(s)
    if flip: f = pygame.transform.flip(f, True, False)
    f = _finish(f, flash)
    _BSPR[key] = f
    return f

def tytti_frame(pose, t, flip=False, flash=False, enraged=False):
    key = ("tytti", pose, t, flip, flash, enraged)
    f = _BSPR.get(key)
    if f: return f
    s = mk(70, 64); cx = 30; fl = (t // 6) % 3
    bob = int(2 * math.sin(t * 0.08)) if pose == "idle" else 0
    robe = (30, 24, 54); trim = (150, 120, 220) if not enraged else (230, 90, 150)
    top = 20 + bob
    _poly(s, robe, [(cx - 7, top + 6), (cx + 7, top + 6), (cx + 13, 56 + fl), (cx + 6, 52), (cx, 58), (cx - 6, 52), (cx - 13, 56 - fl)])
    _poly(s, _mul(robe, 1.5), [(cx - 3, top + 8), (cx + 3, top + 8), (cx + 6, 52), (cx - 6, 52)])
    _rc(s, trim, (cx - 7, top + 6, 14, 1))
    hair = (14, 10, 24)
    pygame.draw.circle(s, hair, (cx, top), 7); _poly(s, hair, [(cx - 7, top), (cx - 11, top + 24 + fl), (cx - 4, top + 8)]); _poly(s, hair, [(cx + 6, top + 2), (cx + 10, top + 22 - fl), (cx + 3, top + 8)])
    pygame.draw.circle(s, (206, 214, 232), (cx, top + 1), 4)
    hot = pose in ("slash_w", "cast", "beam", "tele_in")
    ec = (255, 70, 110) if hot or enraged else (110, 220, 255)
    _rc(s, ec, (cx - 2, top, 1, 1)); _rc(s, ec, (cx + 1, top, 1, 1))
    for k in range(5): _poly(s, (220, 220, 200), [(cx - 6 + k * 3, top - 5), (cx - 5 + k * 3, top - 9 - (k % 2) * 2), (cx - 4 + k * 3, top - 5)])
    # scythe
    ang = {"idle": 70, "slash_w": -150, "slash": 20, "cast": -100, "beam": -90, "stagger": 100, "hurt": 90, "tele_in": 80, "die": 100}.get(pose, 70)
    a = math.radians(ang); sx0, sy0 = cx + 8, top + 12
    ex, ey = sx0 + math.cos(a) * 24, sy0 + math.sin(a) * 24; bx, by = sx0 - math.cos(a) * 10, sy0 - math.sin(a) * 10
    _ln(s, (130, 100, 70), (bx, by), (ex, ey), 2)
    pa = a - 1.6
    _poly(s, (190, 215, 240), [(ex, ey), (ex + math.cos(pa) * 14, ey + math.sin(pa) * 14), (ex + math.cos(pa + 0.5) * 6 + math.cos(a) * 4, ey + math.sin(pa + 0.5) * 6 + math.sin(a) * 4)])
    _ln(s, (230, 245, 255), (ex, ey), (ex + math.cos(pa) * 14, ey + math.sin(pa) * 14), 1)
    _ln(s, (200, 190, 230), (cx + 4, top + 8), (sx0, sy0), 2)
    f = _outline(s)
    if flip: f = pygame.transform.flip(f, True, False)
    f = _finish(f, flash)
    _BSPR[key] = f
    return f

def turso_draw(c, ox, oy, bx, by, hx, hy, t, mouth, flash, enraged):
    """Draws Iku-Turso: a neck from (bx,by) base to head (hx,hy). Coordinates are screen coordinates."""
    n = 14
    col = (50, 120, 110) if not enraged else (120, 60, 90); dk = _mul(col, 0.55); lt = _mul(col, 1.5)
    if flash: col = (200, 200, 200); dk = (160, 160, 160); lt = (255, 255, 255)
    pts = []
    for i in range(n + 1):
        f = i / n
        # curve: rises from the base then bends to the head
        mx = bx + (hx - bx) * f + math.sin(f * 3.14159) * -18 + math.sin(t * 0.07 + f * 4) * 3 * f
        my = by + (hy - by) * f - math.sin(f * 3.14159) * 14
        pts.append((mx, my))
    for i, (px, py) in enumerate(pts):
        r = 9 - i * 0.28 if i < n else 7
        pygame.draw.circle(c, dk, (int(px), int(py) + 1), int(r + 1)); pygame.draw.circle(c, col, (int(px), int(py)), int(r))
        if i % 2 == 0: pygame.draw.circle(c, lt, (int(px) - 1, int(py) - 2), max(1, int(r * 0.4)))
        if i % 3 == 1: _poly(c, dk, [(px - 2, py - r), (px + 1, py - r - 5), (px + 4, py - r)])
    # base blob (coils in the water)
    for k in range(3): pygame.draw.circle(c, col, (int(bx) + k * 9 - 9, int(by) + 4), 10); pygame.draw.circle(c, dk, (int(bx) + k * 9 - 9, int(by) + 8), 5)
    dx = hx - pts[-2][0]; dy = hy - pts[-2][1]; ang = math.atan2(dy, dx)
    # head
    hs = pygame.Surface((46, 36), pygame.SRCALPHA)
    _el(hs, dk, (4, 8, 36, 22)); _el(hs, col, (4, 6, 34, 20))
    jaw = 3 + mouth * 9
    _poly(hs, (30, 20, 30), [(20, 18), (42, 18 + jaw // 2), (20, 20 + jaw)])
    for k in range(5): _poly(hs, (240, 240, 230), [(22 + k * 4, 18), (24 + k * 4, 18 + 4), (26 + k * 4, 18)])
    _poly(hs, lt, [(10, 8), (4, 0), (18, 6)]); _poly(hs, lt, [(18, 6), (14, -2), (26, 6)]) if False else None
    ey = (255, 220, 80) if not enraged else (255, 60, 60)
    pygame.draw.circle(hs, ey, (26, 12), 3); _rc(hs, (20, 10, 10), (26, 11, 2, 3))
    fdir = -1 if dx < 0 else 1
    if fdir < 0: hs = pygame.transform.flip(hs, True, False)
    phi = math.degrees(math.atan2(dy, abs(dx))); phi = max(-60, min(60, phi))
    hs = pygame.transform.rotate(hs, -fdir * phi)
    c.blit(hs, hs.get_rect(center=(int(hx), int(hy))))

def louhi_frame(pose="idle",t=0,flash=False,phase=1):
    k=("louhi",pose,t%4,flash,phase)
    if k in _BSPR:return _BSPR[k]
    s=mk(150,112); dark=(15+phase*2,17,29+phase*4); edge=(71,78,109)
    # A huge ragged northern eagle/mistress silhouette, not a resized humanoid.
    for side in (-1,1):
        pts=[(75,48),(75+side*25,30 if pose!="windup" else 14),(75+side*68,8 if pose=="windup" else 25),(75+side*48,47),(75+side*65,38),(75+side*42,63),(75+side*20,72)]
        pygame.draw.polygon(s,dark,pts);pygame.draw.lines(s,edge,False,pts,2)
        for j in range(5):
            x=75+side*(26+j*8);y=40+j%2*4;pygame.draw.line(s,edge,(x,y),(x+side*14,y+29-j*2),3)
    pygame.draw.ellipse(s,dark,(61,32,29,65));pygame.draw.ellipse(s,edge,(61,32,29,65),2)
    # horns/crown, beak and three baleful eyes.
    pygame.draw.polygon(s,(118,133,162),[(60,49),(66,23),(72,43),(77,15),(82,43),(91,24),(88,56)])
    pygame.draw.polygon(s,(217,219,214),[(91,49),(112,55),(93,60)])
    for xx,yy in ((78,47),(86,44),(83,53)):pygame.draw.circle(s,(255,48,32),(xx,yy),3 if phase>=3 else 2)
    if phase>=2:
        for xx in (68,79,89):pygame.draw.polygon(s,(141,180,235),[(xx,88),(xx-5,106),(xx+5,106)])
    if phase>=3:
        pygame.draw.circle(s,(212,180,99),(75,72),13,2);pygame.draw.circle(s,(255,232,143),(75,72),5,2)
    if flash:s.set_colorkey((0,0,0));white=pygame.Surface(s.get_size());white.fill((255,240,235));white.blit(s,(0,0),special_flags=pygame.BLEND_RGB_MULT);s=white
    _BSPR[k]=s;return s
