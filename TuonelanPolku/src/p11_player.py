
# ---------------- input ----------------
# Face / shoulder mapping is identical for every device:
#   Cross/A = jump, Circle/B = dodge, Square/X = light, Triangle/Y = heavy,
#   L1 = guard, R1 = skill, R2 or D-pad down = flask, Options = start, Share = back.
# GameController path preferred; raw joystick uses the Linux hid-playstation layout that matches it.
# Per-device instance id; never hardcode joystick 0 or split one pad across two players.
class Pad:
    KEYS = ("up", "jump", "light", "heavy", "dodge", "guard", "skill", "flask", "start", "back", "left", "right", "down")
    # raw hid-playstation / DualShock face+shoulder indices (== SDL GameController South,East,West,North,L1,R1,R2,Share,Options)
    RAW = dict(jump=0, dodge=1, light=2, heavy=3, guard=4, skill=5, flask=7, back=8, start=9)
    def __init__(self, kind, dev=None, iid=None, joy=None):
        self.kind, self.dev, self.joy = kind, dev, joy
        self.prev = self.blank(); self.cur = self.blank()
        if kind == "kb": self.id = "kb"
        elif iid is not None: self.id = "js%d" % iid
        else: self.id = "js%s" % (joy.get_instance_id() if joy is not None else (dev.get_instance_id() if hasattr(dev, "get_instance_id") else id(self)))
        self.rep = {}
    def blank(self):
        c = {k: False for k in self.KEYS}; c["x"] = 0.0; c["y"] = 0.0; return c
    def _apply_face(self, c, jump, dodge, light, heavy, guard, skill, flask, start, back):
        c.update(jump=bool(jump), dodge=bool(dodge), light=bool(light), heavy=bool(heavy),
                 guard=bool(guard), skill=bool(skill), flask=bool(flask), start=bool(start), back=bool(back))
    def poll(self, ks):
        c = self.blank()
        try:
            if self.kind == "kb":
                c["x"] = float(ks[pygame.K_RIGHT] - ks[pygame.K_LEFT]); c["y"] = float(ks[pygame.K_DOWN] - ks[pygame.K_UP])
                c.update(up=bool(ks[pygame.K_UP]), down=bool(ks[pygame.K_DOWN]), left=bool(ks[pygame.K_LEFT]), right=bool(ks[pygame.K_RIGHT]))
                self._apply_face(c, ks[pygame.K_z] or ks[pygame.K_SPACE], ks[pygame.K_v], ks[pygame.K_x], ks[pygame.K_c],
                                 ks[pygame.K_a], ks[pygame.K_s], ks[pygame.K_d], ks[pygame.K_RETURN], ks[pygame.K_TAB])
            elif self.kind == "gc":
                g = self.dev; P = pygame
                ax = g.get_axis(P.CONTROLLER_AXIS_LEFTX) / 32768.0; ay = g.get_axis(P.CONTROLLER_AXIS_LEFTY) / 32768.0
                b = g.get_button
                if b(P.CONTROLLER_BUTTON_DPAD_LEFT): ax = -1.0
                if b(P.CONTROLLER_BUTTON_DPAD_RIGHT): ax = 1.0
                if b(P.CONTROLLER_BUTTON_DPAD_UP): ay = -1.0
                if b(P.CONTROLLER_BUTTON_DPAD_DOWN): ay = 1.0
                self._fill_axes(c, ax, ay)
                trig = False
                try: trig = g.get_axis(P.CONTROLLER_AXIS_TRIGGERRIGHT) > 12000
                except (pygame.error, SystemError): pass
                self._apply_face(c, b(P.CONTROLLER_BUTTON_A), b(P.CONTROLLER_BUTTON_B), b(P.CONTROLLER_BUTTON_X), b(P.CONTROLLER_BUTTON_Y),
                                 b(P.CONTROLLER_BUTTON_LEFTSHOULDER), b(P.CONTROLLER_BUTTON_RIGHTSHOULDER),
                                 c["down"] or trig, b(P.CONTROLLER_BUTTON_START), b(P.CONTROLLER_BUTTON_BACK))
            else:    # raw joystick, same layout as GameController face buttons
                j = self.dev
                ax = j.get_axis(0) if j.get_numaxes() > 0 else 0.0; ay = j.get_axis(1) if j.get_numaxes() > 1 else 0.0
                if j.get_numhats() > 0:
                    hx, hy = j.get_hat(0)
                    if hx: ax = float(hx)
                    if hy: ay = -float(hy)          # SDL hat: up = +1
                self._fill_axes(c, ax, ay)
                nb = j.get_numbuttons(); b = lambda i: nb > i and bool(j.get_button(i)); R = Pad.RAW
                self._apply_face(c, b(R["jump"]), b(R["dodge"]), b(R["light"]), b(R["heavy"]), b(R["guard"]), b(R["skill"]),
                                 b(R["flask"]) or c["down"], b(R["start"]), b(R["back"]))
        except (pygame.error, SystemError):
            pass
        self.prev, self.cur = self.cur, c
    def _fill_axes(self, c, ax, ay):
        c["x"] = ax if abs(ax) > 0.25 else 0.0
        c["y"] = ay if abs(ay) > 0.5 else 0.0
        c["left"] = c["x"] < -0.5; c["right"] = c["x"] > 0.5; c["up"] = c["y"] < -0.5; c["down"] = c["y"] > 0.5
    def pressed(self, k): return bool(self.cur.get(k)) and not self.prev.get(k)
    def held(self, k): return bool(self.cur.get(k))
    def nav(self, k):
        if self.pressed(k): self.rep[k] = 0; return True
        if self.held(k):
            self.rep[k] = self.rep.get(k, 0) + 1
            if self.rep[k] > 22 and self.rep[k] % 5 == 0: return True
        return False

