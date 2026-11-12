"""Aquatic bosses. Each one walks or swims after the player and telegraphs four different moves.

Phase 2 starts at half health and only shortens the rest, the way Hiisi does.
There is no second transformation at a quarter of the health.
"""
class WaterBoss(Boss):
    movers = ("leap", "dive", "charge", "arc", "lattice", "cross", "stream")
    def __init__(s, g, key, x, y):
        Boss.__init__(s, g, key, x, y)
        s.fly = False
        s.vb = "idle"
        s.hold = False
        s.flow = 0
        s.actname = ""
    def physics(s):
        # Horizontal speed is kept, as on Hiisi. The old per-frame damp stopped every step.
        if s.hold:
            s.x = max(s.L + 8, min(s.R - 8, s.x))
            return
        vx0 = s.vx
        s.vy = min(MAX_FALL, s.vy + GRAV)
        if not s.on_ground:
            s.drop_t = 2
        move_body(s.g.wd, s)
        if s.x < s.L + 8:
            s.x = s.L + 8
            s.wall = -1
        elif s.x > s.R - 8:
            s.x = s.R - 8
            s.wall = 1
        s.vx = vx0
        if s.y > s.gy:
            s.y = s.gy
            s.vy = 0
            s.on_ground = True
        if s.vx and abs(s.vx) > 0.05 and not s.atk:
            s.face = 1 if s.vx > 0 else -1
    def spd(s):
        return (1.0 if s.phase < 2 else 1.15) * D()["spd"]
    def far(s):
        t = s.mid_target()
        return bool(t and abs(t.x - s.x) > 130)
    def trans(s):
        s.atk = None
        s.invuln = True
        s.vx = 0
        s.flow = 0
        s.hold = False
        s.vb = "roar"
        sfx("roar", 0.9)
        s.g.shake(3, 38)
        for i in range(70):
            s.warn = 70 - i
            s.warn_t = i
            s.vx = 0
            yield
        s.phase = 2
        s.invuln = False
        s.vb = "idle"
        s.warn = 0
        MUSIC.request(s.key + "2")
    def tell(s, n):
        n = tele(n)
        s.vb = "windup"
        s.vx = 0
        for i in range(n):
            s.warn = n - i
            s.warn_t = i
            s.vx = 0
            yield
        s.warn = 0
        s.vb = "attack"
    def wait(s, n):
        s.vb = "idle"
        s.vx = 0
        s.flow = 0
        for _ in range(rest(n)):
            s.vx = 0
            yield
    def shoot(s, kind, x, y, vx, vy, dmg=20, life=160, curve=0, col=(103, 210, 203), w=10, h=14):
        s.g.projs.append(Proj(kind, x, y, vx, vy, dmg * D()["dmg"], w, h, tags=("magic",), life=life, curve=curve, col=col))
    def lanes(s, kind, speed, dmg, col, both=True):
        """Low lane catches a standing body. The full jump sits in the gap. The high lane is above that jump."""
        sides = (-1, 1) if both else (s.face,)
        for side in sides:
            s.shoot(kind, s.x, s.gy - 9, side * speed, 0, dmg, col=col, h=14)
            s.shoot(kind, s.x, s.gy - 93, side * speed, 0, dmg, col=col, h=14)
    def mark(s, x, delay, w, h, dmg, life, style):
        x = max(s.L + 18, min(s.R - 18, x))
        deal = dmg * D()["dmg"] if dmg else 0
        s.g.zones.append(Zone(x, s.gy, w, h, max(1, delay), life, deal, style, 2.2))
        return x
    def column_gap(s, w, h, dmg, step, delay, style):
        t = s.mid_target()
        xs = []
        x = s.L + 28
        while x < s.R - 20:
            xs.append(x)
            x += step
        if not xs:
            return
        if t:
            xs.remove(min(xs, key=lambda q: abs(q - t.x)))
        else:
            xs.pop(len(xs) // 2)
        for i, col in enumerate(xs):
            s.g.zones.append(Zone(col, s.gy, w, h, delay + (i % 3) * 6, 16, dmg * D()["dmg"], style, 2.2))
    def pursue(s, dist, frames):
        for _ in range(frames):
            t = s.mid_target()
            if t is None:
                s.vx = 0
                yield
                continue
            s.see(t)
            if abs(t.x - s.x) < dist:
                break
            s.vb = "idle"
            s.vx = s.face * 1.0 * s.spd()
            yield
        s.vx = 0
    def leap_to(s, tx, pose="attack"):
        tx = max(s.L + 24, min(s.R - 24, tx))
        n = tele(30)
        s.mark(tx, n + 16, 34, 18, 0, 10, "rock")
        s.vb = "windup"
        s.vx = 0
        for i in range(n):
            s.warn = n - i
            s.warn_t = i
            s.vx = 0
            yield
        s.warn = 0
        s.vb = pose
        s.hold = True
        sx = s.x
        arc_n = 20
        for i in range(1, arc_n + 1):
            s.hold = True
            s.x = sx + (tx - sx) * i / arc_n
            s.y = s.gy - math.sin(math.pi * i / arc_n) * 50
            if i > arc_n - 6:
                s.atk = Atk((-16, -14, 32, 16), s.sp["dmg"] * D()["dmg"] * 0.85, 3.0, ("heavy",), 18)
            yield
        s.atk = None
        s.hold = False
        s.y = s.gy
        s.vy = 0
        s.vx = 0
        s.g.shake(3, 8)
        yield from s.wait(8)
    def perform(s, act):
        s.actname = act
        fn = getattr(s, "a_" + act, None)
        if fn is None:
            yield from s.wait(6)
            return
        yield from fn()
    def jous(s):
        yield from s.perform(s.pick(s.opts()))
    aht = ain = vel = jous
    def brain(s):
        s.invuln = True
        s.vb = "roar"
        sfx("roar", 0.9)
        for i in range(48):
            s.vx = 0
            s.warn = max(0, 18 - i)
            yield
        s.invuln = False
        s.warn = 0
        yield from s.wait(12)
        while True:
            t = s.mid_target()
            if t is None:
                s.vx = 0
                s.vb = "idle"
                yield
                continue
            act = s.pick(s.opts())
            s.actname = act
            if act not in s.movers and abs(t.x - s.x) > 84:
                yield from s.pursue(56, 70)
            yield from s.perform(act)
            yield from s.wait(34 if s.phase < 2 else 18)
    def a_verse(s):
        t = s.mid_target()
        if t:
            s.see(t)
        yield from s.tell(32)
        s.lanes("verse", 1.65, 18, (120, 170, 210), both=False)
        yield from s.wait(22)
    def a_bog(s):
        t = s.mid_target()
        x = t.x if t and t.y > s.gy - 24 else s.x
        x = max(s.L + 20, min(s.R - 20, x))
        n = tele(34)
        s.g.zones.append(Zone(x, s.gy, 46, 16, n, 150, 14 * D()["dmg"], "bog", 0))
        for i in range(n):
            s.vb = "windup"
            s.warn = n - i
            s.warn_t = i
            s.vx = 0
            yield
        s.vb = "attack"
        s.warn = 0
        yield from s.wait(18)
    def a_leap(s):
        t = s.mid_target()
        tx = t.x if t else s.x + s.face * 48
        yield from s.leap_to(tx, "attack")
    def a_frost(s):
        yield from s.tell(24)
        s.column_gap(26, 130, 22, 64, tele(26), "frost")
        yield from s.wait(22)
    def a_dive(s):
        t = s.mid_target()
        tx = max(s.L + 28, min(s.R - 28, t.x if t else s.x))
        n = tele(34)
        s.mark(tx, n, 36, 30, 20, 12, "geyser")
        s.vb = "windup"
        s.hold = True
        s.invuln = True
        for i in range(10):
            s.y = s.gy + i * 1.5
            yield
        s.x = tx
        for i in range(max(0, n - 10)):
            s.warn = max(0, n - 10 - i)
            s.warn_t = i
            s.y = s.gy + 16
            yield
        s.invuln = False
        s.hold = False
        s.y = s.gy
        s.vb = "attack"
        s.warn = 0
        for _ in range(8):
            yield
        s.lanes("swell", 1.55, 18, (80, 160, 200), True)
        yield from s.wait(16)
    def a_charge(s):
        t = s.mid_target()
        if t:
            s.see(t)
        n = tele(30)
        end = s.R - 16 if s.face > 0 else s.L + 16
        s.mark((s.x + end) * 0.5, n, max(24, abs(end - s.x)), 8, 0, 8, "rock")
        for i in range(n):
            s.vb = "windup"
            s.vx = 0
            s.warn = n - i
            s.warn_t = i
            yield
        s.warn = 0
        s.vb = "attack"
        sfx("roar", 0.75)
        s.atk = Atk((-18, -26, 36, 26), s.sp["dmg"] * D()["dmg"], 3.4, ("heavy",), 24)
        crashed = False
        for _ in range(64):
            s.vx = s.face * 3.15 * s.spd()
            if s.wall or abs(s.x - (s.R if s.face > 0 else s.L)) < 8:
                crashed = True
                break
            yield
        s.atk = None
        s.vx = 0
        if crashed:
            s.g.shake(4, 12)
            sfx("boom", 0.85)
            s.stun = 66
            s.vuln = 66
            s.armor = False
            s.vb = "roar"
            s.anim = "stagger"
            yield
            s.armor = True
        else:
            yield from s.wait(8)
    def a_geyser(s):
        n = tele(22)
        for i in range(n):
            s.vb = "windup"
            s.warn = n - i
            s.warn_t = i
            s.vx = 0
            yield
        xs = []
        for p in s.g.players:
            if p.alive() and p.y > s.gy - 24:
                xs.append(max(s.L + 18, min(s.R - 18, p.x)))
        if not xs:
            xs = [s.L + 24, s.R - 24]
        for i, x in enumerate(xs[:3]):
            s.g.zones.append(Zone(x, s.gy, 24, 30, tele(24) + i * 6, 14, 20 * D()["dmg"], "geyser", 2.2))
        s.vb = "attack"
        s.warn = 0
        yield from s.wait(28)
    def a_current(s):
        t = s.mid_target()
        gap = t.x if t else (s.L + s.R) * 0.5
        s.flow = -1 if t and t.x < s.x else 1
        n = tele(28)
        x = s.L + 34
        made = False
        while x < s.R - 20:
            if abs(x - gap) > 36:
                s.g.zones.append(Zone(x, s.gy, 26, 14, n, 18, 16 * D()["dmg"], "tidepike", 1.2))
                made = True
            x += 48
        if not made:
            s.g.zones.append(Zone(s.L + 30, s.gy, 22, 14, n, 18, 16 * D()["dmg"], "tidepike", 1.2))
        for i in range(n + 16):
            s.vb = "windup" if i < n else "attack"
            s.warn = max(0, n - i)
            s.vx = 0
            yield
        s.warn = 0
        yield from s.wait(12)
    def a_arc(s):
        t = s.mid_target()
        tx = t.x if t else s.x + s.face * 40
        s.vb = "fish"
        yield from s.leap_to(tx, "fish")
        s.vb = "maiden"
    def a_drop(s):
        t = s.mid_target()
        x = max(s.L + 20, min(s.R - 20, t.x if t else s.x))
        n = tele(30)
        s.mark(x, n + 20, 26, 140, 0, 8, "rock")
        for i in range(n):
            s.vb = "windup"
            s.warn = n - i
            s.warn_t = i
            s.vx = 0
            yield
        s.shoot("memory", x, s.gy - 84, 0, 2.3, 20, life=70, h=14, w=12, col=(192, 181, 231))
        s.vb = "attack"
        s.warn = 0
        yield from s.wait(18)
    def a_stream(s):
        mid = (s.L + s.R) * 0.5
        for _ in range(90):
            if abs(s.x - mid) < 14:
                break
            s.face = 1 if mid > s.x else -1
            s.vx = s.face * 0.95 * s.spd()
            s.vb = "maiden"
            yield
        s.vx = 0
        yield from s.tell(28)
        s.lanes("bubble", 1.5, 18, (150, 210, 220), True)
        yield from s.wait(16)
    def a_lattice(s):
        players = [p for p in s.g.players if p.alive()]
        if players:
            far = max(players, key=lambda p: abs(p.x - s.x))
            tx = far.x + (40 if far.x < s.x else -40)
        else:
            tx = s.L + 40 if s.x > (s.L + s.R) * 0.5 else s.R - 40
        tx = max(s.L + 24, min(s.R - 24, tx))
        n = tele(32)
        s.mark(tx, n, 34, 30, 18, 10, "geyser")
        s.hold = True
        s.invuln = True
        s.vb = "windup"
        for i in range(8):
            s.y = min(s.gy + 18, s.y + 2)
            yield
        s.x = tx
        for i in range(max(0, n - 8)):
            s.warn = max(0, n - 8 - i)
            s.warn_t = i
            yield
        s.invuln = False
        s.hold = False
        s.y = s.gy
        s.vb = "attack"
        s.warn = 0
        for _ in range(6):
            yield
        s.lanes("memory", 1.5, 20, (160, 150, 210), True)
        yield from s.wait(14)
    def a_crown(s):
        yield from s.tell(26)
        s.armor = False
        s.vuln = 86
        s.column_gap(22, 120, 24, 58, tele(22), "tidepike")
        yield from s.wait(34)
        s.armor = True
    def a_cage(s):
        t = s.mid_target()
        n = tele(36)
        if t:
            s.g.zones.append(Zone(t.x, s.gy, 54, 78, n, 18, 24 * D()["dmg"], "cage", 1.6))
        for i in range(n):
            s.vb = "windup"
            s.warn = n - i
            s.warn_t = i
            s.vx = 0
            yield
        s.vb = "attack"
        s.warn = 0
        yield from s.wait(14)
    def a_cross(s):
        t = s.mid_target()
        if t:
            s.see(t)
        n = tele(28)
        for i in range(n):
            s.vb = "windup"
            s.vx = 0
            s.warn = n - i
            s.warn_t = i
            yield
        s.warn = 0
        s.vb = "attack"
        s.atk = Atk((-16, -24, 32, 24), s.sp["dmg"] * D()["dmg"] * 0.8, 3.0, ("heavy",), 16)
        for _ in range(22):
            s.vx = s.face * 2.8 * s.spd()
            if s.wall:
                break
            yield
        s.atk = None
        s.vx = 0
        for vx, vy in ((1.7, 0), (-1.7, 0), (0, -1.7), (0, 1.5)):
            y = s.gy - 9 if vy == 0 else s.gy - 40
            s.shoot("memory", s.x, y, vx, vy, 20, life=110, h=12, w=10, col=(176, 170, 220))
        yield from s.wait(16)

class Joukahainen(WaterBoss):
    def __init__(s, g, x, y):
        WaterBoss.__init__(s, g, "joukahainen", x, y)
    def opts(s):
        o = [("verse", 1.1), ("bog", 1.0), ("leap", 1.2)]
        if s.phase >= 2:
            o.append(("frost", 1.0))
        if s.far():
            o = [("leap", 1.7), ("verse", 1.2), ("bog", 0.6)]
            if s.phase >= 2:
                o.append(("frost", 0.8))
        return o

class Ahti(WaterBoss):
    def __init__(s, g, x, y):
        WaterBoss.__init__(s, g, "ahti", x, y)
    def opts(s):
        o = [("dive", 1.2), ("charge", 1.3), ("geyser", 1.0)]
        if s.phase >= 2:
            o.append(("current", 1.0))
        if s.far():
            o = [("charge", 1.7), ("dive", 1.4), ("geyser", 0.5)]
            if s.phase >= 2:
                o.append(("current", 0.8))
        return o

class Aino(WaterBoss):
    def __init__(s, g, x, y):
        WaterBoss.__init__(s, g, "aino", x, y)
    def die(s, pl):
        s.calm()
    def calm(s):
        s.hp = 1
        s.gen = None
        s.g.start_aino_reveal()
    def opts(s):
        o = [("arc", 1.3), ("drop", 1.0), ("stream", 1.1)]
        if s.phase >= 2:
            o.append(("frost", 1.0))
        if s.far():
            o = [("arc", 1.8), ("stream", 1.0), ("drop", 0.7)]
            if s.phase >= 2:
                o.append(("frost", 0.7))
        return o
    def a_frost(s):
        yield from s.tell(24)
        slots = [s.L + 52, (s.L + s.R) * 0.5, s.R - 52]
        t = s.mid_target()
        if t:
            slots.remove(min(slots, key=lambda q: abs(q - t.x)))
        else:
            slots.pop(1)
        for x in slots:
            s.g.zones.append(Zone(x, s.gy, 30, 130, tele(22), 16, 22 * D()["dmg"], "frost", 2.0))
        s.vb = "attack"
        yield from s.wait(18)

class Vellamo(WaterBoss):
    def __init__(s, g, x, y):
        WaterBoss.__init__(s, g, "vellamo", x, y)
    def opts(s):
        o = [("lattice", 1.2), ("crown", 1.0), ("cage", 1.0)]
        if s.phase >= 2:
            o.append(("cross", 1.1))
        if s.far():
            o = [("lattice", 1.6), ("crown", 0.7), ("cross", 1.2) if s.phase >= 2 else ("cage", 0.9)]
        return o

BOSS_CLS.update(joukahainen=Joukahainen, ahti=Ahti, aino=Aino, vellamo=Vellamo)
