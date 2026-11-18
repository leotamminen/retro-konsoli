# Endless course: a fixed opening, then a shuffle of proved chunks, then a finish.
import random

from .chunks import ALKU, ALL_CHUNKS, BY_NAME, MAALI, POOL, validate_all
from .const import CH_W, FINISH_X, POWER_KINDS, W


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


class World:
    OPENING = ("tasamaa", "pikkukuilu", "kolikot", "okapuu", "nousu", "tasamaa")

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        validate_all()
        self.placed = []
        self.x_end = 0.0
        self.coins = []
        self.powers = []
        self.power_i = 0
        self.last_hard = False
        self.done = False
        self.finish_x = None
        self.opening = list(self.OPENING)
        self._place(ALKU)
        self.ensure(0)

    def _pick(self):
        if self.opening:
            return BY_NAME[self.opening.pop(0)]
        bag = []
        for chunk in POOL:
            if self.last_hard and chunk.hard:
                continue
            bag.extend([chunk] * (1 if chunk.hard else 3))
        if not bag:
            bag = [c for c in POOL if not c.hard] or list(POOL)
        choice = self.rng.choice(bag)
        for _ in range(6):
            if not self.placed or choice.name != self.placed[-1][1].name:
                break
            choice = self.rng.choice(bag)
        return choice

    def _place(self, chunk):
        origin = float(self.x_end)
        self.placed.append((origin, chunk))
        self.x_end += chunk.w
        self.last_hard = chunk.hard
        for x, y in chunk.coins:
            self.coins.append(Coin(origin + x, y))
        shared = chunk.name == "alku"
        for x, y in chunk.powers:
            kind = POWER_KINDS[self.power_i % len(POWER_KINDS)]
            self.power_i += 1
            self.powers.append(Pickup(kind, origin + x, y, shared=shared))
        if chunk.name == "maali":
            self.finish_x = origin + 70
            self.done = True

    def ensure(self, camera):
        guard = 0
        while self.x_end < camera + W + CH_W * 2 and not self.done and guard < 48:
            guard += 1
            if self.x_end >= FINISH_X:
                self._place(MAALI)
                break
            self._place(self._pick())

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
        return out

    def hazards_near(self, x0, x1):
        out = []
        for origin, chunk in self._near(x0, x1):
            for hx, hy, hw, hh in chunk.hazards:
                out.append((origin + hx, hy, hw, hh))
        return out


def chunk_count():
    return len(ALL_CHUNKS)