class IdlePad(Pad):
    def __init__(self): Pad.__init__(self, "idle"); self.id = "idle%d" % id(self)
    def poll(self, ks): self.prev, self.cur = self.cur, self.blank()

class ScriptPad(Pad):
    """Used by tests: set .nextc (or .cur) directly. Same KEYS as a real pad."""
    def __init__(self, name="script"):
        Pad.__init__(self, "script"); self.id = name; self.cur = self.blank(); self.prev = self.blank(); self.nextc = None
    def poll(self, ks):
        self.prev = self.cur; self.cur = self.nextc if self.nextc is not None else self.blank()

class FakeJoyPad(Pad):
    """Test stand-in for a physical stick. Push the same button/axis events P1 and P2 would see."""
    def __init__(self, name, via="gc"):
        Pad.__init__(self, "fake"); self.id = name; self.via = via
        self.axes = [0.0] * 6; self.buttons = [0] * 16; self.hat = (0, 0)
        self.cur = self.blank(); self.prev = self.blank()
    def set_button(self, name, v=1):
        """name is a logical action OR a raw index. Logical names use the shared RAW/GC mapping."""
        if name in Pad.RAW: self.buttons[Pad.RAW[name]] = int(bool(v))
        elif name == "dpad_up": self.hat = (self.hat[0], 1 if v else 0)
        elif name == "dpad_down": self.hat = (self.hat[0], -1 if v else 0)
        elif name == "dpad_left": self.hat = (-1 if v else 0, self.hat[1])
        elif name == "dpad_right": self.hat = (1 if v else 0, self.hat[1])
        elif isinstance(name, int): self.buttons[name] = int(bool(v))
    def set_stick(self, x=0.0, y=0.0): self.axes[0] = x; self.axes[1] = y
    def poll(self, ks):
        # Always go through the same apply path as a real pad of the chosen kind.
        c = self.blank(); b = lambda i: i < len(self.buttons) and bool(self.buttons[i]); R = Pad.RAW
        ax, ay = self.axes[0], self.axes[1]
        hx, hy = self.hat
        if hx: ax = float(hx)
        if hy: ay = -float(hy)
        self._fill_axes(c, ax, ay)
        self._apply_face(c, b(R["jump"]), b(R["dodge"]), b(R["light"]), b(R["heavy"]), b(R["guard"]), b(R["skill"]),
                         b(R["flask"]) or c["down"], b(R["start"]), b(R["back"]))
        self.prev, self.cur = self.cur, c

_FLIP = {}
def flipped(surf):
    k = id(surf)
    f = _FLIP.get(k)
    if f is None or f[0] is not surf:
        f = (surf, pygame.transform.flip(surf, True, False)); _FLIP[k] = f
    return f[1]

# ---------------- classes ----------------
CLS = {
    "warrior": dict(hp=120, st=100, foc=0, flask=0.45),
    "sage":    dict(hp=80, st=90, foc=100, flask=0.45),
    "hunter":  dict(hp=95, st=105, foc=0, flask=0.45),
}
# attack tables: st=startup frames, ac=active, rc=recover, stam, rel hitbox (fwd, y, w, h)
ATK = {
    "warrior": {
        "light": [dict(st=6, ac=4, rc=11, dmg=14, rel=(2, -20, 25, 16), kb=1.6, poise=10, stam=14, step=0.9, anim="atk1", snd="swing"),
                  dict(st=5, ac=4, rc=12, dmg=14, rel=(2, -18, 25, 16), kb=1.6, poise=10, stam=14, step=0.9, anim="atk2", snd="swing"),
                  dict(st=8, ac=5, rc=18, dmg=23, rel=(2, -24, 30, 22), kb=3.0, poise=22, stam=20, step=1.5, anim="atk3", snd="swing2")],
        "heavy": dict(st=18, ac=5, rc=24, dmg=40, rel=(2, -26, 32, 26), kb=3.6, poise=36, stam=32, step=1.0, anim="heavy", snd="swing2", tags=("heavy",)),
    },
    "sage": {
        "light": [dict(st=8, ac=2, rc=12, dmg=12, fire="bolt", foc=4, stam=6, anim="atk1", snd="bolt")],
        "heavy": dict(st=22, ac=2, rc=22, dmg=30, fire="orb", foc=16, stam=14, anim="cast", snd="orb", tags=("heavy",)),
        "melee": dict(st=6, ac=4, rc=12, dmg=8, rel=(2, -22, 24, 14), kb=1.4, poise=8, stam=10, step=0.5, anim="atk1", snd="swing"),
    },
    "hunter": {
        "light": [dict(st=3, ac=3, rc=8, dmg=9, rel=(2, -16, 20, 14), kb=0.8, poise=7, stam=9, step=1.0, anim="atk1", snd="swing"),
                  dict(st=3, ac=3, rc=10, dmg=9, rel=(2, -16, 20, 14), kb=0.8, poise=7, stam=9, step=1.0, anim="atk2", snd="swing"),
                  dict(st=4, ac=4, rc=14, dmg=14, rel=(2, -18, 24, 16), kb=1.6, poise=12, stam=12, step=1.6, anim="atk3", snd="swing2")],
        "heavy": dict(st=10, ac=5, rc=18, dmg=26, rel=(0, -18, 28, 14), kb=2.4, poise=24, stam=24, step=3.0, anim="heavy", snd="swing2", tags=("heavy",)),
    },
}
ROLL = {"warrior": dict(dur=22, i0=3, i1=16, sp=2.7, stam=20), "sage": dict(dur=22, i0=3, i1=13, sp=2.6, stam=22),
        "hunter": dict(dur=26, i0=3, i1=20, sp=3.3, stam=18)}
