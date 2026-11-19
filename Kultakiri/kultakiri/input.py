# One pad, one player. SDL GameController first; raw hid-playstation if it is not mapped.
# Cross and Circle both jump. In the lobby Circle adds a CPU and Square removes one.
# Triangle opens settings, Options starts, Share goes back.
# The same layout for every player. Instance id, never a hard-coded joystick 0.
import pygame


def blank():
    return {"x": 0.0, "y": 0.0, "jump": False, "circle": False, "start": False, "back": False, "alt": False, "menu": False}


class Pad:
    # Linux hid-playstation / DualShock: Cross, Circle, Square, Triangle, L1, R1, L2, R2, Share, Options.
    RAW_JUMP = 0
    RAW_CIRCLE = 1
    RAW_TRIANGLE = 3
    RAW_SHARE = 8
    RAW_OPTIONS = 9

    def __init__(self, kind, dev=None, iid=None, joy=None):
        self.kind = kind
        self.dev = dev
        self.joy = joy
        self.prev = blank()
        self.cur = blank()
        self.desired = blank()
        self.script = kind == "script"
        self.auto = False
        self.skill = 1.0
        # Events, for pads whose d-pad never shows up in get_button/get_hat
        # (and for tests that post into the queue). Device state still wins
        # when it already reports a direction.
        self.held_keys = set()
        self.hat = (0, 0)
        self.axis_ev = {}
        self.gc_buttons = set()
        self.js_buttons = set()
        if kind == "kb":
            self.id = "kb"
        elif iid is not None:
            self.id = "js%d" % int(iid)
        else:
            self.id = "pad%d" % id(self)

    def on_key(self, key, down):
        if down:
            self.held_keys.add(key)
        else:
            self.held_keys.discard(key)

    def on_joy(self, ev):
        t = ev.type
        if t == pygame.JOYHATMOTION:
            value = getattr(ev, "value", (0, 0)) or (0, 0)
            try:
                hx, hy = value
            except (TypeError, ValueError):
                hx, hy = 0, 0
            # Hat +y is up. Our y is +1 down, same as the left stick.
            self.hat = (int(hx), -int(hy))
        elif t == pygame.JOYAXISMOTION:
            try:
                val = float(ev.value)
            except (TypeError, ValueError):
                return
            if abs(val) > 1.5:
                val = val / 32768.0
            self.axis_ev[int(ev.axis)] = val
        elif t in (pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLERBUTTONUP):
            self._set_button(self.gc_buttons, ev, t == pygame.CONTROLLERBUTTONDOWN)
        elif t in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
            self._set_button(self.js_buttons, ev, t == pygame.JOYBUTTONDOWN)

    def _set_button(self, bucket, ev, down):
        try:
            button = int(ev.button)
        except (TypeError, ValueError):
            return
        if down:
            bucket.add(button)
        else:
            bucket.discard(button)

    def _event_stick(self):
        """Direction from the event queue, used when the device read is neutral."""
        x = float(self.axis_ev.get(0, 0.0))
        y = float(self.axis_ev.get(1, 0.0))
        hx, hy = self.hat
        if hx or hy:
            x, y = float(hx), float(hy)
        if pygame.CONTROLLER_BUTTON_DPAD_LEFT in self.gc_buttons:
            x = -1.0
        if pygame.CONTROLLER_BUTTON_DPAD_RIGHT in self.gc_buttons:
            x = 1.0
        if pygame.CONTROLLER_BUTTON_DPAD_UP in self.gc_buttons:
            y = -1.0
        if pygame.CONTROLLER_BUTTON_DPAD_DOWN in self.gc_buttons:
            y = 1.0
        return x, y

    def _merge_buttons(self, c):
        gc, js = self.gc_buttons, self.js_buttons
        if pygame.CONTROLLER_BUTTON_A in gc or Pad.RAW_JUMP in js:
            c["jump"] = True
        if pygame.CONTROLLER_BUTTON_B in gc or Pad.RAW_CIRCLE in js:
            c["circle"] = True
            c["jump"] = True
        if pygame.CONTROLLER_BUTTON_X in gc or 2 in js:
            c["menu"] = True
        if pygame.CONTROLLER_BUTTON_Y in gc or Pad.RAW_TRIANGLE in js:
            c["alt"] = True
        if pygame.CONTROLLER_BUTTON_START in gc or Pad.RAW_OPTIONS in js:
            c["start"] = True
        if pygame.CONTROLLER_BUTTON_BACK in gc or Pad.RAW_SHARE in js:
            c["back"] = True

    def poll(self, ks):
        c = blank()
        try:
            if self.kind == "kb":
                def down(code):
                    return bool(ks[code]) or code in self.held_keys
                right = down(pygame.K_RIGHT) or down(pygame.K_d)
                left = down(pygame.K_LEFT) or down(pygame.K_a)
                down_k = down(pygame.K_DOWN) or down(pygame.K_s)
                up = down(pygame.K_UP) or down(pygame.K_w)
                c["x"] = float(bool(right)) - float(bool(left))
                c["y"] = float(bool(down_k)) - float(bool(up))
                c["circle"] = down(pygame.K_z)
                c["jump"] = down(pygame.K_x) or down(pygame.K_SPACE) or down(pygame.K_z)
                c["start"] = down(pygame.K_RETURN) or down(pygame.K_KP_ENTER)
                c["back"] = down(pygame.K_BACKSPACE) or down(pygame.K_TAB)
                c["alt"] = down(pygame.K_c)
                c["menu"] = down(pygame.K_v)
            elif self.kind == "gc":
                g = self.dev

                def gb(button):
                    try:
                        return bool(g.get_button(button))
                    except (pygame.error, ValueError, OverflowError, SystemError, AttributeError, TypeError):
                        return False

                try:
                    ax = g.get_axis(pygame.CONTROLLER_AXIS_LEFTX) / 32768.0
                    ay = g.get_axis(pygame.CONTROLLER_AXIS_LEFTY) / 32768.0
                except (pygame.error, ValueError, TypeError, ZeroDivisionError, AttributeError):
                    ax, ay = 0.0, 0.0
                if gb(pygame.CONTROLLER_BUTTON_DPAD_LEFT):
                    ax = -1.0
                if gb(pygame.CONTROLLER_BUTTON_DPAD_RIGHT):
                    ax = 1.0
                if gb(pygame.CONTROLLER_BUTTON_DPAD_UP):
                    ay = -1.0
                if gb(pygame.CONTROLLER_BUTTON_DPAD_DOWN):
                    ay = 1.0
                c["x"], c["y"] = ax, ay
                c["circle"] = gb(pygame.CONTROLLER_BUTTON_B)
                c["jump"] = gb(pygame.CONTROLLER_BUTTON_A) or gb(pygame.CONTROLLER_BUTTON_B)
                c["start"] = gb(pygame.CONTROLLER_BUTTON_START)
                c["back"] = gb(pygame.CONTROLLER_BUTTON_BACK)
                c["alt"] = gb(pygame.CONTROLLER_BUTTON_Y)
                c["menu"] = gb(pygame.CONTROLLER_BUTTON_X)
            elif self.kind == "js":
                j = self.dev
                ax = j.get_axis(0) if j.get_numaxes() > 0 else 0.0
                ay = j.get_axis(1) if j.get_numaxes() > 1 else 0.0
                if j.get_numhats() > 0:
                    hx, hy = j.get_hat(0)
                    if hx:
                        ax = float(hx)
                    if hy:
                        ay = -float(hy)
                c["x"], c["y"] = ax, ay
                nb = j.get_numbuttons()

                def b(i):
                    return nb > i and bool(j.get_button(i))

                c["circle"] = b(Pad.RAW_CIRCLE)
                c["jump"] = b(Pad.RAW_JUMP) or b(Pad.RAW_CIRCLE)
                c["menu"] = b(2)
                c["alt"] = b(Pad.RAW_TRIANGLE)
                c["back"] = b(Pad.RAW_SHARE)
                c["start"] = b(Pad.RAW_OPTIONS)
            elif self.kind == "script":
                c.update(self.desired)
                c["x"] = float(c.get("x", 0.0))
                c["y"] = float(c.get("y", 0.0))
            ex, ey = self._event_stick()
            if abs(c["x"]) < 0.28 and abs(ex) >= 0.28:
                c["x"] = ex
            if abs(c["y"]) < 0.45 and abs(ey) >= 0.45:
                c["y"] = ey
            self._merge_buttons(c)
        except (pygame.error, SystemError, AttributeError, ValueError, TypeError, OverflowError):
            c = blank()
        if abs(c["x"]) < 0.28:
            c["x"] = 0.0
        if abs(c["y"]) < 0.45:
            c["y"] = 0.0
        self.prev = self.cur
        self.cur = c

    def pressed(self, key):
        return bool(self.cur.get(key)) and not bool(self.prev.get(key))

    def held(self, key):
        return bool(self.cur.get(key))


class ScriptPad(Pad):
    def __init__(self, name):
        Pad.__init__(self, "script", iid=None)
        self.id = name
        self.script = True
