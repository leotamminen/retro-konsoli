# One jump model shared by players, bots, the fairness proof and the tests.
import math
import random

from .const import (
    ACCEL, CH_W, COYOTE, EY, FALL_Y, GLIDE_FALL, GRAV, JUMP_BUF, JUMP_CUT,
    JUMP_HOLD, JUMP_V, LEAD, MAX_FALL, PH, PW, RUN, SCROLL_MAX, SLOW_MUL,
    SPEED_RUN,
)


class Body:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.w = PW
        self.h = PH
        self.on_ground = False
        self.coyote = 0
        self.buf = 0
        self.air_jumps = 0
        self.air_max = 0
        self.slow = False
        self.glide = False
        self.speed = False
        self.stun = 0
        self.was_jump = False

    def feet(self):
        return self.y + self.h

    def copy_flags(self, other):
        self.slow = other.slow
        self.glide = other.glide
        self.speed = other.speed
        self.air_max = other.air_max


def move_toward(v, target, step):
    if v < target:
        return min(target, v + step)
    if v > target:
        return max(target, v - step)
    return v


def support_at(x, feet, solids, slop=2.6):
    for px, top, pw in solids:
        if px - 1 <= x <= px + pw + 1 and abs(feet - top) <= slop:
            return True
    return False


def step_body(b, ix, jump_held, jump_pressed, solids):
    """Advance one frame. solids are one-way platforms (x, top, w).

    Returns "jump", "airjump" or None. Vertical overlap with another player is
    not a solid: callers never pass players in as platforms, so nobody can
    stomp or stand on anybody else.
    """
    if b.stun > 0:
        b.stun -= 1
        ix = 0.0
        jump_pressed = False
        jump_held = False
    if b.on_ground:
        b.coyote = COYOTE
        b.air_jumps = b.air_max
    elif b.coyote > 0:
        b.coyote -= 1
    if jump_pressed:
        b.buf = JUMP_BUF
    elif b.buf > 0:
        b.buf -= 1

    rate = SPEED_RUN if b.speed else RUN
    if b.slow:
        rate *= SLOW_MUL
    if ix > 0.25:
        target = rate
    elif ix < -0.25:
        target = -rate
    else:
        target = 0.0
    accel = ACCEL * (SLOW_MUL if b.slow else 1.0)
    b.vx = move_toward(b.vx, target, accel)

    did = None
    if b.buf > 0 and b.stun <= 0:
        if b.coyote > 0:
            b.vy = JUMP_V
            b.coyote = 0
            b.buf = 0
            b.on_ground = False
            did = "jump"
        elif b.air_jumps > 0:
            b.air_jumps -= 1
            b.vy = JUMP_V
            b.buf = 0
            b.on_ground = False
            did = "airjump"
    released = (not jump_held) and b.was_jump
    b.was_jump = bool(jump_held)
    if released and b.vy < 0:
        b.vy *= JUMP_CUT
    if b.glide and jump_held and b.vy > GLIDE_FALL:
        b.vy = GLIDE_FALL
    else:
        b.vy = min(MAX_FALL, b.vy + GRAV)

    b.x += b.vx
    prev_bottom = b.feet()
    b.y += b.vy
    landed = None
    if b.vy >= 0:
        best = None
        left = b.x + 1
        right = b.x + b.w - 1
        for px, top, pw in solids:
            if right <= px or left >= px + pw:
                continue
            if prev_bottom <= top + 0.9 and b.feet() >= top:
                if best is None or top < best:
                    best = top
        if best is not None:
            b.y = best - b.h
            b.vy = 0.0
            b.on_ground = True
            b.air_jumps = b.air_max
            landed = best
        else:
            b.on_ground = False
    else:
        b.on_ground = False
    return did, landed


def air_needed(body, solids):
    """Falling, and no ledge close under the feet: a second jump can still save it."""
    if body.vy < 0.2:
        return False
    feet = body.feet()
    for dx in (0, 10, 18):
        if support_at(body.x + body.w * 0.5 + dx, feet + 8, solids, slop=10):
            return False
    return True


def ground_ends(body, solids, lead):
    """True when a point `lead` px past the right side has no ledge at foot height."""
    feet = body.feet()
    if not support_at(body.x + body.w * 0.5, feet, solids):
        return False
    return not support_at(body.x + body.w + lead, feet, solids)


def hazard_ahead(body, hazards, lead):
    feet = body.feet()
    x0 = body.x + 4
    x1 = body.x + body.w + lead
    for hx, hy, hw, hh in hazards:
        if hx < x1 and hx + hw > x0 and hy < feet + 2 and hy + hh > body.y + 2:
            return True
    return False


