
# ---------------- procedural pixel art ----------------
def mk(w, h): return pygame.Surface((w, h), pygame.SRCALPHA)
def _ln(s, c, a, b, w=1): pygame.draw.line(s, c, a, b, w)
def _rc(s, c, r): pygame.draw.rect(s, c, r)
def _el(s, c, r): pygame.draw.ellipse(s, c, r)
def _poly(s, c, pts): pygame.draw.polygon(s, c, pts)
def _mul(c, f): return (max(0, min(255, int(c[0] * f))), max(0, min(255, int(c[1] * f))), max(0, min(255, int(c[2] * f))))
OUT = (14, 10, 18)

def _outline(s, col=OUT):
    """Dark 1px outline around the opaque pixels (what makes small sprites readable)."""
    m = pygame.mask.from_surface(s, 40)
    o = mk(s.get_width() + 2, s.get_height() + 2)
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
        o.blit(m.to_surface(setcolor=col, unsetcolor=(0, 0, 0, 0)), (dx, dy))
    o.blit(s, (1, 1))
    return o

# ---- humanoid rig (players, peikko, hukkunut, haamu ...) ----
PCLASS_PAL = {
    "warrior": dict(skin=(226, 182, 140), hair=(110, 70, 40), tunic=(150, 50, 50), trim=(210, 170, 70), cape=(110, 36, 44), boots=(70, 50, 40), metal=(190, 195, 205)),
    "sage":    dict(skin=(226, 182, 140), hair=(200, 200, 210), tunic=(60, 120, 130), trim=(230, 210, 130), cape=(40, 90, 110), boots=(60, 60, 70), metal=(150, 220, 200)),
    "hunter":  dict(skin=(214, 170, 130), hair=(60, 40, 30), tunic=(70, 100, 60), trim=(190, 150, 80), cape=(40, 70, 50), boots=(70, 55, 40), metal=(180, 180, 170)),
}
P2_TINT = {"warrior": (60, 110, 190), "sage": (170, 90, 190), "hunter": (200, 130, 50)}

