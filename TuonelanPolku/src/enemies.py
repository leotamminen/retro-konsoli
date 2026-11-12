
# ---------------- enemy brains ----------------
def _los_walk_chase(e, t, until):
    """Walk toward the target until horizontal distance < until."""
    e.see(t); e.anim = "walk"; e.step(e.face)

class Mob(Enemy):
    def brain(s):
        if s.kind in ("poltto", "merikala", "kutri", "lampi", "rapu", "haaksi", "koralli", "ankkuri", "pylvas"):
            return aquatic_brain(s)
        return getattr(s, "b_" + s.kind)()
    # ---- grounded melee ----
    def b_peikko(s):
        while True:
            t = s.target()
            if t is None: yield from s.patrol(70); continue
            ad = abs(t.x - s.x); s.see(t)
            if ad > 26: s.anim = "walk"; s.step(s.face); yield; continue
            s.vx = 0
            yield from s.attack("windup", 34, "attack", 7, 22, (3, -20, 26, 20), s.sp["dmg"], 2.4, ("parry",), snd="swing", poise=18)
            if random.random() < min(0.75, 0.3 * D()["aggr"]):
                s.see(t); yield from s.attack("windup", 24, "attack", 7, 26, (3, -20, 26, 20), s.sp["dmg"], 2.4, ("parry",), poise=18)
            yield from s.idle(rest(36))
    def b_susi(s):
        while True:
            t = s.target()
            if t is None: yield from s.patrol(60); continue
            ad = abs(t.x - s.x); s.see(t)
            if ad > 78: s.anim = "walk"; s.step(s.face, s.speed * 1.2); yield; continue
            # prowl, then pounce
            for _ in range(random.randint(20, 50)):
                t = s.target()
                if t is None: break
                s.see(t); ad = abs(t.x - s.x)
                s.anim = "walk"
                s.step(-s.face if ad < 44 else s.face, s.speed * 0.5); yield
            t = s.target()
            if t is None: continue
            s.see(t)
            yield from s.attack("windup", 24, "attack", 14, 36, (-4, -13, 28, 13), s.sp["dmg"], 2.6, ("parry",), lunge=3.0, poise=14,
                                snd="roar", vy=-3.0, until_ground=True, anim_r="idle")
            yield from s.idle(rest(18))
    def b_hukkunut(s):
        while True:
            t = s.target()
            if t is None: yield from s.patrol(80); continue
            ad = abs(t.x - s.x); s.see(t)
            if ad > 34: s.anim = "walk"; s.step(s.face); yield; continue
            s.vx = 0
            if random.random() < 0.55:
                yield from s.attack("windup", 38, "attack", 8, 34, (2, -24, 32, 24), s.sp["dmg"], 3.0, ("parry", "heavy"), poise=40, snd="boom", armor=True)
            else:
                yield from s.attack("windup", 26, "attack", 14, 28, (0, -20, 28, 16), s.sp["dmg"] * 0.75, 2.2, ("parry",), lunge=1.6, poise=30, armor=True)
            yield from s.idle(rest(40))
    def b_haamu(s):
        while True:
            t = s.target()
            if t is None: yield from s.patrol(80); continue
            ad = abs(t.x - s.x); s.see(t)
            if ad > 52: s.anim = "walk"; s.step(s.face); yield; continue
            s.vx = 0
            if random.random() < 0.6:
                yield from s.attack("windup", 30, "attack", 9, 32, (4, -21, 44, 7), s.sp["dmg"], 2.6, ("parry",), lunge=2.2, poise=40, snd="swing2", armor=True)
            else:
                yield from s.attack("windup", 40, "attack", 8, 36, (0, -32, 30, 32), s.sp["dmg"] * 1.15, 3.2, ("parry", "heavy"), poise=50, snd="boom", armor=True)
            if random.random() < min(0.5, 0.15 * D()["aggr"]):
                s.see(t); yield from s.attack("windup", 22, "attack", 9, 28, (4, -21, 44, 7), s.sp["dmg"], 2.6, ("parry",), lunge=2.2, poise=40, armor=True)
            yield from s.idle(rest(34))
    # ---- ranged ----
    def b_jousi(s):
        while True:
            t = s.target()
            if t is None: yield from s.patrol(70); continue
            ad = abs(t.x - s.x); s.see(t); dy = abs(t.y - s.y)
            if ad < 64 and s.can_step(-s.face):
                s.anim = "walk"; s.step(-s.face, s.speed * 1.2); yield; continue
            if ad > 200 or dy > 52 or not s.g.los(s.x, s.y - 12, t.x, t.y - 9):
                s.anim = "walk"; s.step(s.face, s.speed * 0.7) if ad > 120 else None; yield; continue
            n = tele(30); s.anim = "windup"
            for i in range(n): s.vx = 0; s.warn = n - i; s.warn_t = i; s.see(t); yield
            s.warn = 0; s.anim = "attack"; sfx("bow", 0.7)
            sp = 3.0 * D()["spd"]; s.g.projs.append(Proj("arrow", s.x + s.face * 8, s.y - 13, s.face * sp, 0.0, s.sp["dmg"] * D()["dmg"], 8, 3, tags=("parry",), life=200, col=(220, 200, 150)))
            for _ in range(12): yield
            s.anim = "idle"
            yield from s.idle(rest(80))
    def b_virvatuli(s):
        yield from s._caster(70, 26, 1.6, "orb", (255, 170, 80), 0.0, 110)
    def b_henki(s):
        yield from s._caster(92, 30, 1.2, "orb", (180, 130, 255), 0.022, 150)
    def _caster(s, dist, tel_n, spd, kind, col, homing, cd):
        cool = random.randint(30, cd)
        while True:
            t = s.target()
            if t is None:
                s.vx = 0; s.vy = math.sin(s.t * 0.05) * 0.2; s.anim = "idle"; yield; continue
            s.see(t); dx = t.x - s.x; ad = abs(dx); ty = t.y - 26 - 14 * math.sin(s.t * 0.03)
            want = (1 if dx > 0 else -1) * (1 if ad > dist + 14 else (-1 if ad < dist - 14 else 0))
            s.vx = want * s.speed * D()["spd"]; s.vy = max(-0.7, min(0.7, (ty - (s.y - s.h * 0.5)) * 0.04)); s.anim = "idle"
            cool -= 1
            if cool <= 0 and ad < 190 and s.g.los(s.x, s.y - 10, t.x, t.y - 9):
                n = tele(tel_n); s.anim = "windup"
                for i in range(n): s.vx *= 0.9; s.vy *= 0.9; s.warn = n - i; s.warn_t = i; yield
                s.warn = 0; s.anim = "attack"; sfx("orb", 0.7)
                ang = math.atan2(t.y - 9 - (s.y - s.h * 0.5), t.x - s.x)
                sp = spd * D()["spd"]
                s.g.projs.append(Proj(kind, s.x + s.face * 6, s.y - s.h * 0.5, math.cos(ang) * sp, math.sin(ang) * sp, s.sp["dmg"] * D()["dmg"], 7, 7, tags=("parry", "magic"), life=260, col=col, homing=homing, hp=1))
                for _ in range(10): s.vx = 0; s.vy = 0; yield
                cool = rest(cd)
            yield
    # ---- fliers ----
    def b_korppi(s): yield from s._swooper(1.0, 22, 2.6, 52)
    def b_joutsen(s): yield from s._swooper(1.4, 30, 2.1, 62)
    def _swooper(s, dmgm, tel_n, speed, hover):
        cool = random.randint(20, 90)
        while True:
            t = s.target()
            if t is None:
                s.vx = math.sin(s.t * 0.02) * 0.4; s.vy = math.cos(s.t * 0.03) * 0.2; s.anim = "idle"; yield; continue
            s.see(t)
            gx = t.x + math.sin(s.t * 0.025) * 70; gy = t.y - hover
            s.vx = max(-1.2, min(1.2, (gx - s.x) * 0.03)) * D()["spd"]; s.vy = max(-1.0, min(1.0, (gy - s.y) * 0.04)); s.anim = "idle"
            cool -= 1
            if cool <= 0 and abs(t.x - s.x) < 170 and s.y < t.y - 14:
                n = tele(tel_n); s.anim = "windup"
                for i in range(n):
                    s.vx = 0; s.vy = -0.5 if i < n - 8 else 0; s.warn = n - i; s.warn_t = i; s.see(t); yield
                s.warn = 0; s.anim = "attack"; sfx("crow", 0.7)
                ang = math.atan2(t.y - 8 - s.y, t.x - s.x); sp = speed * D()["spd"]
                s.atk = Atk((-s.w // 2 - 2, -s.h - 2, s.w + 4, s.h + 4), s.sp["dmg"] * D()["dmg"] * dmgm, 2.2, ("parry",), 12)
                s.atk.rel = (-s.w // 2 - 2 if s.face > 0 else -s.w // 2 - 2, -s.h - 2, s.w + 4, s.h + 4)
                for i in range(46):
                    s.vx = math.cos(ang) * sp; s.vy = math.sin(ang) * sp
                    if s.wall or s.head or s.on_ground and i > 4: break
                    yield
                s.atk = None; s.anim = "idle"
                for i in range(38): s.vx = -math.cos(ang) * 0.8; s.vy = -1.0; yield
                cool = rest(80)
            yield
    # ---- water ----
    def b_nakki(s):
        wy = s.hy
        while True:
            s.hidden = True; s.invuln = True; s.vx = 0; s.vy = 0; s.y = wy + 6; s.anim = "idle"
            t = s.g.nearest_player(s.x, s.y)
            if t is None or abs(t.x - s.x) > 52 or t.y > wy + 4 or t.y < wy - 120: yield; continue
            # bubbles warn, then leap
            n = tele(34)
            for i in range(n):
                if i % 4 == 0: s.g.parts.add(s.x + random.randint(-5, 5), wy, 0, -0.5, 18, (200, 230, 255), 1)
                s.warn = 0; yield
            t = s.g.nearest_player(s.x, s.y) or t
            s.hidden = False; s.invuln = False; s.see(t); s.y = wy
            s.anim = "windup"; s.warn = 8; s.warn_t = 0
            for _ in range(10): s.warn = 0; s.vy = 0; yield
            s.anim = "attack"; sfx("splash", 0.7); s.g.parts.burst(s.x, wy, (180, 220, 255), 8, 1.4, 16, 1, 0.1, 1.5)
            s.vy = -6.0; dxx = max(-60.0, min(60.0, t.x - s.x)); s.vx = dxx / 60.0
            s.atk = Atk((-8, -s.h - 2, 16, s.h + 4), s.sp["dmg"] * D()["dmg"], 2.4, ("parry",), 20); s.fly = True
            i = 0
            while True:
                i += 1; s.vy += GRAV * 0.98
                if s.y >= wy and i > 6: break
                yield
            s.fly = False; s.atk = None; s.vx = 0
            s.g.parts.burst(s.x, wy, (180, 220, 255), 8, 1.4, 16, 1, 0.1, 1.5); sfx("splash", 0.5)
            s.vuln = 0
            # snap back home and hide
            s.x = s.hx; s.y = wy + 6
            for _ in range(rest(70)): yield

    def update(s):
        if s.kind == "nakki" and not s.dead:
            # nakki are handled without tile physics
            s.t += 1; s.poise_t -= 1; s.last_hit += 1
            if s.flash > 0: s.flash -= 1
            if s.stun > 0: s.stun -= 1
            if s.gen is None: s.gen = s.brain()
            try: next(s.gen)
            except StopIteration: s.gen = None
            if not s.hidden: s.x += s.vx; s.y += s.vy
            if s.atk: s.atk.t += 1
            if s.hp <= 0 and not s.dead: s.die(None)
            return
        Enemy.update(s)
    def take(s, dmg, kb=0.0, poise=10, pl=None, tags=(), kbu=0.0):
        r = Enemy.take(s, dmg, 0.0 if s.kind == "nakki" else kb, poise, pl, tags, kbu)
        return r
    def hurt_rect(s):
        return (s.x - s.w / 2, s.y - s.h, s.w, s.h)
    def draw(s, surf, cx, cy):
        if s.kind not in ("poltto", "merikala", "kutri", "lampi", "rapu", "haaksi", "koralli", "ankkuri", "pylvas"):
            return Enemy.draw(s, surf, cx, cy)
        x = int(s.x - cx); y = int(s.y - s.h / 2 - cy)
        if s.kind == "lampi":
            pygame.draw.circle(surf, (186, 236, 210), (x, y), 6); pygame.draw.circle(surf, (255, 255, 220), (x, y - 1), 2)
            pygame.draw.line(surf, (120, 190, 170), (x, y + 4), (x, y + 12), 1)
        elif s.kind == "rapu":
            pygame.draw.ellipse(surf, (168, 92, 64), (x - 10, y - 6, 20, 10))
            pygame.draw.line(surf, (120, 60, 40), (x - 8, y), (x - 14, y - 6), 2); pygame.draw.line(surf, (120, 60, 40), (x + 8, y), (x + 14, y - 6), 2)
            pygame.draw.circle(surf, (40, 24, 16), (x - 3, y - 2), 1); pygame.draw.circle(surf, (40, 24, 16), (x + 3, y - 2), 1)
        elif s.kind == "poltto":
            pygame.draw.circle(surf, (34, 108, 121), (x, y), 8); pygame.draw.circle(surf, (113, 216, 183), (x, y), 5)
            for i in range(5): pygame.draw.line(surf, (22, 90, 120), (x - 8 + i * 4, y), (x - 8 + i * 4, y - 10), 2)
        elif s.kind == "merikala":
            pygame.draw.ellipse(surf, (41, 141, 164), (x - 14, y - 8, 25, 16)); pygame.draw.polygon(surf, (96, 186, 169), [(x - 10, y), (x - 25, y - 8), (x - 25, y + 8)]); pygame.draw.circle(surf, (211, 232, 179), (x + 7, y - 2), 2)
        elif s.kind == "haaksi":
            pygame.draw.ellipse(surf, (120, 190, 210), (x - 12, y - 5, 24, 10)); pygame.draw.polygon(surf, (80, 150, 180), [(x - 8, y), (x - 18, y - 4), (x - 18, y + 4)])
        elif s.kind == "koralli":
            pygame.draw.ellipse(surf, (70, 150, 110), (x - 9, y - 5, 18, 10))
            pygame.draw.line(surf, (40, 110, 80), (x - 6, y), (x - 10, y - 8), 2); pygame.draw.line(surf, (40, 110, 80), (x + 6, y), (x + 10, y - 8), 2)
        elif s.kind == "ankkuri":
            pygame.draw.rect(surf, (150, 150, 160), (x - 3, y - 14, 6, 18)); pygame.draw.circle(surf, (170, 170, 180), (x, y - 14), 5)
            pygame.draw.rect(surf, (120, 120, 130), (x - 8, y + 2, 16, 3))
        elif s.kind == "pylvas":
            pygame.draw.rect(surf, (170, 150, 210), (x - 4, y - 16, 8, 24)); pygame.draw.circle(surf, (240, 220, 160), (x, y - 6), 2)
        else:
            pygame.draw.arc(surf, (146, 171, 219), (x - 9, y - 10, 18, 34), 0, 6.28, 2)
            for i in range(3): pygame.draw.line(surf, (68, 141, 138), (x - 7 + i * 7, y), (x - 11 + i * 7, y + 14), 1)
