# One pad, one player. SDL GameController first; raw hid-playstation if it is not mapped.
# Cross and Circle are the action (join, throw löyly). Square cycles CPU players.
# Triangle opens settings, Options starts, Share goes back.
# The same layout for every player. Instance id, never a hard-coded joystick 0.
# "jump" is the action button. "cpu" is Square.
import pygame


def _safe_button(dev, name):
    idx = getattr(pygame, name, None)
    if idx is None or idx < 0:
        return False
    try:
        return bool(dev.get_button(idx))
    except Exception:
        return False


def blank():
    return {"x": 0.0, "y": 0.0, "jump": False, "start": False, "back": False, "alt": False, "cpu": False}


class Pad:
    # Linux hid-playstation / DualShock: Cross, Circle, Square, Triangle, L1, R1, L2, R2, Share, Options.
    RAW_JUMP = 0
    RAW_CIRCLE = 1
    RAW_SQUARE = 2
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
        if kind == "kb":
            self.id = "kb"
        elif iid is not None:
            self.id = "js%d" % int(iid)
        else:
            self.id = "pad%d" % id(self)

    def poll(self, ks):
        c = blank()
        try:
            if self.kind == "kb":
                right = ks[pygame.K_RIGHT] or ks[pygame.K_d]
                left = ks[pygame.K_LEFT] or ks[pygame.K_a]
                down = ks[pygame.K_DOWN] or ks[pygame.K_s]
                up = ks[pygame.K_UP] or ks[pygame.K_w]
                c["x"] = float(bool(right)) - float(bool(left))
                c["y"] = float(bool(down)) - float(bool(up))
                c["jump"] = bool(ks[pygame.K_x] or ks[pygame.K_z] or ks[pygame.K_SPACE])
                c["start"] = bool(ks[pygame.K_RETURN] or ks[pygame.K_KP_ENTER])
                c["back"] = bool(ks[pygame.K_BACKSPACE] or ks[pygame.K_TAB])
                c["alt"] = bool(ks[pygame.K_c])
                c["cpu"] = bool(ks[pygame.K_q])
            elif self.kind == "gc":
                g = self.dev
                ax = g.get_axis(pygame.CONTROLLER_AXIS_LEFTX) / 32768.0
                ay = g.get_axis(pygame.CONTROLLER_AXIS_LEFTY) / 32768.0
                if _safe_button(g, "CONTROLLER_BUTTON_DPAD_LEFT"):
                    ax = -1.0
                if _safe_button(g, "CONTROLLER_BUTTON_DPAD_RIGHT"):
                    ax = 1.0
                if _safe_button(g, "CONTROLLER_BUTTON_DPAD_UP"):
                    ay = -1.0
                if _safe_button(g, "CONTROLLER_BUTTON_DPAD_DOWN"):
                    ay = 1.0
                c["x"], c["y"] = ax, ay
                c["jump"] = bool(g.get_button(pygame.CONTROLLER_BUTTON_A) or g.get_button(pygame.CONTROLLER_BUTTON_B))
                c["start"] = bool(g.get_button(pygame.CONTROLLER_BUTTON_START))
                c["back"] = bool(g.get_button(pygame.CONTROLLER_BUTTON_BACK))
                c["alt"] = bool(g.get_button(pygame.CONTROLLER_BUTTON_Y))
                c["cpu"] = bool(g.get_button(pygame.CONTROLLER_BUTTON_X))
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

                c["jump"] = b(Pad.RAW_JUMP) or b(Pad.RAW_CIRCLE)
                c["cpu"] = b(Pad.RAW_SQUARE)
                c["alt"] = b(Pad.RAW_TRIANGLE)
                c["back"] = b(Pad.RAW_SHARE)
                c["start"] = b(Pad.RAW_OPTIONS)
            elif self.kind == "script":
                c.update(self.desired)
                c["x"] = float(c.get("x", 0.0))
                c["y"] = float(c.get("y", 0.0))
        except (pygame.error, SystemError, AttributeError):
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
