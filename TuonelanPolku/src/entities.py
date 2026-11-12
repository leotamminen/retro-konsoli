
# ---------------- entities: particles, projectiles, zones, enemies, bosses ----------------
def ov(a, b): return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]

class Parts:
    def __init__(s): s.l = []
    def add(s, x, y, vx, vy, life, col, size=1, grav=0.0):
        if len(s.l) < 360: s.l.append([x, y, vx, vy, life, life, col, size, grav])
    def burst(s, x, y, col, n=8, sp=1.6, life=22, size=1, grav=0.08, up=0.0):
        for _ in range(n):
            a = random.random() * 6.283; v = random.random() * sp
            s.add(x, y, math.cos(a) * v, math.sin(a) * v - up, life + random.randint(-6, 6), col, size, grav)
    def update(s):
        out = []
        for p in s.l:
            p[0] += p[2]; p[1] += p[3]; p[3] += p[8]; p[4] -= 1
            if p[4] > 0: out.append(p)
        s.l = out
    def draw(s, surf, cx, cy):
        for p in s.l:
            x = int(p[0] - cx); y = int(p[1] - cy)
            if -4 < x < W + 4 and -4 < y < H + 4:
                c = p[6]
                if p[4] < p[5] * 0.4: c = (c[0] * 2 // 3, c[1] * 2 // 3, c[2] * 2 // 3)
                surf.fill(c, (x, y, p[7], p[7]))

class Atk:
    """A melee hitbox attached to a body. rel = (forward offset, y offset from feet, w, h)."""
    __slots__ = ("rel", "dmg", "kb", "kbu", "tags", "hit", "poise", "pid", "t", "mult")
    def __init__(s, rel, dmg, kb=2.0, tags=(), poise=20, kbu=0.0, pid=0):
        s.rel = rel; s.dmg = dmg; s.kb = kb; s.kbu = kbu; s.tags = set(tags); s.hit = set(); s.poise = poise; s.pid = pid; s.t = 0; s.mult = 1.0
    def rect(s, x, y, face):
        ox, oy, w, h = s.rel
        return (x + ox if face > 0 else x - ox - w, y + oy, w, h)

class Proj:
    def __init__(s, kind, x, y, vx, vy, dmg, w=6, h=6, enemy=True, life=240, grav=0.0, tags=(), homing=0.0, pid=0, pierce=0, poise=10, col=(255, 160, 80), hp=1, curve=0):
        s.kind = kind; s.x = x; s.y = y; s.vx = vx; s.vy = vy; s.dmg = dmg; s.w = w; s.h = h; s.enemy = enemy; s.life = life
        s.grav = grav; s.tags = set(tags); s.homing = homing; s.pid = pid; s.pierce = pierce; s.poise = poise; s.col = col
        s.hit = set(); s.dead = False; s.t = 0; s.hp = hp; s.kbx = 1.5; s.curve = curve; s.wd = None
    def rect(s): return (s.x - s.w / 2, s.y - s.h / 2, s.w, s.h)
    def update(s, g):
        s.wd = g.wd
        if s.kind in ("runic", "verse", "memory", "thornwave", "bubble", "swell"):
            s.t += 1; s.life -= 1
            if s.life <= 0: s.dead = True; return
            s.x += s.vx; s.y += s.vy; s.vy += s.curve
            if s.kind == "bubble": s.vy -= .012
            if s.kind not in ("thornwave",) and g.wd.solid(int(s.x // TILE), int(s.y // TILE)): s.dead = True
            return
        s.t += 1; s.life -= 1
        if s.life <= 0: s.dead = True; return
        if s.homing and s.enemy:
            t = g.nearest_player(s.x, s.y)
            if t:
                ta = math.atan2(t.y - 9 - s.y, t.x - s.x); ca = math.atan2(s.vy, s.vx)
                d = (ta - ca + math.pi) % (2 * math.pi) - math.pi
                ca += max(-s.homing, min(s.homing, d)); sp = math.hypot(s.vx, s.vy)
                s.vx = math.cos(ca) * sp; s.vy = math.sin(ca) * sp
        s.vy += s.grav
        if s.kind == "wave":
            s.x += s.vx; return
        s.x += s.vx; s.y += s.vy
        if s.kind not in ("rock",) and g.wd.solid(int(s.x // TILE), int(s.y // TILE)):
            s.dead = True; g.parts.burst(s.x, s.y, s.col, 5, 1.0, 14)
            if s.kind == "spit": g.spit_land(s)
        if s.kind in ("orb", "bolt", "spit") and s.t % 3 == 0:
            g.parts.add(s.x, s.y, random.uniform(-.2, .2), random.uniform(-.2, .2), 14, s.col, 1)
    def draw(s, surf, cx, cy):
        x = int(s.x - cx); y = int(s.y - cy); co = s.col
        if s.kind in ("runic", "memory"):
            pygame.draw.rect(surf, co, (x - 2, y - 6, 4, 12), 1); pygame.draw.line(surf, co, (x - 5, y + 3), (x + 5, y - 3), 1); return
        if s.kind == "thornwave":
            pygame.draw.polygon(surf, co, [(x - 4, y + 7), (x, y - 8), (x + 4, y + 7)]); return
        if s.kind == "bubble":
            pygame.draw.circle(surf, co, (x, y), 6, 1); pygame.draw.circle(surf, (223, 250, 234), (x + 2, y - 2), 1); return
        if s.kind == "verse":
            pygame.draw.arc(surf, co, (x - 8, y - 10, 15, 21), -math.pi / 2, math.pi, 1); pygame.draw.circle(surf, co, (x - 4, y + 8), 3); return
        if s.kind == "swell":
            pygame.draw.arc(surf, co, (x - 13, y - 22, 27, 40), 0, math.pi, 3); pygame.draw.arc(surf, (173, 233, 227), (x - 6, y - 13, 13, 23), 0, math.pi, 1); return
        if s.kind == "arrow":
            a = math.atan2(s.vy, s.vx); ex = int(math.cos(a) * 6); ey = int(math.sin(a) * 6)
            pygame.draw.line(surf, (200, 180, 140), (x - ex, y - ey), (x + ex, y + ey), 1); surf.set_at((x + ex, y + ey), (240, 240, 240))
        elif s.kind == "parrow":
            a = math.atan2(s.vy, s.vx); ex = int(math.cos(a) * 7); ey = int(math.sin(a) * 7)
            pygame.draw.line(surf, (230, 210, 150), (x - ex, y - ey), (x + ex, y + ey), 1); surf.set_at((x + ex, y + ey), (255, 255, 255))
        elif s.kind in ("orb", "bolt", "spit"):
            r = 3 if s.kind != "bolt" else 2 + (s.t // 3) % 2
            c = s.col
            pygame.draw.circle(surf, _mul(c, 0.5), (x, y), r + 1); pygame.draw.circle(surf, c, (x, y), r); surf.set_at((x, y), (255, 255, 255))
        elif s.kind == "wave":
            f = (s.t // 3) % 2
            sgn = 1 if s.vx > 0 else -1
            pygame.draw.polygon(surf, _mul(s.col, 0.6), [(x - sgn * 4, y), (x - sgn * 2, y - 8 - f), (x + sgn * 5, y - 2), (x + sgn * 5, y)])
            pygame.draw.polygon(surf, s.col, [(x - sgn * 2, y), (x, y - 6 - f), (x + sgn * 3, y - 2), (x + sgn * 3, y)])
        elif s.kind == "rock":
            pygame.draw.circle(surf, (96, 90, 84), (x, y), 6); pygame.draw.circle(surf, (130, 124, 116), (x - 2, y - 2), 3); pygame.draw.circle(surf, (50, 46, 44), (x + 2, y + 2), 2)
        else:
            surf.fill(s.col, (x - 1, y - 1, 3, 3))

class Zone:
    """Telegraphed area hazard: warns for `delay` frames, then hurts for `life` frames."""
    def __init__(s, x, y, w, h, delay, life, dmg, style="rock", kb=2.5, tags=("heavy",)):
        s.x = x; s.y = y; s.w = w; s.h = h; s.delay = delay; s.life = life; s.dmg = dmg; s.style = style; s.t = 0; s.hit = set(); s.dead = False
        s.kb = kb; s.tags = set(tags)
    @property
    def active(s): return s.t >= s.delay
    def rect(s):
        if s.style == "bog" and s.active: return (s.x - 24, s.y - 20, 48, 5)
        return (s.x - s.w / 2, s.y - s.h, s.w, s.h)
    def update(s, g):
        s.t += 1
        if s.t == s.delay:
            if s.style == "rock": g.shake(3, 8); sfx("boom", 0.5); g.parts.burst(s.x, s.y, (150, 140, 130), 10, 1.8, 20, 2, 0.1, 0.8)
            elif s.style == "geyser": sfx("splash", 0.9); g.parts.burst(s.x, s.y, (150, 200, 255), 12, 1.6, 22, 1, 0.05, 2.0)
            elif s.style == "beam": sfx("ice", 0.8)
        if s.t >= s.delay + s.life: s.dead = True
        if s.style == "bog" and s.active:
            for p in g.players:
                if abs(p.x - s.x) < 24 and abs(p.y - s.y) < 32:
                    bo = getattr(p, "bog", None)
                    if bo != s:
                        p.bog = s; p.bog_t = 90; p.vx = 0; p.y = s.y; p.vy = 0
                    elif p.pad.pressed("jump"):
                        p.bog_t = 0; p.bog = None; p.y -= 18; p.vy = JUMP_V; p.inv = max(p.inv, 80); s.dead = True
                    else:
                        p.bog_t -= 1
                        if s.t % 90 == 0: p.take_hit(12 * D()["dmg"], s.x, 0, tags=("magic",))
                        if p.bog_t <= 0: p.bog = None; s.dead = True
    def draw(s, surf, cx, cy):
        x = int(s.x - cx); y = int(s.y - cy); w = int(s.w); h = int(s.h)
        if not s.active:
            f = s.t / max(1, s.delay); a = 60 + int(120 * f)
            warn = pygame.Surface((w, h if s.style != "rock" else 4), pygame.SRCALPHA)
            col = (126,190,255) if s.style=="frost" else (194,138,255) if s.style=="stolen" else (255,80,60) if s.style!="puddle" else (160,255,90)
            if s.style == "ghost":
                if (s.t // 3) % 2 == 0:
                    gs = tytti_frame("idle", 0, False, False, False).copy(); gs.set_alpha(40 + int(80 * f)); surf.blit(gs, (x - gs.get_width() // 2, y - gs.get_height() + 8))
            elif s.style == "beam": warn.fill(col + (int(40 + 60 * f),)); surf.blit(warn, (x - w // 2, y - h))
            elif s.style == "rock":
                warn.fill(col + (a,)); surf.blit(warn, (x - w // 2, y - 3))
                if (s.t // 4) % 2 == 0: pygame.draw.line(surf, (255, 200, 120), (x, y - 6), (x, y - 14), 1)
                rem = s.delay - s.t
                if rem < 24:
                    ry = y - 6 - rem * 5
                    pygame.draw.circle(surf, (96, 90, 84), (x, ry), 6); pygame.draw.circle(surf, (130, 124, 116), (x - 2, ry - 2), 3)
            else:
                warn.fill(col + (int(30 + 50 * f),)); surf.blit(warn, (x - w // 2, y - 6 if s.style == "geyser" else y - h)); 
                if s.style == "geyser" and (s.t // 3) % 2 == 0: surf.fill((200, 230, 255), (x - 3 + (s.t % 5), y - 8 - (s.t % 7), 2, 2))
        else:
            k = s.t - s.delay
            if s.style == "geyser":
                hh = min(h, 12 + k * 14) if k < s.life - 4 else max(0, h * (s.delay + s.life - s.t) // 4)
                pygame.draw.rect(surf, (140, 200, 255), (x - w // 2, y - hh, w, hh)); pygame.draw.rect(surf, (230, 245, 255), (x - w // 4, y - hh, w // 2, hh))
            elif s.style == "beam":
                pygame.draw.rect(surf, (255, 120, 190), (x - w // 2, y - h, w, h)); pygame.draw.rect(surf, (255, 240, 250), (x - w // 4, y - h, max(2, w // 2), h))
            elif s.style == "rock":
                pass
            elif s.style == "puddle":
                pygame.draw.ellipse(surf, (90, 200, 70), (x - w // 2, y - 5, w, 6)); pygame.draw.ellipse(surf, (190, 255, 120), (x - w // 3, y - 4, w * 2 // 3, 3))
                if (s.t // 7) % 2 == 0: surf.fill((220, 255, 150), (x - 4 + (s.t * 3) % 9, y - 8, 1, 2))

ESPEC = {
    "peikko":   dict(hp=34, w=12, h=20, souls=14, poise=22, spd=0.8, wake=130, dmg=20),
    "susi":     dict(hp=24, w=18, h=12, souls=10, poise=12, spd=1.3, wake=150, dmg=16),
    "korppi":   dict(hp=16, w=12, h=9, souls=8, poise=8, spd=1.1, wake=140, fly=True, dmg=10),
    "jousi":    dict(hp=26, w=10, h=20, souls=14, poise=14, spd=0.7, wake=170, dmg=14),
    "hukkunut": dict(hp=90, w=14, h=24, souls=25, poise=45, spd=0.55, wake=120, dmg=30),
    "virvatuli": dict(hp=20, w=10, h=10, souls=18, poise=6, spd=0.7, wake=150, fly=True, dmg=14),
    "nakki":    dict(hp=30, w=12, h=12, souls=20, poise=30, spd=1.0, wake=70, dmg=18),
    "haamu":    dict(hp=110, w=12, h=26, souls=40, poise=50, spd=0.8, wake=140, dmg=32),
    "henki":    dict(hp=40, w=12, h=24, souls=35, poise=10, spd=0.7, wake=170, fly=True, dmg=18),
    "joutsen":  dict(hp=40, w=16, h=10, souls=28, poise=14, spd=1.0, wake=160, fly=True, dmg=18),
    "hiisi":    dict(hp=800, w=26, h=44, souls=900, poise=9999, spd=1.0, wake=0, dmg=28),
    "turso":    dict(hp=800, w=22, h=22, souls=1800, poise=9999, spd=1.0, wake=0, dmg=40, fly=True),
    "louhi":    dict(hp=2800, w=88, h=94, souls=8000, poise=9999, spd=1.0, wake=0, dmg=52, fly=True),
    "tytti":    dict(hp=1500, w=14, h=34, souls=4000, poise=9999, spd=1.0, wake=0, dmg=36, fly=True),
}
FLYERS = ("korppi", "virvatuli", "henki", "joutsen")

class Enemy(Body):
    boss = False
    def __init__(s, g, kind, x, y, sid=None):
        sp = ESPEC[kind]
        Body.__init__(s, x, y, sp["w"], sp["h"])
        s.g = g; s.kind = kind; s.sp = sp; s.hp = s.maxhp = float(sp["hp"]); s.souls = sp["souls"]; s.fly = sp.get("fly", False)
        cycle = int((g.save or {}).get("ng") or 0) if getattr(g, "save", None) else 0
        if cycle:
            s.hp = s.maxhp = s.maxhp * (1.0 + 0.12 * cycle)
        s.hx, s.hy = x, y; s.face = random.choice((-1, 1)); s.anim = "idle"; s.t = random.randint(0, 99); s.stun = 0; s.flash = 0
        s.poise = s.poise_max = sp["poise"]; s.poise_t = 0; s.armor = False; s.dead = False; s.dt = 0; s.atk = None; s.warn = 0; s.warn_t = 0
        s.kx = 0.0; s.vuln = 0; s.alert = 0; s.invuln = False; s.hidden = False; s.sid = sid; s.gen = None; s.stag_cd = 0; s.last_hit = 0
        s.speed = sp["spd"]
    # ----- helpers for the AI -----
    def target(s):
        g = s.g; t = g.nearest_player(s.x, s.y - 10)
        if t is None: return None
        dx = abs(t.x - s.x); dy = abs(t.y - s.y)
        if s.alert > 0: s.alert -= 1
        if dx < s.sp["wake"] and dy < 60 and g.los(s.x, s.y - s.h * 0.6, t.x, t.y - 9):
            s.alert = 240
        if s.alert > 0 and abs(s.x - s.hx) < 230 and dx < 260: return t
        return None
    def see(s, t): s.face = 1 if t.x >= s.x else -1
    def can_step(s, d):
        wd = s.g.wd
        nx = s.x + d * (s.w / 2 + 4); tx = int(nx // TILE)
        ty_f = int((s.y + 2) // TILE)
        if wd.solid(tx, int((s.y - 4) // TILE)) or wd.solid(tx, int((s.y - 12) // TILE)): return False
        for k in range(0, 3):
            tt = wd.tile(tx, ty_f + k)
            if tt in (THORN, WATER): return False
            if tt in (SOLID, PLAT) or (tt == LADDER and wd.tile(tx, ty_f + k - 1) != LADDER): return True if k < 2 else False
        return False
    def step(s, d, spd=None):
        if spd is None: spd = s.speed
        s.vx = d * spd * D()["spd"] if s.can_step(d) else 0.0
    def idle(s, n):
        s.vx = 0
        for _ in range(n):
            s.anim = "idle"; s.vx = 0; yield
    def patrol(s, n):
        d = random.choice((-1, 1))
        if abs(s.x - s.hx) > 60: d = 1 if s.hx > s.x else -1
        s.face = d
        for _ in range(n):
            if s.target(): break
            s.anim = "walk"
            s.vx = d * s.speed * 0.5 * D()["spd"] if s.can_step(d) and abs(s.x + d * 8 - s.hx) < 70 else 0.0
            yield
        s.vx = 0; s.anim = "idle"
        for _ in range(random.randint(20, 60)):
            if s.target(): break
            yield
    def attack(s, anim_w, tel, anim_a, act, rec, rel, dmg, kb=2.0, tags=(), lunge=0.0, poise=20, snd="swing", kbu=0.0, armor=False, anim_r="idle", vy=0.0, until_ground=False, hook=None):
        n = tele(tel); s.armor = armor
        s.anim = anim_w
        for i in range(n):
            s.vx = 0; s.warn = n - i; s.warn_t = i; yield
        s.warn = 0
        s.anim = anim_a; s.atk = Atk(rel, dmg * D()["dmg"], kb, tags, poise, kbu); sfx(snd, 0.8)
        if vy: s.vy = vy; s.on_ground = False
        if hook: hook()
        i = 0
        while i < act or (until_ground and not s.on_ground and i < act + 40):
            s.vx = lunge * s.face * D()["spd"]; i += 1; yield
        s.atk = None; s.vx = 0; s.armor = False; s.anim = anim_r
        for _ in range(rec): yield
    # ----- core -----
    def hurt_rect(s): return (s.x - s.w / 2, s.y - s.h, s.w, s.h)
    def mult(s): return D()["hp"] * s.g.coop_mult(s.boss)
    def take(s, dmg, kb=0.0, poise=10, pl=None, tags=(), kbu=0.0):
        if s.dead or s.invuln or s.hidden: return False
        g = s.g
        if s.vuln > 0: dmg *= 2.2; tags = set(tags) | {"crit"}
        real = dmg / s.mult(); s.hp -= real; s.flash = 4; s.last_hit = 0
        if pl is not None: pl.dealt = getattr(pl, "dealt", 0) + 1
        g.dnum(s.x, s.y - s.h - 2, int(round(dmg)), (255, 230, 120) if "crit" in tags else (255, 255, 255))
        g.parts.burst(s.x, s.y - s.h * 0.55, (255, 230, 200) if not s.boss else (255, 180, 140), 6, 1.6, 14)
        sfx("hit2" if "heavy" in tags or "crit" in tags else "hit", 0.8)
        g.hitstop = max(g.hitstop, 5 if "heavy" in tags or "crit" in tags else 3)
        if s.alert < 200: s.alert = 240
        if s.hp <= 0: s.die(pl); return True
        s.poise -= poise; s.poise_t = 100
        if s.stun <= 0 and not s.boss and (s.poise <= 0) and not s.armor:
            s.stun = 16 if "heavy" not in tags else 24; s.poise = s.poise_max; s.atk = None; s.warn = 0; s.gen = None; s.anim = "hurt"
        if kb and not (s.boss or s.armor): s.kx = kb * (1.0 if not s.fly else 0.7)
        if kbu and not (s.boss or s.armor) and not s.fly: s.vy = -kbu; s.on_ground = False
        return True
    def stagger(s, n=70):
        if s.stag_cd > 0 or s.dead: return
        s.stun = n; s.vuln = n; s.atk = None; s.warn = 0; s.gen = None; s.anim = "hurt"; s.armor = False; s.stag_cd = 240 if s.boss else 0
        s.g.parts.burst(s.x, s.y - s.h * 0.6, (255, 240, 160), 14, 2.2, 20)
    def die(s, pl):
        s.dead = True; s.dt = 0; s.atk = None; s.anim = "die"; s.warn = 0
        g = s.g
        g.parts.burst(s.x, s.y - s.h * 0.5, (255, 255, 255) if not s.fly else (180, 255, 240), 14, 2.0, 26, 1, 0.05, 0.6)
        sfx("edie", 0.9)
        g.give_souls(int(s.souls * D()["souls"]), s.x, s.y - s.h)
        g.on_kill(s)
    def brain(s): raise NotImplementedError
    def update(s):
        g = s.g; s.t += 1; s.poise_t -= 1; s.last_hit += 1
        if s.flash > 0: s.flash -= 1
        if s.stag_cd > 0: s.stag_cd -= 1
        if s.poise_t <= 0: s.poise = s.poise_max
        if s.dead:
            s.dt += 1; s.vx = 0
            if not s.fly and not s.on_ground: s.vy = min(MAX_FALL, s.vy + GRAV); move_body(g.wd, s)
            return
        if s.vuln > 0: s.vuln -= 1
        if s.stun > 0:
            s.stun -= 1; s.vx = 0
            if s.stun == 0: s.anim = "idle"
        else:
            if s.gen is None: s.gen = s.brain()
            try: next(s.gen)
            except StopIteration: s.gen = None
        if s.atk: s.atk.t += 1
        # physics
        vx0 = s.vx; s.vx = vx0 + s.kx
        if not s.fly: s.vy = min(MAX_FALL, s.vy + GRAV)
        move_body(g.wd, s)
        if s.wall: s.kx = 0.0
        s.vx = vx0; s.kx *= 0.82
        if abs(s.kx) < 0.05: s.kx = 0.0
        if s.vx and s.stun <= 0 and not s.atk and abs(s.vx) > 0.05: s.face = 1 if s.vx > 0 else -1
        if s.y > ROWS * TILE - 20 or (not s.fly and hazard_at(g.wd, s) and not s.kind == "nakki"):
            s.hp = 0; s.dead = True; s.dt = 30; s.souls = 0; g.parts.burst(s.x, s.y, (150, 200, 255), 8, 1.2, 16, 1, 0.1, 1.5); sfx("splash", 0.5)
    # ----- drawing -----
    def sprite(s):
        a = s.anim
        if a == "walk" and abs(s.vx) < 0.05: a = "idle"
        t = (s.t // (5 if a != "walk" else 6)) % 8
        if s.dead: a = "die"; t = 0
        fl = s.flash > 0
        return enemy_frame(s.kind, a, t, s.face < 0, fl)
    def draw(s, surf, cx, cy):
        if isinstance(s, WaterBoss):
            spr = newboss_frame(s.key, getattr(s, "vb", "idle"), max(1, min(3, round(s.phase))), s.t)
            if s.face > 0:
                fk = ("flip", s.key, getattr(s, "vb", "idle"), max(1, min(3, round(s.phase))), s.t % 4)
                if fk not in _BSPR: _BSPR[fk] = pygame.transform.flip(spr, True, False)
                spr = _BSPR[fk]
            bx = int(s.x - cx - spr.get_width() // 2)
            by = int(s.y - cy - spr.get_height())
            surf.blit(spr, (bx, by))
            if s.warn > 0 and s.warn_t < 14:
                pygame.draw.rect(surf, (255, 60, 50), (int(s.x - cx) - 1, by - 8, 3, 5))
                pygame.draw.rect(surf, (255, 60, 50), (int(s.x - cx) - 1, by - 2, 3, 2))
            return
        if s.hidden: return
        spr = s.sprite(); w, h = spr.get_size()
        x = int(s.x - cx); y = int(s.y - cy)
        if s.fly: bx, by = x - w // 2, y - h // 2 - int(s.h / 2) + (int(math.sin(s.t * 0.1) * 2) if not s.dead else 0)
        else: bx, by = x - w // 2, y - h + 2
        if s.dead:
            if s.dt > 34: return
            spr = spr.copy(); spr.set_alpha(max(0, 255 - s.dt * 8))
        surf.blit(spr, (bx, by))
        if s.warn > 0:
            if s.warn_t < 12:
                px = x; py = by - 6
                pygame.draw.rect(surf, (255, 60, 50), (px - 1, py - 8, 3, 5)); pygame.draw.rect(surf, (255, 60, 50), (px - 1, py - 2, 3, 2))
                pygame.draw.rect(surf, (255, 230, 200), (px, py - 7, 1, 3))
            if s.warn <= 4:
                g2 = spr.copy(); g2.fill((100, 80, 20, 0), special_flags=pygame.BLEND_RGB_ADD); surf.blit(g2, (bx, by))
        if not s.dead and s.vuln > 0 and (s.t // 4) % 2 == 0: surf.fill((255, 240, 140), (x - 1, by - 3, 3, 3))
        if s.atk and DEBUG_BOXES:
            r = s.atk.rect(s.x, s.y, s.face); pygame.draw.rect(surf, (255, 0, 0), (r[0] - cx, r[1] - cy, r[2], r[3]), 1)
DEBUG_BOXES = False