CHARM_NAMES = ("c_bear", "c_wolf", "c_moss", "c_ember", "c_pearl")

class Player(Body):
    def __init__(s, g, idx, pad, ch):
        Body.__init__(s, 0, 0, PW_, PH_)
        s.g = g; s.idx = idx; s.pad = pad; s.ch = ch; s.cls = ch["cls"]
        s.state = "free"; s.st_t = 0; s.face = 1; s.hp = 1.0; s.stam = 1.0; s.focus = 0.0
        s.inv = 0; s.flash = 0; s.atk = None; s.act = None; s.combo = 0; s.combo_t = 0; s.buf = None; s.buf_t = 0
        s.stam_delay = 0; s.stun = 0; s.guard_t = 0; s.drink_t = 0; s.flasks = 0
        s.down_t = 0; s.revive_t = 0; s.safe = (0, 0); s.safe_t = 0; s.draw_t = 0; s.ward = 0; s.roll_dir = 1
        s.nearby = None; s.blocked_flash = 0; s.dealt = 0; s.exh = 0; s.air_atk = False; s.climb = False; s.t = 0; s.carry_souls = 0
        s.recalc(); s.hp = s.maxhp; s.stam = s.maxst; s.focus = s.maxfoc
    @property
    def souls(s): return s.ch.get("souls", 0)
    @souls.setter
    def souls(s, v): s.ch["souls"] = max(0, min(99999999, int(v)))
    # ----- derived stats -----
    @property
    def taken(s): return s.g.save["taken"]
    def has(s, k): return k in s.taken
    def recalc(s):
        c = CLS[s.cls]; st = s.ch["stats"]
        s.maxhp = c["hp"] + 10 * st["vit"] + (20 if s.has("c_moss") else 0)
        s.maxst = c["st"] + 6 * st["end"]
        s.maxfoc = (c["foc"] + 10 * st["foc"]) if s.cls == "sage" else 0
        s.dmgm = (1 + 0.08 * st["str"]) * (1.15 if s.has("c_bear") else 1.0) * (1.25 if s.ward > 0 else 1.0)
        s.spellm = (1 + 0.08 * st["foc"] + 0.04 * st["str"]) * (1.15 if s.has("c_bear") else 1.0) * (1.25 if s.ward > 0 else 1.0)
        s.bowm = (1 + 0.04 * st["str"] + 0.08 * st["foc"]) * (1.15 if s.has("c_bear") else 1.0) * (1.25 if s.ward > 0 else 1.0)
        s.regen = 0.55 * (1.3 if s.has("c_wolf") else 1.0) * (1.08 if s.has("c_pearl") else 1.0)
        if SETTINGS.get("test_weapon"):
            s.dmgm *= 25; s.spellm *= 25; s.bowm *= 25
        s.flask_max = 3 + (1 if s.has("flask1") else 0) + (1 if s.has("flask2") else 0)
        s.flask_pct = CLS[s.cls]["flask"] + (0.25 if s.has("flaskpow") else 0.0)
        s.dj_ok = s.has("feather")
        s.poise_b = 3 * st["foc"] if s.cls == "warrior" else 0
        s.block_eff = 1.0 - (0.03 * st["foc"] if s.cls == "warrior" else 0.0)
        s.roll_cost = ROLL[s.cls]["stam"] * (0.7 if s.has("c_ember") else 1.0) * (1.0 - (0.03 * st["foc"] if s.cls == "hunter" else 0.0))
        s.hp = min(s.hp, s.maxhp); s.stam = min(s.stam, s.maxst); s.focus = min(s.focus, s.maxfoc)
    def refill(s):
        s.recalc(); s.hp = s.maxhp; s.stam = s.maxst; s.focus = s.maxfoc; s.flasks = s.flask_max
    def alive(s): return s.state not in ("dead", "down")
    @property
    def level(s): return 1 + sum(s.ch["stats"].values())
    def hurt_rect(s): return (s.x - 5, s.y - 18, 10, 18)
    def spawn(s, x, y):
        s.x = float(x); s.y = float(y); s.vx = s.vy = 0.0; s.state = "free"; s.st_t = 0; s.atk = None; s.act = None; s.inv = 40; s.climb = False
        s.stun = 0; s.safe = (x, y); s.buf = None; s.drink_t = 0; s.on_ground = False; s.revive_t = 0
    # ----- resources -----
    def spend(s, n):
        s.stam = max(0.0, s.stam - n); s.stam_delay = 36 if s.stam > 0 else 70
    # ----- damage in -----
    def take_hit(s, dmg, sx, kb=2.0, tags=(), src=None):
        if s.state in ("dead", "down") or s.inv > 0: return False
        g = s.g; tags = set(tags)
        cycle = int((g.save or {}).get("ng") or 0) if g.save else 0
        if cycle: dmg *= 1.0 + 0.12 * cycle
        facing_src = (sx >= s.x) == (s.face > 0) or abs(sx - s.x) < 3
        # parry / block (warrior guard)
        if s.state == "guard" and facing_src:
            win = int(11 * D()["parry"])
            if s.guard_t < win and "parry" in tags:
                sfx("parry", 1.0); g.hitstop = max(g.hitstop, 8); s.flash = 3; g.shake(2, 6)
                g.parts.burst(s.x + s.face * 8, s.y - 12, (255, 240, 160), 14, 2.4, 20)
                if isinstance(src, Enemy): src.stagger(60 if src.boss else 80)
                elif isinstance(src, Proj): src.enemy = False; src.vx *= -1.4; src.vy *= -1.4; src.pid = s.idx; src.hit = set(); src.tags.add("reflected")
                s.stam = min(s.maxst, s.stam + 25); s.inv = 12
                g.dnum(s.x, s.y - 26, tr("parry"), (255, 240, 160))
                return True
            cost = dmg * 0.55 * s.block_eff + 6
            if "heavy" in tags: cost *= 1.4
            if s.stam >= cost:
                s.spend(cost); sfx("block", 0.9); g.hitstop = max(g.hitstop, 3); s.vx = -s.face * kb * 0.5 if sx > s.x else s.face * -kb * 0.5
                s.blocked_flash = 6; g.parts.burst(s.x + s.face * 7, s.y - 11, (255, 255, 220), 6, 1.8, 12)
                chip = dmg * 0.12
                s.hp -= chip
                if s.hp <= 0: s.die()
                return True
            s.stam = 0; s.stam_delay = 90; dmg *= 0.7; s.stun = 26; s.state = "hurt"; s.st_t = 0   # guard break
            sfx("hurt", 1.0)
        else:
            s.state = "hurt"; s.st_t = 0
            s.stun = 14 if "heavy" not in tags else 22
        if s.state == "hurt" and s.act is not None: s.act = None
        s.atk = None; s.drink_t = 0; s.draw_t = 0; s.climb = False; s.buf = None
        s.hp -= dmg; s.flash = 6; s.inv = 40
        s.vx = kb * (1 if s.x >= sx else -1) * 1.3; s.vy = -2.2; s.on_ground = False
        sfx("hurt", 1.0); g.hitstop = max(g.hitstop, 6); g.shake(3, 8)
        g.parts.burst(s.x, s.y - 10, (200, 40, 50), 8, 1.8, 18, 1, 0.08)
        g.dnum(s.x, s.y - 26, int(round(dmg)), (255, 90, 90), player=True)
        if s.hp <= 0: s.die()
        return True
    def die(s):
        s.hp = 0; s.atk = None; s.act = None; s.drink_t = 0; s.climb = False
        s.g.player_down(s)
    # ----- actions -----
    def start_act(s, kind, spec, **kw):
        s.state = "act"; s.st_t = 0; s.act = dict(spec); s.act["kind"] = kind; s.act.update(kw); s.atk = None
        s.combo_t = 0
        if "stam" in spec: s.spend(spec["stam"])
        if "foc" in spec: s.focus = max(0.0, s.focus - spec["foc"])
    def can(s, stam=1, foc=0): return s.stam >= min(stam, 1) and s.focus >= foc
    def want(s, name):
        s.buf = name; s.buf_t = 12
    def try_action(s, name):
        """returns True if the action started."""
        c = s.cls; tbl = ATK[c]
        if name == "dodge":
            if s.stam < 1: return False
            r = ROLL[c]; s.state = "roll"; s.st_t = 0; s.atk = None; s.act = None; s.spend(s.roll_cost)
            ix = s.pad.cur["x"]
            s.roll_dir = (1 if ix > 0 else -1) if abs(ix) > 0.3 else s.face
            s.face = s.roll_dir; s.climb = False; sfx("roll", 0.7); return True
        if name == "flask":
            if s.flasks <= 0 or s.hp >= s.maxhp or not s.on_ground: return False
            s.state = "drink"; s.st_t = 0; s.flasks -= 1; s.drink_t = 0; sfx("flask", 0.8); return True
        if name in ("light", "heavy"):
            if s.stam < 1 and c != "sage": return False
            if name == "heavy":
                if c == "sage" and s.focus < tbl["heavy"]["foc"]: return False
                s.start_act("heavy", tbl["heavy"]); return True
            if c == "sage":
                sp = tbl["light"][0]
                if s.focus < sp["foc"]: sp = tbl["melee"]
                s.start_act("light", sp); return True
            sp = tbl["light"][s.combo % len(tbl["light"])]
            s.start_act("light", sp); s.combo += 1; return True
        if name == "guard":
            if c == "warrior":
                if not s.on_ground: return False
                s.state = "guard"; s.st_t = 0; s.guard_t = 0; s.vx = 0; return True
            if c == "sage":
                if s.focus < 45 or not s.on_ground: return False
                s.focus -= 45; s.state = "kantele"; s.st_t = 0; sfx("kantele", 0.9); return True
            if c == "hunter":
                if s.stam < 1: return False
                s.start_act("flip", dict(st=4, ac=22, rc=6, stam=20, anim="shoot"))
                s.vx = -s.face * 3.2; s.vy = -3.0; s.on_ground = False; s.inv = max(s.inv, 10); return True
        if name == "skill":
            if c == "warrior":
                if s.stam < 1: return False
                s.start_act("bash", dict(st=8, ac=4, rc=14, dmg=10, rel=(2, -20, 20, 18), kb=4.5, poise=60, stam=22, step=1.8, anim="bash", snd="swing", tags=("bash",)))
                return True
            if c == "sage":
                if s.focus < 25: return False
                s.start_act("nova", dict(st=10, ac=3, rc=18, dmg=22, foc=25, stam=10, anim="cast", snd="boom"))
                return True
            if c == "hunter":
                if s.stam < 1: return False
                s.state = "draw"; s.st_t = 0; s.draw_t = 0; return True
        return False
    # ----- per frame -----
    def update(s):
        s.g.pending_action={a for a in ("jump","light","heavy","dodge") if s.pad.pressed(a)}
        g = s.g; pad = s.pad; c = pad.cur; s.t += 1
        if s.flash > 0: s.flash -= 1
        if s.blocked_flash > 0: s.blocked_flash -= 1
        if s.ward > 0: s.ward -= 1; s.recalc() if s.ward in (0, 1799) else None
        if s.state == "dead": return
        if s.state == "down":
            s.down_t -= 1; s.vx *= 0.8
            s.vy = min(MAX_FALL, s.vy + GRAV); move_body(g.wd, s)
            if s.down_t <= 0: s.state = "dead"; g.on_player_dead(s)
            return
        if s.inv > 0: s.inv -= 1
        if s.buf_t > 0:
            s.buf_t -= 1
            if s.buf_t == 0: s.buf = None
        if s.combo_t > 0:
            s.combo_t -= 1
            if s.combo_t == 0: s.combo = 0
        # stamina / focus
        if s.stam_delay > 0: s.stam_delay -= 1
        elif s.stam < s.maxst:
            r = s.regen * (0.45 if s.state == "guard" else 1.0) * (1.0 if s.on_ground or s.climb else 0.6)
            s.stam = min(s.maxst, s.stam + r)
        if s.cls == "sage" and s.focus < s.maxfoc: s.focus = min(s.maxfoc, s.focus + 0.018)
        if g.state_name == "play" and s.t % 6 == 0: pass
        mode = SETTINGS["runmode"]
        ixr = c["x"]; ix = (ixr if mode == "analog" and abs(ixr) > 0.25 else (1.0 if ixr > 0.25 else -1.0 if ixr < -0.25 else 0.0))
        if mode == "analog" and ix: ix = math.copysign(0.45 + 0.55 * min(1.0, (abs(ixr) - 0.25) / 0.6), ix)
        iy = c["y"] if abs(c["y"]) > 0.5 else 0.0
        # inputs -> buffered actions
        for k in ("light", "heavy", "dodge", "guard", "skill", "flask"):
            if pad.pressed(k): s.want(k)
        jp = pad.pressed("jump"); jh = pad.held("jump")
        st = s.state
        if st == "free": s.upd_free(ix, iy, jp, jh)
        elif st == "act": s.upd_act(ix, iy, jp, jh)
        elif st == "roll": s.upd_roll()
        elif st == "guard": s.upd_guard(ix)
        elif st == "hurt": s.upd_hurt()
        elif st == "drink": s.upd_drink(ix)
        elif st == "kantele": s.upd_kantele()
        elif st == "draw": s.upd_draw(ix)
        # safe spot tracking
        if s.on_ground and not s.climb and s.state in ("free", "act", "guard") and not hazard_at(g.wd, s):
            s.safe_t += 1
            if s.safe_t > 24 and g.safe_ok(s): s.safe = (s.x, s.y)
        else: s.safe_t = 0 if not s.on_ground else s.safe_t
    # --- states ---
    def phys(s, fric=0.82, grav=True):
        g = s.g
        if grav: s.vy = min(MAX_FALL, s.vy + GRAV)
        if s.on_ground: s.vx *= fric
        move_body(g.wd, s)
    def upd_free(s, ix, iy, jp, jh):
        g = s.g; pad = s.pad
        # buffered actions
        if s.buf and not s.climb:
            b = s.buf
            if s.try_action(b): s.buf = None; return
            if b in ("flask",) : s.buf = None
        if s.climb and s.buf in ("dodge",) and s.try_action("dodge"): s.buf = None; return
        # interaction
        if pad.pressed("up") and s.nearby and not ladder_overlap(g.wd, s):
            g.interact(s, s.nearby)
        drop = bool(pad.held("down") and jp)
        if drop: jp = False
        if ix: s.face = 1 if ix > 0 else -1
        s.run_speed = RUN
        ev = walk_step(g.wd, s, ix, iy, jp, jh, s.dj_ok, drop)
        if "jump" in ev: sfx("jump", 0.5); g.parts.burst(s.x, s.y, (200, 200, 190), 3, 0.6, 10, 1, 0.0)
        if "djump" in ev: sfx("djump", 0.6); g.parts.burst(s.x, s.y, (190, 230, 255), 8, 1.0, 14, 1, 0.0)
        if "land" in ev: sfx("land", 0.4)
        s.combo_t = s.combo_t  # keep
    def upd_act(s, ix, iy, jp, jh):
        g = s.g; a = s.act; t = s.st_t; s.st_t += 1; kind = a["kind"]
        st, ac, rc = a["st"], a["ac"], a["rc"]
        total = st + ac + rc
        # movement during action
        if kind == "flip":
            s.vy = min(MAX_FALL, s.vy + GRAV); move_body(g.wd, s)
            if t == st:
                s.fire_arrow(10 * s.bowm, 3.4, 0, 0, poise=8, n=3, spread=0.12)
            if s.on_ground and t > 6: s.vx *= 0.7
            if t >= total or (s.on_ground and t > 10): s.end_act()
            return
        if t < st: s.vx *= 0.8
        if st <= t < st + ac and "step" in a: s.vx = s.face * a["step"]
        s.vy = min(MAX_FALL, s.vy + GRAV); 
        if s.on_ground: s.vx *= 0.85
        move_body(g.wd, s)
        # fire at the first active frame
        if t == st:
            if "fire" in a: s.fire_spell(a)
            elif kind == "nova": s.nova(a)
            elif "rel" in a:
                tags = set(a.get("tags", ())); dm = a["dmg"] * s.dmgm
                s.atk = Atk(a["rel"], dm, a["kb"], tags, a["poise"] + s.poise_b, pid=s.idx)
                sfx(a.get("snd", "swing"), 0.8)
        if "rel" in a and st <= t < st + ac and s.atk: s.melee_hits()
        if t == st + ac: s.atk = None
        # cancel into roll after active frames
        if t >= st + ac and s.buf == "dodge" and s.stam >= 1:
            s.atk = None; s.act = None
            if s.try_action("dodge"): s.buf = None; return
        if t >= st + ac and s.buf in ("light", "heavy", "guard", "skill", "flask") and t >= st + ac + max(2, rc // 3):
            s.atk = None; s.act = None; s.state = "free"
            if s.try_action(s.buf): s.buf = None; return
        if s.atk is None and t >= st and kind == "light" and "rel" in a: s.combo_t = 22 + rc
        if t >= total: s.end_act()
    def end_act(s):
        s.state = "free"; s.act = None; s.atk = None
    def melee_hits(s):
        g = s.g; a = s.atk
        rect = a.rect(s.x, s.y, s.face)
        for e in g.enemies:
            if e.dead or e.hidden or e.invuln or id(e) in a.hit: continue
            if ov(rect, e.hurt_rect()):
                a.hit.add(id(e)); tg = set(a.tags)
                dm = a.dmg
                if e.take(dm, a.kb * s.face, a.poise, s, tg, 0.0):
                    if s.cls == "sage": s.focus = min(s.maxfoc, s.focus + 3)
                    if "bash" in a.tags: e.stun = max(e.stun, 40) if not e.boss and e.poise_max < 100 else e.stun
        g.poke_secret(rect)
        for p in g.projs:
            if p.enemy and p.kind in ("orb", "spit") and ov(rect, p.rect()):
                p.dead = True; g.parts.burst(p.x, p.y, p.col, 8, 1.6, 16); sfx("parry", 0.5)
    def fire_spell(s, a):
        g = s.g; sp = 3.6
        if a["fire"] == "bolt":
            g.projs.append(Proj("bolt", s.x + s.face * 8, s.y - 13, s.face * sp, 0, a["dmg"] * s.spellm, 6, 5, enemy=False, life=70, tags=(), pid=s.idx, poise=7, col=(150, 255, 230)))
        else:
            g.projs.append(Proj("orb", s.x + s.face * 8, s.y - 13, s.face * 2.4, 0, a["dmg"] * s.spellm, 11, 11, enemy=False, life=110, tags=("heavy",), pid=s.idx, pierce=2, poise=22, col=(110, 255, 210)))
        sfx(a.get("snd", "bolt"), 0.8); g.parts.burst(s.x + s.face * 9, s.y - 13, (150, 255, 230), 4, 0.8, 10)
    def nova(s, a):
        g = s.g
        rect = (s.x - 28, s.y - 30, 56, 32); sfx("boom", 0.7); g.shake(2, 6)
        for k in range(18):
            ang = k / 18 * 6.283; g.parts.add(s.x, s.y - 12, math.cos(ang) * 2.0, math.sin(ang) * 1.4, 18, (150, 255, 230), 2)
        for e in g.enemies:
            if e.dead or e.hidden or e.invuln: continue
            if ov(rect, e.hurt_rect()):
                if e.take(a["dmg"] * s.spellm, 4.5 * (1 if e.x >= s.x else -1), 40, s, ("heavy",), 1.5): s.focus = min(s.maxfoc, s.focus + 3)
        for p in g.projs:
            if p.enemy and ov(rect, p.rect()): p.dead = True; g.parts.burst(p.x, p.y, p.col, 6, 1.4, 14)
    def fire_arrow(s, dmg, speed, vy, charge, poise=8, n=1, spread=0.0):
        g = s.g
        for k in range(n):
            ang = (k - (n - 1) / 2) * spread
            vx = math.cos(ang) * speed * s.face; vyy = math.sin(ang) * speed + vy
            g.projs.append(Proj("parrow", s.x + s.face * 8, s.y - 12, vx, vyy, dmg, 8, 4, enemy=False, life=70, pid=s.idx, poise=poise,
                                pierce=2 if charge else 0, tags=("heavy",) if charge else (), col=(240, 230, 190)))
        sfx("arrow", 0.8)
    def upd_roll(s):
        g = s.g; r = ROLL[s.cls]; t = s.st_t; s.st_t += 1
        f = 1.0 - 0.45 * (t / r["dur"])
        s.vx = s.roll_dir * r["sp"] * f
        if r["i0"] <= t <= r["i1"]: s.inv = max(s.inv, 2)
        s.vy = min(MAX_FALL, s.vy + GRAV); move_body(g.wd, s)
        if s.wall: s.vx = 0
        if t % 5 == 2 and s.on_ground: g.parts.add(s.x - s.roll_dir * 4, s.y - 1, 0, -0.2, 10, (170, 170, 160), 1)
        if t >= r["dur"]:
            s.state = "free"; s.vx *= 0.3
            s.inv = max(s.inv, 0)
    def upd_guard(s, ix):
        g = s.g
        s.guard_t += 1; s.vx *= 0.6
        if abs(ix) > 0: s.face = 1 if ix > 0 else -1; s.vx = ix * 0.5
        s.vy = min(MAX_FALL, s.vy + GRAV); move_body(g.wd, s)
        if not s.pad.held("guard") or not s.on_ground: s.state = "free"; s.guard_t = 0; return
        if s.buf == "dodge": 
            if s.try_action("dodge"): s.buf = None
        elif s.buf in ("light", "heavy", "skill"):
            nm = s.buf; s.state = "free"
            if s.try_action(nm): s.buf = None
    def upd_hurt(s):
        g = s.g; s.stun -= 1
        s.vy = min(MAX_FALL, s.vy + GRAV); s.vx *= 0.92; move_body(g.wd, s)
        if s.stun <= 0 and s.on_ground or s.stun < -20: s.state = "free"; s.stun = 0
    def upd_drink(s, ix):
        g = s.g; t = s.st_t; s.st_t += 1
        s.vx = ix * 0.35 if ix else s.vx * 0.5
        s.vy = min(MAX_FALL, s.vy + GRAV); move_body(g.wd, s)
        if t == 24:
            s.hp = min(s.maxhp, s.hp + s.maxhp * s.flask_pct * D()["flask"]); sfx("heal", 0.8)
            g.parts.burst(s.x, s.y - 10, (255, 220, 140), 10, 1.0, 22, 1, -0.02, 0.5)
        if t >= 42: s.state = "free"
        elif s.buf == "dodge" and t >= 24:
            if s.try_action("dodge"): s.buf = None
    def upd_kantele(s):
        g = s.g; t = s.st_t; s.st_t += 1; s.vx = 0
        s.vy = min(MAX_FALL, s.vy + GRAV); move_body(g.wd, s)
        if t % 8 == 0: sfx("kantele", 0.5); g.parts.burst(s.x, s.y - 20, (255, 235, 150), 3, 0.7, 24, 1, -0.02, 0.4)
        if t == 40:
            for p in g.players:
                if p.alive() and abs(p.x - s.x) < 110 and abs(p.y - s.y) < 70:
                    p.hp = min(p.maxhp, p.hp + p.maxhp * 0.22); p.ward = 1800; p.recalc()
                    g.parts.burst(p.x, p.y - 10, (255, 235, 150), 12, 1.2, 28, 1, -0.02, 0.6)
            sfx("heal", 0.9)
        if t >= 54: s.state = "free"
    def upd_draw(s, ix):
        g = s.g; s.draw_t += 1; s.vx *= 0.5
        if ix: s.face = 1 if ix > 0 else -1
        s.vy = min(MAX_FALL, s.vy + GRAV); move_body(g.wd, s)
        if s.draw_t == 1: s.spend(14)
        held = s.pad.held("skill")
        if (not held and s.draw_t >= 6) or s.draw_t > 70:
            ch = s.draw_t >= 26
            if ch: s.fire_arrow(34 * s.bowm, 5.2, 0, 1, poise=26)
            else: s.fire_arrow(14 * s.bowm, 3.8, 0, 0, poise=8)
            g.parts.burst(s.x + s.face * 10, s.y - 12, (255, 255, 255), 3, 0.8, 8)
            s.state = "act"; s.st_t = 0; s.act = dict(kind="bowrec", st=99, ac=0, rc=0); s.act["st"] = 0; s.act["rc"] = 8 if ch is False else 14
            s.act["ac"] = 0; s.act["st"] = 0
        elif s.buf == "dodge" and s.try_action("dodge"): s.buf = None
    def projs_hit_player_setup(s): pass
    # ----- drawing -----
    def anim_name(s):
        st = s.state
        if st == "down": return "down", 0
        if st == "roll": return "roll", min(3, s.st_t * 4 // ROLL[s.cls]["dur"])
        if st == "hurt": return "hurt", 0
        if st == "drink": return "drink", (s.st_t // 8)
        if st == "guard": return "guard", 0
        if st == "kantele": return "kantele", s.st_t // 6
        if st == "draw": return "shoot", 0
        if st == "act":
            a = s.act; k = a["kind"]; t = s.st_t
            if k == "flip": return "shoot", 1
            if k == "bowrec": return "shoot", 1
            ph = 0 if t < a["st"] else (1 if t < a["st"] + a["ac"] else 2)
            if k == "bash": return "bash", 0 if ph == 0 else 1
            if k == "nova": return "cast", 0 if ph == 0 else 1
            if "fire" in a:
                return ("cast", 0 if ph == 0 else 1) if a["fire"] == "orb" else ("atk1", ph)
            return a["anim"], ph
        if s.climb: return "climb", (s.t // 6) % 2
        if not s.on_ground: return ("jump" if s.vy < 0 else "fall"), 0
        if abs(s.vx) > 0.3: return "run", (s.t // 5) % 4
        return "idle", (s.t // 24) % 2
    def draw(s, surf, cx, cy):
        a, t = s.anim_name()
        flash = s.flash > 0 and (s.flash % 2 == 0)
        tint = P2_TINT[s.cls] if s.idx == 1 else None
        spr = player_frame(s.cls, a, t, flash, tint)
        if s.face < 0: spr = flipped(spr)
        x = int(s.x - cx); y = int(s.y - cy)
        if s.inv > 0 and s.state not in ("roll", "hurt") and (s.t // 3) % 2 == 0 and s.inv < 40: spr = spr.copy(); spr.set_alpha(120)
        w, h = spr.get_size()
        if s.state == "down": spr = spr.copy(); spr.set_alpha(180 if (s.t // 20) % 2 else 230)
        surf.blit(spr, (x - w // 2, y - h + 2))
        if s.state == "guard" or s.blocked_flash:
            pass
        if s.state == "guard" and s.guard_t < int(11 * D()["parry"]):
            pygame.draw.circle(surf, (255, 240, 170), (x + s.face * 9, y - 12), 3 + s.guard_t // 3, 1)
        if s.state == "draw" and s.draw_t > 4:
            f = min(1.0, s.draw_t / 26.0)
            pygame.draw.line(surf, (255, 255, 255) if f >= 1 else (200, 200, 140), (x + s.face * 6, y - 22), (x + s.face * (6 + int(10 * f)), y - 22), 1)
            if f >= 1 and (s.t // 3) % 2 == 0: surf.fill((255, 255, 255), (x + s.face * 18, y - 23, 2, 2))
        if s.g.coop and s.alive():
            col = P2_TINT[s.cls] if s.idx == 1 else (255, 220, 120)
            pygame.draw.polygon(surf, col, [(x - 2, y - 33), (x + 2, y - 33), (x, y - 30)])
        if s.atk and DEBUG_BOXES:
            r = s.atk.rect(s.x, s.y, s.face); pygame.draw.rect(surf, (0, 255, 0), (r[0] - cx, r[1] - cy, r[2], r[3]), 1)
        if s.state == "down":
            f = s.down_t / 1200.0
            pygame.draw.rect(surf, (60, 20, 20), (x - 8, y - 34, 16, 3)); pygame.draw.rect(surf, (230, 70, 70), (x - 8, y - 34, int(16 * f), 3))
            if s.revive_t > 0: pygame.draw.rect(surf, (140, 255, 160), (x - 8, y - 38, int(16 * s.revive_t / 70.0), 2))

def physical_pad(s, skip=None):
    """First non-keyboard pad. The always-present keyboard is never a silent P2."""
    for pad in s.pads.values():
        if pad is skip or pad is getattr(s, "kb", None):
            continue
        if getattr(pad, "kind", None) in ("kb", "idle"):
            continue
        return pad
    return None

def join_pad(s, pred):
    """A physical press wins over the keyboard when both ask on the same frame."""
    hits = [pad for pad in s.pads.values() if pred(pad)]
    for pad in hits:
        if getattr(pad, "kind", None) in ("gc", "js"):
            return pad
    return hits[0] if hits else None
