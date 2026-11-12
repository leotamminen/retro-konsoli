
# ---------------- bosses ----------------
class Boss(Enemy):
    boss = True
    def __init__(s, g, key, x, y):
        Enemy.__init__(s, g, key, x, y)
        s.key = key; s.arena = ARENAS[key]; s.engaged = False; s.phase = 1; s.invuln = True; s.armor = True
        s.L = (s.arena["x0"] + 1) * TILE + 12; s.R = s.arena["x1"] * TILE - 12; s.gy = s.arena["ground"] * TILE
        s.face = -1; s.trans_t = 0; s.death_t = 0; s.shown_bar = 0.0
    def engage(s):
        if s.engaged: return
        s.engaged = True; s.gen = None
    def mid_target(s):
        return s.g.nearest_player(s.x, s.y - 10)
    def trans(s):
        s.atk = None; s.warn = 0; s.invuln = True; s.armor = True; s.anim = "roar"; s.vx = 0
        sfx("roar", 1.0); s.g.shake(5, 40)
        for i in range(80):
            s.trans_t = i; s.vx = 0
            if i % 6 == 0: s.g.parts.burst(s.x, s.y - s.h * 0.5, (255, 120, 60), 4, 2.0, 24, 1, 0.0)
            yield
        s.phase = 2; s.invuln = False; s.anim = "idle"
    def die(s, pl):
        s.dead = True; s.gen = None; s.dt = 0; s.atk = None; s.warn = 0; s.anim = "die"; s.invuln = True
        s.g.give_souls(int(s.souls * D()["souls"]), s.x, s.y - s.h)
        s.g.on_boss_dead(s)
    def update(s):
        g = s.g; s.t += 1
        if s.flash > 0: s.flash -= 1
        if s.stag_cd > 0: s.stag_cd -= 1
        if s.vuln > 0: s.vuln -= 1
        if s.dead:
            s.dt += 1
            if s.dt % 5 == 0 and s.dt < 120:
                g.parts.burst(s.x + random.randint(-14, 14), s.y - random.randint(0, int(s.h)), (255, 230, 180), 5, 2.0, 22, 2, 0.02)
                if s.dt % 15 == 0: sfx("boom", 0.6); g.shake(3, 6)
            self_phys = getattr(s, "dead_phys", None)
            if self_phys: self_phys()
            return
        if not s.engaged: s.anim = "idle"; self_idle = getattr(s, "idle_pose", None); self_idle() if self_idle else None; return
        if s.phase == 1 and s.hp <= s.maxhp * 0.5 and s.key!="louhi":
            s.phase = 1.5; s.stun = 0; s.gen = s.trans()
        if s.stun > 0:
            s.stun -= 1; s.vx = 0
            if s.stun == 0 and s.anim == "stagger": s.anim = "idle"
        else:
            if s.gen is None: s.gen = s.brain()
            try: next(s.gen)
            except StopIteration:
                s.gen = None
        if s.atk: s.atk.t += 1
        s.physics()
    def physics(s): pass
    def take(s, dmg, kb=0.0, poise=10, pl=None, tags=(), kbu=0.0):
        return Enemy.take(s, dmg, 0.0, poise, pl, tags, 0.0)
    def pick(s, opts):
        """weighted choice, never the same attack three times in a row"""
        last = getattr(s, "_last", [])
        pool = [(n, w) for n, w in opts if not (len(last) >= 2 and last[-1] == last[-2] == n)]
        r = random.random() * sum(w for _, w in pool)
        for n, w in pool:
            r -= w
            if r <= 0: break
        s._last = (last + [n])[-3:]
        return n

