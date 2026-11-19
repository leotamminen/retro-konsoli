# Endless course: a fixed opening, then a shuffle of proved chunks, then a finish.
import random

from .chunks import ALKU, ALL_CHUNKS, BY_NAME, MAALI, POOL, validate_all
from .const import CH_W, CRUMBLE_TIME, FINISH_X, POWER_KINDS, SCROLL0, SCROLL_MAX, W
from .physics import mover_dx


class Coin:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.alive = True


class Pickup:
    def __init__(self, kind, x, y, shared=False):
        self.kind = kind
        self.x = float(x)
        self.y = float(y)
        self.alive = True
        self.t = 0
        self.shared = shared
        self.got = set()
        self.linger = 0


class Crumble:
    def __init__(self, x, top, w):
        self.x, self.top, self.w = float(x), float(top), float(w)
        self.timer = 0
        self.armed = False
        self.live = True
        self.stood = {}


class Mover:
    def __init__(self, x, top, w, amp, period):
        self.x, self.top, self.w = float(x), float(top), float(w)
        self.amp, self.period = float(amp), int(period)

    def at(self, frame):
        return self.x + mover_dx(frame, self.period, self.amp), self.top, self.w


class World:
    # Teach the new shapes while the scroll is still gentle, each once.
    OPENING = ("pikkukuilu", "portaat", "okapuu", "lasku", "murea", "liuku", "katto", "piikit", "haara")

    def __init__(self, rng=None, powers_on=None, power_freq=1.0):
        self.rng = rng or random.Random()
        validate_all()
        self.placed = []
        self.x_end = 0.0
        self.coins = []
        self.powers = []
        self.crumbles = []
        self.movers = []
        self.power_i = 0
        self.powers_on = powers_on
        self.power_freq = power_freq if power_freq > 0 else 0.0
        self.last_hard = False
        self.last_name = ""
        self.frame = 0
        self.done = False
        self.finish_x = None
        self.opening = list(self.OPENING)
        self._place(ALKU)
        self.ensure(0, SCROLL0)

    def _allowed(self, chunk, scroll):
        ramp = (scroll - SCROLL0) / max(0.001, SCROLL_MAX - SCROLL0)
        ramp = 0.0 if ramp < 0 else (1.0 if ramp > 1 else ramp)
        if chunk.tier >= 2 and ramp < 0.55:
            return False
        if chunk.tier == 1 and ramp < 0.15:
            return False
        if chunk.name == self.last_name:
            return False
        if self.last_hard and chunk.hard:
            return False
        return True

    def _pick(self, scroll):
        if self.opening:
            return BY_NAME[self.opening.pop(0)]
        choices = [c for c in POOL if self._allowed(c, scroll)]
        if not choices:
            choices = [c for c in POOL if c.tier == 0 and c.name != self.last_name] or list(POOL)
        ramp = (scroll - SCROLL0) / max(0.001, SCROLL_MAX - SCROLL0)
        bag = []
        for chunk in choices:
            weight = 4 - chunk.tier
            if ramp > 0.7 and chunk.tier >= 1:
                weight += 1
            bag.extend([chunk] * max(1, weight))
        return self.rng.choice(bag)

    def _place(self, chunk):
        origin = float(self.x_end)
        self.placed.append((origin, chunk))
        self.x_end += chunk.w
        self.last_hard = chunk.hard
        self.last_name = chunk.name
        for x, y in chunk.coins:
            self.coins.append(Coin(origin + x, y))
        enabled = [k for k in POWER_KINDS if self.powers_on is None or self.powers_on.get(k, True)]
        for x, y in chunk.powers:
            if not enabled or self.rng.random() > self.power_freq:
                continue
            kind = enabled[self.power_i % len(enabled)]
            self.power_i += 1
            self.powers.append(Pickup(kind, origin + x, y, shared=False))
        for x, top, w in chunk.crumbles:
            self.crumbles.append(Crumble(origin + x, top, w))
        for x, top, w, amp, period in chunk.movers:
            self.movers.append(Mover(origin + x, top, w, amp, period))
        if chunk.name == "maali":
            self.finish_x = origin + 70
            self.done = True

    def ensure(self, camera, scroll=None):
        if scroll is None:
            scroll = SCROLL0
        guard = 0
        while self.x_end < camera + W + CH_W * 2 and not self.done and guard < 48:
            guard += 1
            if self.x_end >= FINISH_X:
                self._place(MAALI)
                break
            self._place(self._pick(scroll))

    def arm_crumbles(self, players):
        # Each runner gets their own count. The leader crossing must not
        # drop the bridge under the people still walking up to it.
        for tile in self.crumbles:
            if not tile.live:
                continue
            highest = 0
            for player in players:
                body = player.body
                if player.state != "run" or not body.on_ground:
                    continue
                fx = body.x + body.w * 0.5
                fy = body.feet()
                if abs(fy - tile.top) <= 3 and tile.x - 2 <= fx <= tile.x + tile.w + 2:
                    n = tile.stood.get(player.idx, 0) + 1
                    tile.stood[player.idx] = n
                    highest = max(highest, n)
                    if n >= CRUMBLE_TIME:
                        tile.live = False
            if highest:
                tile.armed = True
                tile.timer = highest

    def advance(self):
        self.frame += 1

    def _near(self, x0, x1):
        for origin, chunk in self.placed:
            if origin + chunk.w < x0 or origin > x1:
                continue
            yield origin, chunk

    def solids_near(self, x0, x1):
        out = []
        for origin, chunk in self._near(x0, x1):
            for px, top, pw in chunk.plats:
                out.append((origin + px, top, pw))
        for tile in self.crumbles:
            if tile.live and tile.x + tile.w >= x0 and tile.x <= x1:
                out.append((tile.x, tile.top, tile.w))
        for slab in self.movers:
            x, top, w = slab.at(self.frame)
            if x + w >= x0 and x <= x1:
                out.append((x, top, w))
        return out

    def hazards_near(self, x0, x1):
        out = []
        for origin, chunk in self._near(x0, x1):
            for hx, hy, hw, hh in chunk.hazards:
                out.append((origin + hx, hy, hw, hh))
            for hx, hy, hw, hh in chunk.ceilings:
                out.append((origin + hx, hy, hw, hh))
        return out


def chunk_count():
    return len(ALL_CHUNKS)