def next_ledge(body, solids):
    """Nearest platform that is not the one currently under the feet."""
    feet = body.feet()
    best = None
    for px, top, pw in solids:
        if px + pw < body.x + body.w - 4:
            continue
        if abs(top - feet) <= 2.6 and px <= body.x + 6:
            continue
        if best is None or px < best[0] - 0.1 or (abs(px - best[0]) < 0.1 and top < best[1]):
            best = (px, top, pw)
    return best


def _threat(body, solids, hazards, lead):
    if hazard_ahead(body, hazards, lead + 16):
        return True
    if not ground_ends(body, solids, lead):
        return False
    nxt = next_ledge(body, solids)
    # A lower ledge is a drop: keep running and fall. Jumping would overshoot it.
    if nxt is not None and nxt[1] > body.feet() + 8:
        return False
    return True


class Pilot:
    """Same jump choices for the fairness proof, couch bots and a dropped pad."""

    def __init__(self, skill=1.0, rng=None):
        self.skill = skill
        self.rng = rng or random.Random(0)
        self.hold = 0
        self.did_air = False

    def decide(self, body, solids, hazards, glide=False, air_jumps=0):
        if body.on_ground:
            self.did_air = False
        pressed = False
        held = False
        if self.hold > 0:
            self.hold -= 1
            held = True
        elif body.on_ground and _threat(body, solids, hazards, LEAD):
            if self.rng.random() <= self.skill:
                self.hold = JUMP_HOLD - 1
                held = True
                pressed = True
        if (not body.on_ground) and air_jumps > 0 and not self.did_air and body.vy > 0.2:
            # The extra jump is the recovery, so a sloppy runner still uses it.
            if (air_needed(body, solids) or _threat(body, solids, hazards, LEAD)) and self.rng.random() <= max(self.skill, 0.92):
                pressed = True
                held = True
                self.hold = max(self.hold, JUMP_HOLD // 2)
                self.did_air = True
        if glide and body.vy > GLIDE_FALL and not body.on_ground:
            held = True
        return 1.0, held, pressed


def ghost_steer(body, solids):
    """Stick axes for a ghost trying to settle on the nearest ledge. iy is -1 up."""
    best = None
    best_d = 1e9
    cx = body.x + body.w * 0.5
    fy = body.feet()
    for px, top, pw in solids:
        mx = px + pw * 0.5
        d = abs(mx - cx) + abs(top - fy) * 1.4
        if d < best_d:
            best_d = d
            best = (mx, top)
    if best is None:
        return 0.3, 0.4
    mx, top = best
    ix = 0.0 if abs(mx - cx) < 6 else (1.0 if mx > cx else -1.0)
    if top < fy - 6:
        iy = -1.0
    elif top > fy + 6:
        iy = 1.0
    else:
        iy = 0.0
    return ix, iy


def rect_hit(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


_GAP_CACHE = {}


def measure_gap(rise=0, lead=LEAD, hold=JUMP_HOLD, speed=False):
    """Largest gap, in pixels, a full jump can clear onto a ledge `rise` px higher.

    rise > 0 means the landing ledge is above the takeoff ledge.
    """
    key = (int(rise), int(lead), int(hold), bool(speed))
    hit = _GAP_CACHE.get(key)
    if hit is not None:
        return hit
    lo, hi = 0, 140
    best = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if clears_gap(mid, rise, lead, hold, speed):
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    _GAP_CACHE[key] = best
    return best


def clears_gap(gap, rise, lead=LEAD, hold=JUMP_HOLD, speed=False):
    b = Body()
    b.x = -lead - PW
    b.y = -PH
    b.vx = SPEED_RUN if speed else RUN
    b.speed = bool(speed)
    b.on_ground = True
    b.coyote = COYOTE
    a_left = b.x - 30
    solids = [(a_left, 0.0, -a_left), (float(gap), float(-rise), 120.0)]
    for f in range(180):
        step_body(b, 1.0, f < hold, f == 0, solids)
        if f > 2 and b.on_ground:
            top = -rise
            on_b = (b.x + b.w - 1) > gap and b.x < gap + 120 and abs(b.feet() - top) < 2.5
            return on_b
        if b.y > 120:
            return False
    return False


def chunk_platforms(chunk, origin=0.0):
    out = []
    for px, top, pw in chunk.plats:
        out.append((origin + px, top, pw))
    return out


def chunk_hazards(chunk, origin=0.0):
    out = []
    for hx, hy, hw, hh in chunk.hazards:
        out.append((origin + hx, hy, hw, hh))
    return out


def validate_chunk(chunk):
    """Prove a hand-built chunk is clearable with the game's own jump physics.

    Two checks, both using step_body:
    - every real gap is strictly inside the measured jump envelope
    - a perfect pilot holding right, from a standstill on the entry lip,
      crosses to the exit at the fastest scroll without falling or touching a thorn
    """
    if chunk.w < 64:
        raise AssertionError("%s: too narrow" % chunk.name)
    entry = _cover(chunk, 2, EY)
    exitp = _cover(chunk, chunk.w - 4, EY)
    if entry is None or entry[2] < 64:
        raise AssertionError("%s: entry ledge missing" % chunk.name)
    if exitp is None or exitp[2] < 48 or exitp[0] + exitp[2] < chunk.w - 1:
        raise AssertionError("%s: exit ledge missing" % chunk.name)
    for hx, hy, hw, hh in chunk.hazards:
        if hh > 14 or hw < 6:
            raise AssertionError("%s: thorn size" % chunk.name)
        if hx < 56:
            raise AssertionError("%s: thorn in the runway" % chunk.name)
        bottom = hy + hh
        sitting = False
        for px, top, pw in chunk.plats:
            if abs(bottom - top) <= 2.0 and hx < px + pw - 2 and hx + hw > px + 2:
                sitting = True
        if not sitting:
            raise AssertionError("%s: thorn is not standing on a ledge" % chunk.name)
    _lint_envelope(chunk)
    _run_pilot(chunk)
    return True


def _cover(chunk, x, top, slop=3.0):
    for p in chunk.plats:
        if p[0] - 0.1 <= x <= p[0] + p[2] + 0.1 and abs(p[1] - top) <= slop:
            return p
    return None


def _has_step(plats, a, b):
    gap_l = a[0] + a[2]
    gap_r = b[0]
    for c in plats:
        if c is a or c is b:
            continue
        if c[0] < gap_r - 4 and c[0] + c[2] > gap_l + 4:
            return True
    return False


def _lint_envelope(chunk):
    plats = list(chunk.plats)
    for a in plats:
        for b in plats:
            if b is a:
                continue
            gap = b[0] - (a[0] + a[2])
            if gap < 8 or _has_step(plats, a, b):
                continue
            rise = a[1] - b[1]
            if rise < -4:
                if gap > 20:
                    raise AssertionError("%s: drop of %spx is wider than a running fall" % (chunk.name, gap))
                continue
            limit = measure_gap(rise=max(0, int(round(rise))))
            if gap > limit - 6:
                raise AssertionError(
                    "%s: gap %spx rise %s exceeds jump envelope %s"
                    % (chunk.name, int(gap), int(rise), limit)
                )


def _run_pilot(chunk, speed=False):
    # The next chunk always begins with a ledge at EY, so the seam is ground.
    solids = chunk_platforms(chunk) + [(float(chunk.w), float(EY), 96.0)]
    hazards = chunk_hazards(chunk)
    b = Body()
    b.x = 6.0
    b.y = EY - PH
    b.vx = 0.0
    b.on_ground = True
    b.speed = bool(speed)
    pilot = Pilot(1.0, random.Random(0))
    cam = 0.0
    for frame in range(1100):
        b.speed = bool(speed)
        ix, held, pressed = pilot.decide(b, solids, hazards)
        step_body(b, ix, held, pressed, solids)
        cam += SCROLL_MAX
        if b.feet() > FALL_Y or b.y > EY + 80:
            raise AssertionError("%s: fell at frame %s x=%.1f y=%.1f" % (chunk.name, frame, b.x, b.y))
        if b.x + b.w < cam - 2:
            raise AssertionError("%s: scrolled off at frame %s" % (chunk.name, frame))
        for hx, hy, hw, hh in hazards:
            if rect_hit(b.x, b.y, b.w, b.h, hx, hy, hw, hh):
                raise AssertionError("%s: thorn at frame %s x=%.1f" % (chunk.name, frame, b.x))
        if b.x > chunk.w + 8 and b.on_ground and abs(b.feet() - EY) < 3:
            return
    raise AssertionError("%s: pilot did not reach the exit (x=%.1f y=%.1f ground=%s)" % (
        chunk.name, b.x, b.y, b.on_ground))


def nearest_platform(body, solids):
    best = None
    best_d = 1e9
    cx = body.x + PW * 0.5
    fy = body.feet()
    for px, top, pw in solids:
        mx = px + min(pw * 0.5, 40)
        d = math.hypot(mx - cx, top - fy)
        if d < best_d:
            best_d = d
            best = (px, top, pw)
    return best