class Hiisi(Boss):
    def __init__(s, g, x, y): Boss.__init__(s, g, "hiisi", x, y)
    def physics(s):
        g = s.g
        vx0 = s.vx; s.vy = min(MAX_FALL, s.vy + GRAV); move_body(g.wd, s)
        s.x = max(s.L, min(s.R, s.x)); s.vx = vx0
        if s.vx and abs(s.vx) > 0.05 and not s.atk: s.face = 1 if s.vx > 0 else -1
    def dead_phys(s):
        s.vy = min(MAX_FALL, s.vy + GRAV); move_body(s.g.wd, s)
    def spd(s): return (1.0 if s.phase < 2 else 1.25) * D()["spd"]
    def brain(s):
        if not getattr(s, "intro_done", False):
            s.intro_done = True; s.invuln = True; s.anim = "roar"; sfx("roar", 1.0); s.g.shake(4, 50)
            for i in range(90): s.vx = 0; yield
            s.invuln = False; s.armor = True
        while True:
            t = s.mid_target()
            if t is None: s.anim = "idle"; yield; continue
            s.see(t); ad = abs(t.x - s.x)
            opts = [("slam", 0.4), ("sweep", 0.35), ("charge", 0.25)]
            if s.phase >= 2: opts = [("slam", 0.25), ("sweep", 0.2), ("charge", 0.2), ("rocks", 0.2), ("combo", 0.25)]
            if ad > 150: opts = [("charge", 0.6), ("rocks" if s.phase >= 2 else "slam", 0.4)]
            act = s.pick(opts)
            if act in ("slam", "sweep", "combo") and ad > 62:
                for _ in range(100):
                    t = s.mid_target(); s.see(t); s.anim = "walk"; s.vx = s.face * 0.9 * s.spd()
                    if abs(t.x - s.x) < 56: break
                    yield
                s.vx = 0
            yield from getattr(s, "a_" + act)()
            yield from s.idle(rest(34 if s.phase < 2 else 18))
    def a_slam(s):
        def hook():
            s.g.shake(4, 10); s.g.parts.burst(s.x + s.face * 38, s.y, (160, 140, 120), 12, 2.2, 22, 2, 0.1, 1.0)
            for d in (-1, 1):
                s.g.projs.append(Proj("wave", s.x + s.face * 38 + d * 8, s.y, d * 1.8 * s.spd(), 0, 22 * D()["dmg"], 12, 10, tags=("heavy",), life=130, col=(190, 160, 120)))
        yield from s.attack("slam_w", 46, "slam", 8, 44, (10, -34, 46, 34), s.sp["dmg"] * 1.05, 3.6, ("parry", "heavy"), snd="boom", hook=hook, armor=True)
    def a_sweep(s):
        yield from s.attack("sweep_w", 36, "sweep", 12, 34, (-6, -16, 70, 16), s.sp["dmg"] * 0.85, 3.2, ("parry",), snd="swing2", armor=True)
    def a_combo(s):
        yield from s.a_slam(); s.see(s.mid_target()) if s.mid_target() else None
        yield from s.attack("sweep_w", 20, "sweep", 12, 30, (-6, -16, 70, 16), s.sp["dmg"] * 0.85, 3.2, ("parry",), snd="swing2", armor=True)
    def a_charge(s):
        t = s.mid_target(); s.see(t)
        n = tele(38); s.anim = "charge_w"
        for i in range(n):
            s.vx = 0; s.warn = n - i; s.warn_t = i
            if i % 5 == 0: s.g.parts.burst(s.x, s.y, (160, 140, 120), 3, 1.0, 14, 1, 0.05, 0.6)
            yield
        s.warn = 0; s.anim = "charge"; sfx("roar", 0.8)
        s.atk = Atk((-14, -42, 28, 42), s.sp["dmg"] * D()["dmg"], 4.0, ("heavy",), 40)
        crashed = False
        for i in range(80):
            s.vx = s.face * 3.4 * s.spd()
            if i % 4 == 0: s.g.parts.burst(s.x - s.face * 10, s.y, (150, 130, 110), 2, 1.0, 14, 1, 0.05, 0.6)
            if s.wall or abs(s.x - (s.R if s.face > 0 else s.L)) < 3: crashed = True; break
            yield
        s.atk = None; s.vx = 0
        if crashed:
            s.g.shake(5, 14); sfx("boom", 0.9); s.g.parts.burst(s.x + s.face * 14, s.y - 20, (160, 140, 120), 18, 2.4, 26, 2, 0.1, 1.2)
            s.anim = "stagger"; s.stun = 78; s.vuln = 78; s.armor = False
            yield
            s.armor = True
    def a_rocks(s):
        s.anim = "rock"; n = tele(44); s.vx = 0
        for i in range(n): s.warn = n - i; s.warn_t = i; yield
        s.warn = 0; s.anim = "slam"; sfx("roar", 0.7)
        t = s.mid_target()
        xs = [t.x if t else s.x]
        for k in range(5): xs.append(random.uniform(s.L + 10, s.R - 10))
        for k, x in enumerate(xs):
            s.g.zones.append(Zone(x, s.gy, 20, 150, tele(48) + k * 9, 6, 30 * D()["dmg"], "rock", 2.8))
        for _ in range(30): yield
    def draw(s, surf, cx, cy):
        if s.dead and s.dt > 150: return
        pose = s.anim if s.anim in ("idle", "walk", "slam_w", "slam", "sweep_w", "sweep", "charge_w", "charge", "roar", "stagger", "hurt", "die", "rock") else "idle"
        if s.dead: pose = "die"
        if s.anim == "walk" and abs(s.vx) < 0.05: pose = "idle"
        spr = hiisi_frame(pose, (s.t // 6) % 6 if pose in ("walk", "charge") else (s.t // 12) % 2 * 8, s.face < 0, s.flash > 0, s.phase >= 2)
        w, h = spr.get_size(); x = int(s.x - cx); y = int(s.y - cy)
        if s.dead: spr = spr.copy(); spr.set_alpha(max(0, 255 - max(0, s.dt - 80) * 4))
        surf.blit(spr, (x - w // 2, y - h + 3))
        if s.warn > 0 and s.warn_t < 12:
            pygame.draw.rect(surf, (255, 60, 50), (x - 1, y - 66, 3, 5)); pygame.draw.rect(surf, (255, 60, 50), (x - 1, y - 60, 3, 2))
        if s.warn > 0 and s.warn <= 5:
            g2 = spr.copy(); g2.fill((90, 60, 10, 0), special_flags=pygame.BLEND_RGB_ADD); surf.blit(g2, (x - w // 2, y - h + 3))

class Turso(Boss):
    def __init__(s, g, x, y):
        Boss.__init__(s, g, "turso", x, y)
        s.bx = s.R + 4; s.by = s.gy + 10
        s.hx_, s.hy_ = s.bx - 56, s.gy - 74
        s.x, s.y = s.hx_, s.hy_ + 11; s.mouth = 0; s.face = -1
    def idle_pose(s):
        s.x = s.hx_ + math.sin(s.t * 0.04) * 4; s.y = s.hy_ + 11 + math.sin(s.t * 0.06) * 3
    def physics(s):
        if s.anim == "idle" and not s.atk: s.idle_pose()
        if s.wall: s.wall = 0
    def spd(s): return (1.0 if s.phase < 2 else 1.25) * D()["spd"]
    def move_head(s, tx, ty, n, mouth=None):
        sx, sy = s.x, s.y - 11
        for i in range(1, n + 1):
            f = i / n; f = f * f * (3 - 2 * f)
            s.x = sx + (tx - sx) * f; s.y = sy + (ty - sy) * f + 11
            if mouth is not None: s.mouth = mouth
            yield
    def spit_land_fn(s): pass
    def brain(s):
        if not getattr(s, "intro_done", False):
            s.intro_done = True; s.invuln = True; sfx("roar", 1.0); s.g.shake(4, 50); s.mouth = 1
            for i in range(90): s.idle_pose(); yield
            s.mouth = 0; s.invuln = False
        while True:
            s.anim = "idle"; s.mouth = 0
            for i in range(rest(50 if s.phase < 2 else 30)):
                s.idle_pose(); yield
            opts = [("lunge", 0.4), ("geyser", 0.3), ("wave", 0.3)]
            if s.phase >= 2: opts = [("lunge", 0.25), ("geyser", 0.2), ("wave", 0.15), ("spit", 0.25), ("dwave", 0.15)]
            yield from getattr(s, "a_" + s.pick(opts))()
    def a_lunge(s):
        t = s.mid_target()
        tx = max(s.L + 20, min(s.R - 30, t.x if t else s.x)); n = tele(42)
        z = Zone(tx, s.gy, 30, 6, n, 0, 0, "warn"); s.g.zones.append(z); s.anim = "windup"
        sfx("warn", 0.8)
        yield from s.move_head(min(s.R - 10, tx + 70), s.gy - 96, n // 2, 0)
        for i in range(n - n // 2): s.warn = n - n // 2 - i; s.warn_t = i; s.x += random.uniform(-.3, .3); s.mouth = 1 if i > 4 else 0; yield
        s.warn = 0; s.anim = "attack"; s.mouth = 2
        s.atk = Atk((-15, -26, 30, 30), s.sp["dmg"] * D()["dmg"], 3.5, ("heavy",), 30); sfx("roar", 0.7)
        yield from s.move_head(tx, s.gy - 12, 9, 2)
        for i in range(8): yield
        s.atk = None; s.g.shake(3, 8); s.g.parts.burst(s.x, s.gy, (150, 200, 255), 10, 2.0, 20, 1, 0.1, 1.5); sfx("splash", 0.8)
        s.mouth = 1
        s.vuln = 0
        for i in range(tele(96)): s.y += 0; s.x += math.sin(i * 0.5) * 0.2; yield     # stuck: the opening
        yield from s.move_head(s.hx_, s.hy_, 36, 0)
    def a_geyser(s):
        t = s.mid_target(); s.anim = "windup"; s.mouth = 1; sfx("roar", 0.7)
        px = t.x if t else (s.L + s.R) / 2
        xs = [px, px - 46, px + 46] + ([px - 92, px + 92] if s.phase >= 2 else [])
        d0 = tele(52)
        for k, x in enumerate(xs):
            x = max(s.L + 10, min(s.R - 10, x))
            s.g.zones.append(Zone(x, s.gy, 22, 96, d0 + k * 6, 16, s.sp["dmg"] * 0.8 * D()["dmg"], "geyser", 3.0))
        for i in range(d0 + 40): s.idle_pose(); s.warn = 0; yield
        s.mouth = 0
    def a_wave(s):
        s.anim = "windup"; n = tele(34)
        yield from s.move_head(s.hx_ + 6, s.gy - 52, n // 2, 1)
        for i in range(n - n // 2): s.warn = n - n // 2 - i; s.warn_t = i; yield
        s.warn = 0; s.anim = "attack"; s.mouth = 2
        yield from s.move_head(s.bx - 22, s.gy - 14, 8, 2)
        s.g.shake(4, 10); sfx("boom", 0.9)
        s.g.projs.append(Proj("wave", s.bx - 24, s.gy, -2.0 * s.spd(), 0, 24 * D()["dmg"], 14, 12, tags=("heavy",), life=200, col=(120, 200, 255)))
        for i in range(30): yield
        yield from s.move_head(s.hx_, s.hy_, 30, 0)
    def a_dwave(s):
        s.anim = "windup"; n = tele(30)
        yield from s.move_head(s.hx_ + 6, s.gy - 52, n // 2, 1)
        for i in range(n - n // 2): s.warn = n - n // 2 - i; s.warn_t = i; yield
        s.warn = 0; s.mouth = 2
        yield from s.move_head(s.bx - 22, s.gy - 14, 7, 2)
        s.g.shake(4, 10); sfx("boom", 0.9)
        s.g.projs.append(Proj("wave", s.bx - 24, s.gy, -2.0 * s.spd(), 0, 24 * D()["dmg"], 14, 12, tags=("heavy",), life=200, col=(120, 200, 255)))
        for i in range(52): yield
        s.g.shake(4, 10); sfx("boom", 0.9)
        s.g.projs.append(Proj("wave", s.bx - 24, s.gy, -2.0 * s.spd(), 0, 24 * D()["dmg"], 14, 12, tags=("heavy",), life=200, col=(120, 200, 255)))
        for i in range(30): yield
        yield from s.move_head(s.hx_, s.hy_, 30, 0)
    def a_spit(s):
        s.anim = "windup"; n = tele(34); s.mouth = 1
        yield from s.move_head(s.hx_ - 20, s.gy - 86, n // 2, 1)
        for i in range(n - n // 2): s.warn = n - n // 2 - i; s.warn_t = i; yield
        s.warn = 0; s.mouth = 2; sfx("bow", 0.9)
        t = s.mid_target(); tx = t.x if t else s.x - 80
        for k in range(3):
            dx = tx + (k - 1) * 44 - s.x; vx = max(-2.4, min(2.4, dx / 62.0))
            s.g.projs.append(Proj("spit", s.x, s.y - 11, vx, -3.4, 22 * D()["dmg"], 8, 8, tags=("parry", "magic"), life=200, grav=0.11, col=(130, 230, 80)))
        for i in range(40): yield
        yield from s.move_head(s.hx_, s.hy_, 30, 0)
    def draw(s, surf, cx, cy):
        if s.dead and s.dt > 130: return
        hx = int(s.x - cx); hy = int(s.y - 11 - cy)
        if s.dead: hy += s.dt // 2
        turso_draw(surf, 0, 0, int(s.bx - cx), int(s.by - cy), hx, hy, s.t, s.mouth, s.flash > 0, s.phase >= 2)
        if s.warn > 0 and s.warn_t < 12:
            pygame.draw.rect(surf, (255, 60, 50), (hx - 1, hy - 26, 3, 5)); pygame.draw.rect(surf, (255, 60, 50), (hx - 1, hy - 20, 3, 2))
    def hurt_rect(s): return (s.x - 11, s.y - 22, 22, 22)

class Tytti(Boss):
    def __init__(s, g, x, y):
        Boss.__init__(s, g, "tytti", x, y)
        s.fy = s.gy - 8; s.alpha = 255
    def idle_pose(s): s.y = s.fy + math.sin(s.t * 0.06) * 3
    def physics(s):
        s.x = max(s.L, min(s.R, s.x + s.vx)); s.y += s.vy
        if not s.atk and s.anim == "idle": s.vy = 0
    def spd(s): return (1.0 if s.phase < 2 else 1.3) * D()["spd"]
    def brain(s):
        if not getattr(s, "intro_done", False):
            s.intro_done = True; s.invuln = True; s.anim = "cast"; sfx("roar", 0.9); s.g.shake(3, 40)
            for i in range(90): yield
            s.invuln = False
        while True:
            s.anim = "idle"; s.hidden = False; s.invuln = False; s.y = s.fy
            for i in range(rest(54 if s.phase < 2 else 34)): s.idle_pose(); t = s.mid_target(); s.see(t) if t else None; yield
            opts = [("tslash", 0.45), ("orbs", 0.3), ("wave", 0.25)]
            if s.phase >= 2: opts = [("tslash", 0.2), ("orbs", 0.15), ("wave", 0.12), ("beams", 0.3), ("tcombo", 0.23)]
            yield from getattr(s, "a_" + s.pick(opts))()
    def vanish(s, n=14):
        s.invuln = True
        for i in range(n): s.alpha = 255 - int(255 * i / n); s.vx = 0; yield
        s.hidden = True
    def appear_at(s, x, n=26):
        s.x = max(s.L + 16, min(s.R - 16, x)); s.y = s.fy; s.hidden = True
        s.g.zones.append(Zone(s.x, s.gy, 22, 36, n, 0, 0, "ghost"))
        for i in range(n): yield
        s.hidden = False; s.invuln = False; s.alpha = 255; sfx("warn", 0.7); s.g.parts.burst(s.x, s.y - 16, (200, 160, 255), 10, 1.6, 18, 1, 0)
    def a_tslash(s, quick=False):
        t = s.mid_target()
        side = random.choice((-1, 1)); tx = (t.x if t else s.x) + side * 44
        if tx < s.L + 20 or tx > s.R - 20: tx = (t.x if t else s.x) - side * 44
        yield from s.vanish()
        yield from s.appear_at(tx, tele(18 if quick else 26))
        t = s.mid_target()
        if t: s.see(t)
        yield from s.attack("slash_w", 22 if quick else 28, "slash", 10, 30 if not quick else 12, (6, -38, 58, 40), s.sp["dmg"], 3.4, ("parry",), snd="swing2", armor=True)
    def a_tcombo(s):
        yield from s.a_tslash(False); yield from s.a_tslash(True)
    def a_orbs(s):
        s.anim = "cast"; n = tele(34); t = s.mid_target()
        for i in range(n): s.warn = n - i; s.warn_t = i; s.see(t) if t else None; yield
        s.warn = 0; sfx("orb", 0.9)
        t = s.mid_target(); base = math.atan2((t.y - 12 - (s.y - 20)) if t else 0, (t.x - s.x) if t else s.face)
        cnt = 3 if s.phase < 2 else 5
        for k in range(cnt):
            a = base + (k - (cnt - 1) / 2) * 0.32
            s.g.projs.append(Proj("orb", s.x + s.face * 8, s.y - 22, math.cos(a) * 1.5 * s.spd(), math.sin(a) * 1.5 * s.spd(), 22 * D()["dmg"], 8, 8, tags=("parry", "magic"), life=260, col=(220, 120, 255), homing=0.012, hp=1))
        for _ in range(26): yield
    def a_wave(s):
        s.anim = "cast"; n = tele(30)
        for i in range(n): s.warn = n - i; s.warn_t = i; yield
        s.warn = 0; s.anim = "slash"; s.g.shake(3, 8); sfx("boom", 0.7)
        for d in (-1, 1):
            s.g.projs.append(Proj("wave", s.x + d * 8, s.gy, d * 1.9 * s.spd(), 0, 26 * D()["dmg"], 12, 12, tags=("heavy",), life=170, col=(200, 120, 255)))
        for _ in range(34): yield
    def a_beams(s):
        s.anim = "beam"; n = tele(60); s.vx = 0
        t = s.mid_target(); px = t.x if t else s.x
        for vol in range(2):
            d0 = n if vol == 0 else 0
            xs = [s.L + 6 + i * 30 + (15 if vol else 0) for i in range(int((s.R - s.L) // 30))]
            gapx = (t.x if t else px) if vol == 1 else px
            for x in xs:
                if abs(x - gapx) < (26 if vol == 0 else 26): continue
                s.g.zones.append(Zone(x, s.gy, 14, 150, (tele(58) if vol == 0 else tele(58) + 62), 14, 40 * D()["dmg"], "beam", 3.0))
            if vol == 0: sfx("warn", 0.8)
            for i in range(60 if vol == 0 else 30): s.warn = 0; yield
        for _ in range(60): yield
    def draw(s, surf, cx, cy):
        if s.hidden: return
        pose = s.anim if s.anim in ("idle", "slash_w", "slash", "cast", "beam", "stagger", "hurt", "die") else "idle"
        if s.dead: pose = "die"
        spr = tytti_frame(pose, (s.t // 6) % 6 if pose == "idle" else 0, s.face < 0, s.flash > 0, s.phase >= 2)
        w, h = spr.get_size(); x = int(s.x - cx); y = int(s.y - cy)
        if s.alpha < 255 or s.dead:
            spr = spr.copy(); spr.set_alpha(s.alpha if not s.dead else max(0, 255 - s.dt * 2))
        surf.blit(spr, (x - w // 2, y - h + 8))
        if s.warn > 0 and s.warn_t < 12:
            pygame.draw.rect(surf, (255, 60, 50), (x - 1, y - 52, 3, 5)); pygame.draw.rect(surf, (255, 60, 50), (x - 1, y - 46, 3, 2))
    def dead_phys(s):
        s.y = min(s.gy - 2, s.y + 0.3)

BOSS_CLS = {"hiisi": Hiisi, "turso": Turso, "tytti": Tytti}

class Louhi(Boss):
    """Final secret encounter. Large floating eagle; scripted lanes leave fair escape space."""
    def __init__(s,g,x,y):
        Boss.__init__(s,g,"louhi",x,y);s.x=(s.arena["x0"]+14)*16;s.y=s.gy-65;s.fy=s.y;s.darkness=0
    def hurt_rect(s):
        ground=s.y>=s.gy-8
        return (s.x-43,max(s.y-s.h+6,s.gy-150),86,s.gy-max(s.y-s.h+6,s.gy-150)+4)
    def update(s):
        if not s.dead and s.phase in (1,2) and s.hp<=s.maxhp*(.66 if s.phase==1 else .33):
            target=1.5 if s.phase==1 else 2.5;s.phase=target;s.stun=0;s.gen=s.trans(2 if target==1.5 else 3);s.darkness=0.35
        Boss.update(s)
    def physics(s):
        s.x=max(s.L+50,min(s.R-50,s.x+s.vx));s.y=max(s.gy-140,min(s.gy-9,s.y+s.vy));s.atk=None if s.atk and s.atk.t>16 else s.atk
    def trans(s,phase):
        s.atk=None;s.warn=0;s.invuln=True;s.anim="roar";s.vx=s.vy=0;s.g.shake(7,35);sfx("roar",1)
        for i in range(100):
            s.trans_t=i
            if i%7==0:s.g.parts.burst(s.x,s.y-48,(106,139,218),8,2.1,28)
            yield
        s.phase=phase;s.invuln=False;s.darkness=phase-1
    def die(s,pl):
        Boss.die(s,pl)
    def brain(s):
        s.invuln=True;s.anim="roar";sfx("roar",1);s.g.shake(7,65)
        for i in range(100):s.fly_hover();s.warn=max(0,45-i) if i<45 else 0;yield
        s.warn=0;s.invuln=False
        while True:
            t=s.mid_target()
            if t is None:yield;continue
            s.see(t);s.fly_hover()
            opts=[("dive",.3),("frost",.3),("gale",.25),("orbs",.15)]
            if s.phase>=2:opts=[("dive",.22),("frost",.2),("light",.3),("minions",.15),("orbs",.13)]
            if s.phase>=3:opts=[("dive",.25),("frost",.2),("light",.2),("gale",.15),("minions",.1),("combo",.1)]
            yield from getattr(s,"a_"+s.pick(opts))()
            for i in range(rest(36 if s.phase==1 else 22 if s.phase==2 else 13)):s.fly_hover();yield
    def fly_hover(s):
        s.vy=math.sin(s.t*.055)*.18;s.vx=math.sin(s.t*.025)*.2;s.anim="idle"
    def a_dive(s):
        t=s.mid_target();tx=t.x if t else s.x;n=tele(48);s.vx=s.vy=0;s.g.shake(2,6)
        for i in range(n):
            s.anim="windup";s.see(t) if t else None;s.warn=n-i;s.warn_t=i;tx=t.x if t else tx
            for x in (tx-16,tx,tx+16):s.g.parts.add(x,s.gy,0,-.3,1,(255,83,69),1)
            yield
        s.warn=0;s.anim="attack";sfx("roar",.9);sx=s.x
        s.atk=Atk((-45,-38,90,58),s.sp["dmg"]*D()["dmg"]*1.15,4.6,("heavy",),14)
        for i in range(10):s.x=sx+(tx-sx)*i/9;s.y=s.gy-65+(s.gy-(s.gy-65))*i/9;yield
        for i in range(14):s.atk=None; yield
        s.atk=None;sfx("boom",1);s.g.shake(8,15)
        for d in (-1,1):s.g.projs.append(Proj("wave",tx+d*5,s.gy,d*2.7*D()["spd"],0,34*D()["dmg"],13,12,tags=("heavy",),life=120,col=(145,188,235)))
        s.vy=0
        for i in range(25):s.y=s.gy;s.x=max(s.L+30,min(s.R-30,s.x));yield
        for i in range(25):s.y=s.gy+(s.gy-65-s.gy)*i/24;s.x=max(s.L+30,min(s.R-30,s.x));yield
    def a_frost(s):
        t=s.mid_target();n=tele(50);s.vx=s.vy=0
        for i in range(n):s.warn=n-i;s.warn_t=i;s.anim="windup";yield
        s.warn=0;s.anim="attack"
        xs=(([t.x] if t else [s.x])+[s.L+25+(s.R-s.L-50)*(.2 if s.phase<3 else .12),s.L+25+(s.R-s.L-50)*.82])
        for j,x in enumerate(xs):s.g.zones.append(Zone(x,s.gy,36,100,tele(48)+j*10,12,38*D()["dmg"],"beam",3))
        for i in range(55):s.fly_hover();yield
    def a_gale(s):
        t=s.mid_target();s.see(t);n=tele(42)
        for i in range(n):s.vx=s.vy=0;s.warn=n-i;s.warn_t=i;s.anim="windup";yield
        s.warn=0;s.anim="attack"
        for j in range(3+(s.phase>=3)):
            for d in (-1,1):s.g.projs.append(Proj("wave",s.x,s.gy-10,d*(2.7+j*.5)*D()["spd"],0,32*D()["dmg"],14,11,tags=("heavy",),life=110,col=(164,199,239)))
            for i in range(12):yield
    def a_orbs(s):
        t=s.mid_target();n=tele(38)
        for i in range(n):s.warn=n-i;s.warn_t=i;s.anim="windup";yield
        s.warn=0;s.anim="attack"
        for j in range(5+(s.phase-1)*2):
            if t:
                dx=t.x-s.x;dy=t.y-12-(s.y-40);ln=max(1,math.hypot(dx,dy));sp=2.0*D()["spd"]
                s.g.projs.append(Proj("orb",s.x-20+j*10,s.y-38,dx/ln*sp,dy/ln*sp,30*D()["dmg"],7,6,tags=("magic","parry"),life=230,col=(144,115,246),homing=.012,hp=1))
            for i in range(7 if s.phase<3 else 4):yield
    def a_light(s):
        s.darkness=2.8;MUSIC.request("louhi"+("3" if s.phase>=3 else "2"));n=tele(60);t=s.mid_target();safe=t.x if t else s.L+60;s.g.shake(3,12)
        for i in range(n):
            s.warn=n-i;s.warn_t=i;s.anim="windup"
            if i%5==0:
                pygame.draw.circle(s.g.canvas,(239,198,103),(int(safe-s.g.cam[0]),int(s.gy-s.g.cam[1]-12)),26,1)
                s.g.parts.burst(safe,s.gy-15,(224,182,88),5,1.5,22)
            yield
        s.warn=0;s.darkness=0;s.anim="attack"
        for j,x in enumerate([s.L+35,s.L+100,s.L+165,s.R-38]):
            if abs(x-safe)>48:s.g.zones.append(Zone(x,s.gy,58,180,tele(38)+j*3,15,40*D()["dmg"],"beam",3))
        for i in range(58):s.fly_hover();yield
    def a_minions(s):
        s.anim="roar";s.g.projs.append(Proj("orb",s.x,s.y-45,0,0,0,0,0,tags=(),life=1,col=(0,0,0)))
        n=2 if s.phase<3 else 3
        for j in range(n):
            x=max(s.L+20,min(s.R-20,s.x+(j-1)*50));e=Mob(s.g,"virvatuli",x,s.gy-32,1000+j+int(s.t));e.sp=dict(hp=24,w=12,h=20,souls=0,poise=0,spd=.4,wake=99999,dmg=25);e.maxhp=e.hp=24;s.g.enemies.append(e)
        s.g.msg(tr("louhi_minions"),(194,171,240))
        for i in range(38):s.fly_hover();yield
    def a_combo(s):
        yield from s.a_dive();yield from s.a_frost()
    def draw(s,surf,cx,cy):
        spr=louhi_frame(s.anim,(s.t//8)%4,s.flash>0,3 if s.phase>=2.5 else 2 if s.phase>=1.5 else 1)
        x=int(s.x-cx-spr.get_width()/2);y=int(s.y-cy-spr.get_height());
        if s.darkness:
            s.g.black.fill((3,3,18));s.g.black.set_alpha(int(64*s.darkness));surf.blit(s.g.black,(0,0))
        surf.blit(spr,(x,y))
BOSS_CLS["louhi"]=Louhi