def human(p, W=26, H=28):
    s = mk(W, H); c = p["pal"]; ox = 13; base = H - 2
    ph = p.get("phase", 0.0); lean = p.get("lean", 0); cr = p.get("crouch", 0)
    hip = (ox, base - 8 - cr); sh = (ox + lean, hip[1] - 7)
    cape = c.get("cape")
    if cape:
        fl = p.get("flow", 2)
        _poly(s, cape, [(sh[0] - 2, sh[1]), (sh[0] + 1, sh[1] + 1), (hip[0] - 3 - fl, hip[1] + 5), (hip[0] - 5 - fl, hip[1] + 2)])
    legs = []
    for k in (0, 1):
        a = ph + k * 3.14159
        fx = ox - 1 + 2 * k + int(round(math.sin(a) * p.get("stride", 4)))
        fy = base - int(max(0.0, math.cos(a)) * p.get("lift", 3))
        if p.get("air"): fx = ox - 2 + 4 * k + (2 if k else -1); fy = base - 4 - k * 2
        legs.append((fx, fy, k))
    for fx, fy, k in sorted(legs, key=lambda t: -t[2]):
        _ln(s, _mul(c["boots"], 0.8 if k == 0 else 1.0), (ox - 1 + 2 * k, hip[1]), (fx, fy), 2)
        _rc(s, c["boots"], (fx - 1 + (1 if k else 0), fy, 3, 1))
    # off arm
    def arm(angle, length=6, col=None, behind=False):
        a = math.radians(angle); hx = sh[0] + math.cos(a) * length; hy = sh[1] + 1 + math.sin(a) * length
        _ln(s, col or c["skin"], (sh[0], sh[1] + 1), (hx, hy), 2)
        return (int(round(hx)), int(round(hy)))
    offh = None
    if p.get("off_a") is not None: offh = arm(p["off_a"], 5, _mul(c["tunic"], 0.8))
    # torso
    _rc(s, c["tunic"], (ox - 3 + lean // 2, sh[1] - 1, 7, hip[1] - sh[1] + 3))
    _rc(s, c["trim"], (ox - 3 + lean // 2, hip[1] + 1, 7, 1))
    _rc(s, _mul(c["tunic"], 1.25), (ox + lean // 2, sh[1], 3, 2))
    # head
    hx, hy = ox + lean, sh[1] - 4
    pygame.draw.circle(s, c["skin"], (hx, hy), 3)
    if p.get("hood"):
        pygame.draw.circle(s, c["cape"], (hx, hy - 1), 4)
        _rc(s, c["skin"], (hx + 1, hy - 1, 3, 3))
    else:
        _rc(s, c["hair"], (hx - 3, hy - 3, 6, 2)); _rc(s, c["hair"], (hx - 3, hy - 1, 2, 3))
    _rc(s, (20, 14, 20), (hx + 1, hy, 1, 1))
    if c.get("helm"): _rc(s, c["metal"], (hx - 3, hy - 3, 7, 2))
    # shield / weapon arm
    fh = arm(p.get("arm_a", 40), 6)
    w = p.get("wpn"); wa = math.radians(p.get("wpn_a", 0))
    if w == "sword":
        ex, ey = fh[0] + math.cos(wa) * 9, fh[1] + math.sin(wa) * 9
        _ln(s, c["metal"], fh, (ex, ey), 2); _ln(s, (255, 255, 255), fh, (ex, ey), 1); _rc(s, c["trim"], (fh[0] - 1, fh[1] - 1, 3, 3))
    elif w == "dagger":
        ex, ey = fh[0] + math.cos(wa) * 5, fh[1] + math.sin(wa) * 5
        _ln(s, c["metal"], fh, (ex, ey), 2)
    elif w == "staff":
        ex, ey = fh[0] + math.cos(wa) * 10, fh[1] + math.sin(wa) * 10; bx, by = fh[0] - math.cos(wa) * 8, fh[1] - math.sin(wa) * 8
        _ln(s, (120, 90, 60), (bx, by), (ex, ey), 1)
        pygame.draw.circle(s, p.get("glow", c["metal"]), (int(ex), int(ey)), 2)
    elif w == "bow":
        pygame.draw.arc(s, (130, 90, 50), (fh[0] - 3, fh[1] - 8, 7, 16), -1.57, 1.57, 2) if not p.get("draw") else None
        if p.get("draw"):
            _ln(s, (130, 90, 50), (fh[0] + 2, fh[1] - 7), (fh[0] + 4, fh[1]), 2); _ln(s, (130, 90, 50), (fh[0] + 4, fh[1]), (fh[0] + 2, fh[1] + 7), 2)
            _ln(s, (220, 220, 200), (fh[0] + 2, fh[1] - 7), (fh[0] - 3, fh[1]), 1); _ln(s, (220, 220, 200), (fh[0] - 3, fh[1]), (fh[0] + 2, fh[1] + 7), 1)
            _ln(s, (230, 230, 210), (fh[0] - 3, fh[1]), (fh[0] + 7, fh[1]), 1)
        else:
            _ln(s, (220, 220, 200), (fh[0], fh[1] - 7), (fh[0], fh[1] + 7), 1)
    elif w == "club":
        ex, ey = fh[0] + math.cos(wa) * 9, fh[1] + math.sin(wa) * 9
        _ln(s, (110, 80, 50), fh, (ex, ey), 3); pygame.draw.circle(s, (80, 56, 36), (int(ex), int(ey)), 3)
    elif w == "spear":
        ex, ey = fh[0] + math.cos(wa) * 13, fh[1] + math.sin(wa) * 13; bx, by = fh[0] - math.cos(wa) * 5, fh[1] - math.sin(wa) * 5
        _ln(s, (150, 120, 90), (bx, by), (ex, ey), 1); pygame.draw.circle(s, c["metal"], (int(ex), int(ey)), 2)
    if p.get("shield"):
        sx, sy = (offh or (sh[0] + 4, sh[1] + 4))
        sa = p["shield"]    # 1 = held at side, 2 = raised guard
        if sa == 2: sx, sy = sh[0] + 5, sh[1] + 4
        pygame.draw.circle(s, _mul(c["trim"], 0.8), (sx, sy), 5 if sa == 2 else 4)
        pygame.draw.circle(s, c["cape"], (sx, sy), 3); _rc(s, c["metal"], (sx, sy, 1, 1))
    if p.get("flask"):
        _rc(s, (230, 120, 40), (hx + 2, hy - 1, 3, 4)); _rc(s, (255, 220, 120), (hx + 3, hy, 1, 2))
    return s

def _crop_outline(s):
    return _outline(s)

_PSPR = {}
def player_frame(cls, anim, t, flash=False, tint=None):
    key = (cls, anim, t, flash, tint)
    f = _PSPR.get(key)
    if f: return f
    pal = dict(PCLASS_PAL[cls])
    if tint: pal["trim"] = tint
    wpn = {"warrior": "sword", "sage": "staff", "hunter": "dagger"}[cls]
    p = dict(pal=pal, wpn=wpn, arm_a=50, wpn_a=-50, off_a=None, shield=1 if cls == "warrior" else 0, hood=(cls != "warrior"))
    if cls == "warrior": pal["helm"] = True
    if cls == "sage": p["glow"] = (170, 255, 230)
    if anim == "idle":
        p.update(phase=0.0, stride=0, lift=0, lean=0, flow=1 + (t % 2), crouch=1 if t % 2 else 0, wpn_a=-60 + (t % 2) * 6)
    elif anim == "run":
        p.update(phase=t * 1.57, stride=4, lift=3, lean=1, flow=3 + (t % 2), wpn_a=-40, arm_a=30 + (t % 2) * 10)
    elif anim in ("jump", "fall"):
        p.update(air=True, flow=4 if anim == "fall" else 1, wpn_a=-70 if anim == "jump" else -20, arm_a=-30 if anim == "jump" else 60, lean=0)
    elif anim == "roll":
        base = human(dict(pal=pal, air=True, crouch=4, lean=2, wpn=None, arm_a=100, flow=0, hood=p["hood"]))
        ang = -90 * t if t < 4 else 0
        f = pygame.transform.rotate(base, ang)
        out = mk(26, 28); out.blit(f, f.get_rect(center=(13, 17)))
        f = _outline(out)
        _PSPR[key] = f = _finish(f, flash); return f
    elif anim in ("atk1", "atk2", "atk3", "heavy", "stab", "slash"):
        ph = t   # 0 windup, 1 active, 2 recover
        if anim == "heavy":
            p.update(lean=[-2, 3, 2][ph], arm_a=[-100, 55, 40][ph], wpn_a=[-120, 40, 70][ph], crouch=[0, 2, 2][ph], flow=[0, 5, 3][ph], stride=2, phase=0.5)
        elif anim == "atk2":
            p.update(lean=[-1, 3, 2][ph], arm_a=[-20, 10, 20][ph], wpn_a=[-170, 15, 30][ph], crouch=[1, 1, 1][ph], flow=[0, 4, 2][ph], stride=2, phase=0.7)
        else:
            p.update(lean=[-2, 3, 2][ph], arm_a=[-70, 5, 25][ph], wpn_a=[-120 if anim != "atk3" else 90, 5 if anim != "atk3" else -5, 40][ph], crouch=[0, 1, 1][ph], flow=[0, 4, 2][ph], stride=2, phase=0.7)
        if cls == "sage": p["wpn_a"] = [-90, -5, 20][ph]
        if cls == "hunter": p["lean"] += 1
    elif anim == "guard":
        p.update(shield=2, arm_a=0, wpn_a=-30, lean=-1, crouch=1, phase=0.5, stride=2, off_a=10)
    elif anim == "bash":
        p.update(shield=2, arm_a=-20, lean=[2, 4][min(t, 1)], crouch=1, wpn_a=-80, off_a=20)
    elif anim == "cast":
        p.update(arm_a=-80 if t == 0 else -10, wpn_a=-60 if t == 0 else 0, lean=-1 if t == 0 else 2, glow=(200, 255, 240), off_a=-70 if t == 0 else -20)
    elif anim == "kantele":
        p.update(arm_a=-20 + (t % 2) * 25, off_a=10, lean=0, crouch=1, wpn=None, glow=(255, 240, 160))
    elif anim == "shoot":
        p.update(wpn="bow", draw=(t == 0), arm_a=-3, off_a=-3, lean=-1 if t == 0 else 1, crouch=1)
    elif anim == "hurt":
        p.update(lean=-3, arm_a=100, wpn_a=60, flow=5, air=True, off_a=80)
    elif anim == "drink":
        p.update(flask=True, arm_a=-100, lean=-1, crouch=1 + (t % 2), wpn=None, off_a=40)
    elif anim == "climb":
        p.update(phase=t * 3.14, stride=2, lift=2, arm_a=-100 if t % 2 else -60, off_a=-60 if t % 2 else -100, wpn=None, shield=0, flow=0)
    elif anim == "down":
        base = human(dict(pal=pal, wpn=None, crouch=0, hood=p["hood"], arm_a=80))
        f = pygame.transform.rotate(base, 90)
        out = mk(26, 28); out.blit(f, f.get_rect(midbottom=(13, 27)))
        _PSPR[key] = f = _finish(_outline(out), flash); return f
    f = _finish(_outline(human(p)), flash)
    _PSPR[key] = f
    return f

def _finish(f, flash):
    if flash:
        f = f.copy(); f.fill((120, 120, 120, 0), special_flags=pygame.BLEND_RGB_ADD)
    return f

# ---- enemy painters ----  each returns a surface; feet at bottom-centre minus 1
def _en_human(kind, anim, t):
    if kind == "peikko":
        pal = dict(skin=(108, 140, 80), hair=(60, 50, 30), tunic=(100, 70, 44), trim=(70, 50, 30), cape=None, boots=(60, 44, 30), metal=(150, 150, 140))
        p = dict(pal=pal, wpn="club", arm_a=30, wpn_a=-50, lean=2, crouch=1)
    elif kind == "jousi":
        pal = dict(skin=(140, 120, 80), hair=(150, 40, 40), tunic=(120, 50, 40), trim=(200, 150, 60), cape=(80, 30, 30), boots=(50, 40, 30), metal=(200, 200, 190))
        p = dict(pal=pal, wpn="bow", arm_a=-3, wpn_a=0, lean=0, hood=True)
    elif kind == "hukkunut":
        pal = dict(skin=(120, 150, 150), hair=(40, 70, 60), tunic=(70, 100, 90), trim=(50, 80, 70), cape=(40, 70, 60), boots=(50, 70, 70), metal=(150, 170, 160))
        p = dict(pal=pal, wpn="club", arm_a=50, wpn_a=60, lean=3, crouch=0)
    elif kind == "haamu":
        pal = dict(skin=(190, 215, 230), hair=(190, 215, 230), tunic=(70, 80, 110), trim=(120, 180, 220), cape=(40, 50, 90), boots=(60, 70, 100), metal=(170, 210, 240), helm=True)
        p = dict(pal=pal, wpn="spear", arm_a=0, wpn_a=-20, lean=0, hood=False, shield=1)
    else:
        raise KeyError(kind)
    if anim == "walk": p.update(phase=t * 1.57, stride=3, lift=2)
    elif anim == "idle": p.update(phase=0, stride=0, lift=0, crouch=p.get("crouch", 0) + (t % 2))
    elif anim == "windup":
        if kind == "haamu": p.update(arm_a=-5, wpn_a=-5, lean=-3, phase=0.5, stride=2)
        else: p.update(arm_a=-100, wpn_a=-130, lean=-3, phase=0.5, stride=2)
    elif anim == "attack":
        if kind == "haamu": p.update(arm_a=0, wpn_a=0, lean=5, phase=0.5, stride=4)
        else: p.update(arm_a=60, wpn_a=40, lean=5, crouch=2, phase=0.5, stride=3)
    elif anim == "hurt": p.update(lean=-3, arm_a=100, wpn_a=70, air=True)
    elif anim == "die": p.update(lean=-4, arm_a=110, wpn_a=90, air=True, crouch=2)
    p.setdefault("flow", 2)
    return human(p, 30, 32)

def _en_wolf(anim, t):
    s = mk(34, 20); fur = (110, 112, 125); dk = (70, 72, 85)
    cr = {"windup": 3, "attack": -1}.get(anim, 0)
    by = 7 + cr
    _el(s, fur, (6, by, 20, 9)); _poly(s, fur, [(24, by + 1), (32, by - 1 + (0 if anim != "attack" else -3)), (30, by + 6), (24, by + 8)])
    if anim == "attack": _ln(s, fur, (6, by + 3), (0, by - 3), 3)
    else: _ln(s, fur, (6, by + 3), (1, by + 5 + (t % 2)), 3)
    for k, lx in enumerate((9, 12, 20, 23)):
        ph = (t + k) % 4 if anim == "walk" else 0
        if anim == "attack": _ln(s, dk, (lx, by + 8), (lx - 3 + 6 * (k % 2), by + 9), 2)
        else: _ln(s, dk if k % 2 == 0 else fur, (lx, by + 7), (lx + (ph - 1.5), 18 - (1 if ph == 0 else 0)), 2)
    _poly(s, fur, [(29, by - 2), (31, by - 5), (32, by - 1)]); _rc(s, (250, 220, 90) if anim in ("windup", "attack") else (240, 240, 120), (30, by + 1, 1, 1))
    if anim in ("windup", "attack"): _rc(s, (240, 240, 240), (31, by + 4, 3, 1))
    return s

def _en_crow(anim, t, swan=False):
    s = mk(28, 20) if not swan else mk(34, 24)
    col = (30, 28, 42) if not swan else (40, 36, 60)
    up = (t // 4) % 2 == 0
    if anim in ("windup",): up = True
    cx, cy = (14, 10) if not swan else (16, 14)
    _el(s, col, (cx - 5, cy - 3, 11, 7))
    if up: _poly(s, col, [(cx - 2, cy - 2), (cx - 9, cy - 9), (cx + 2, cy - 3)]); _poly(s, _mul(col, 1.5), [(cx - 1, cy - 2), (cx - 4, cy - 8), (cx + 3, cy - 3)])
    else: _poly(s, col, [(cx - 2, cy), (cx - 10, cy + 4), (cx + 2, cy + 2)])
    _poly(s, col, [(cx - 5, cy), (cx - 11, cy + 2), (cx - 5, cy + 3)])
    if not swan:
        _poly(s, (200, 170, 60), [(cx + 5, cy - 1), (cx + 9, cy), (cx + 5, cy + 1)]); pygame.draw.circle(s, col, (cx + 4, cy - 2), 2)
        _rc(s, (255, 90, 80) if anim in ("windup", "attack") else (230, 230, 230), (cx + 4, cy - 3, 1, 1))
    else:
        _ln(s, (60, 54, 90), (cx + 4, cy - 2), (cx + 9, cy - 8), 2); pygame.draw.circle(s, (60, 54, 90), (cx + 10, cy - 9), 2)
        _poly(s, (200, 80, 60), [(cx + 12, cy - 9), (cx + 16, cy - 8), (cx + 12, cy - 7)]); _rc(s, (160, 240, 255), (cx + 10, cy - 10, 1, 1))
    return s

def _en_wisp(anim, t):
    s = mk(20, 20); r = 4 + (t // 5) % 2
    hot = anim in ("windup", "attack")
    c1 = (255, 190, 90) if hot else (120, 255, 200); c2 = (255, 90, 40) if hot else (40, 200, 140)
    _poly(s, _mul(c2, 0.7), [(7, 12), (13, 12), (10, 19)]); pygame.draw.circle(s, c2, (10, 10), r + 2); pygame.draw.circle(s, c1, (10, 10), r)
    _rc(s, (255, 255, 255), (9, 9, 2, 2)); _rc(s, (10, 40, 30), (8, 10, 1, 1)); _rc(s, (10, 40, 30), (12, 10, 1, 1))
    return s

def _en_nakki(anim, t):
    s = mk(24, 22); c = (60, 140, 100); dk = (30, 90, 70)
    leap = anim in ("attack",)
    cr = 2 if anim == "windup" else 0
    _el(s, c, (4, 6 + cr, 16, 12)); _poly(s, dk, [(8, 6 + cr), (11, 1 + cr), (14, 6 + cr)]); _poly(s, dk, [(3, 14), (0, 10), (6, 11)])
    _rc(s, (255, 240, 120), (14, 9 + cr, 2, 2)); _rc(s, (255, 240, 240), (15, 14 + cr, 4, 1)) if anim in ("windup", "attack") else None
    _ln(s, dk, (8, 17), (6, 20 + (0 if leap else t % 2)), 2); _ln(s, dk, (15, 17), (17, 20), 2)
    return s

def _en_henki(anim, t):
    s = mk(28, 34); cx = 14; fl = (t // 6) % 2
    robe = (50, 56, 100); lt = (150, 230, 255)
    _poly(s, robe, [(cx - 6, 10), (cx + 6, 10), (cx + 9, 30 + fl), (cx + 4, 27), (cx, 31), (cx - 4, 27), (cx - 9, 30 + fl)])
    pygame.draw.circle(s, (30, 34, 70), (cx, 8), 6); pygame.draw.circle(s, (210, 225, 235), (cx, 9), 4)
    hot = anim in ("windup", "attack")
    _rc(s, (255, 90, 90) if hot else (20, 20, 40), (cx - 2, 8, 1, 2)); _rc(s, (255, 90, 90) if hot else (20, 20, 40), (cx + 1, 8, 1, 2))
    _ln(s, (60, 66, 110), (cx + 5, 16), (cx + 10, 14 - (4 if hot else 0)), 2)
    pygame.draw.circle(s, (255, 160, 90) if hot else lt, (cx + 11, 12 - (4 if hot else 0)), 3)
    return s

_ESPR = {}
EN_SIZE = {"peikko": (30, 32), "jousi": (30, 32), "hukkunut": (30, 32), "haamu": (30, 32), "susi": (34, 20),
           "korppi": (28, 20), "joutsen": (34, 24), "virvatuli": (20, 20), "nakki": (24, 22), "henki": (28, 34)}
def enemy_frame(kind, anim, t, flip=False, flash=False):
    key = (kind, anim, t, flip, flash)
    f = _ESPR.get(key)
    if f: return f
    if kind in ("peikko", "jousi", "hukkunut", "haamu"): base = _en_human(kind, anim, t)
    elif kind == "susi": base = _en_wolf(anim, t)
    elif kind == "korppi": base = _en_crow(anim, t)
    elif kind == "joutsen": base = _en_crow(anim, t, True)
    elif kind == "virvatuli": base = _en_wisp(anim, t)
    elif kind == "nakki": base = _en_nakki(anim, t)
    elif kind == "henki": base = _en_henki(anim, t)
    else: base = mk(16, 16)
    f = base if kind == "virvatuli" else _outline(base)
    if flip: f = pygame.transform.flip(f, True, False)
    f = _finish(f, flash)
    _ESPR[key] = f
    return f
