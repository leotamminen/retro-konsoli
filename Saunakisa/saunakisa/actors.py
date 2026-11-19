# Bathers, benches, and the little choices that cook you.
from .const import (
    ACCEL, BODY, CLIMB_SPEED, FAINT_KEEP, FPS, HEAT_MAX, HEAT_RATE,
    INSIDE, LOYLY_CD, LOYLY_OTHER, LOYLY_ROOM, LOYLY_SELF, OLUT_COOL, ORDER,
    PLACES, POINT_RATE, ROOM_MULT0, ROOM_MULT1, START_HEAT, STOVE_X,
    TOWEL_COOL, TOWEL_TIME, WALK,
)
from .input import blank


def heat_rate(place, room_heat):
    base = HEAT_RATE[place]
    if base <= 0.0:
        return base
    mult = ROOM_MULT0 + (room_heat / 100.0) * ROOM_MULT1
    return base * mult


def _hotter(a, b, room_heat):
    if heat_rate(a, room_heat) >= heat_rate(b, room_heat):
        return a
    return b


class Player:
    def __init__(self, idx, pad):
        self.idx = idx
        self.pad = pad
        self.place = "floor"
        self.x = 150.0
        self.y = float(PLACES["floor"]["y"])
        self.vx = 0.0
        self.mode = "move"
        self.face = 1
        self.heat = START_HEAT
        self.score = 0.0
        self.bank = 0
        self.wins = 0
        self.faints = 0
        self.round_points = 0
        self.cool_t = 0
        self.loyly_cd = 0
        self.climb_to = "floor"
        self.climb_t = 0
        self.climb_dur = 1
        self.climb_y0 = 0.0
        self.climb_x0 = 0.0
        self.anim = 0
        self.got_bonus = False

    def reset_round(self, place, x):
        self.place = place
        self.x = float(x)
        self.y = float(PLACES[place]["y"])
        self.vx = 0.0
        self.mode = "move"
        self.face = 1
        self.heat = START_HEAT
        self.score = 0.0
        self.round_points = 0
        self.cool_t = 0
        self.loyly_cd = 0
        self.climb_t = 0
        self.got_bonus = False
        self.anim = 0

    @property
    def inside(self):
        if self.mode == "faint":
            return False
        if self.mode == "climb":
            return self.place in INSIDE or self.climb_to in INSIDE
        return self.place in INSIDE


def _enter(player, place, x):
    player.place = place
    player.x = float(x)
    player.y = float(PLACES[place]["y"])
    player.vx = 0.0
    player.mode = "move"


def _start_climb(player, dest):
    spec = PLACES[dest]
    player.mode = "climb"
    player.climb_to = dest
    player.climb_t = 0
    player.climb_y0 = player.y
    player.climb_x0 = player.x
    dist = abs(spec["y"] - player.y)
    player.climb_dur = max(8, int(dist / CLIMB_SPEED))


def _arrive(player):
    dest = player.climb_to
    spec = PLACES[dest]
    player.mode = "move"
    player.place = dest
    player.x = float(spec["climb_x"])
    player.y = float(spec["y"])
    player.vx = 0.0


def step_player(player, ix, iy, act, room):
    """One frame of feet, heat and points. Returns a list of event names."""
    events = []
    if player.loyly_cd:
        player.loyly_cd -= 1
    if player.cool_t:
        player.cool_t -= 1
    if player.mode == "faint":
        player.anim += 1
        return events

    if player.mode == "climb":
        player.climb_t += 1
        dest = PLACES[player.climb_to]
        k = min(1.0, player.climb_t / float(player.climb_dur))
        player.y = player.climb_y0 + (dest["y"] - player.climb_y0) * k
        player.x = player.climb_x0 + (dest["climb_x"] - player.climb_x0) * k
        player.face = -1 if dest["climb_x"] < player.climb_x0 else 1
        if player.climb_t >= player.climb_dur:
            _arrive(player)
    else:
        spec = PLACES[player.place]
        if ix:
            player.vx += ix * ACCEL
            if player.vx > WALK:
                player.vx = WALK
            elif player.vx < -WALK:
                player.vx = -WALK
            player.face = 1 if ix > 0 else -1
        else:
            player.vx *= 0.45
            if abs(player.vx) < 0.08:
                player.vx = 0.0
        player.x += player.vx
        if player.x < spec["x0"]:
            player.x = float(spec["x0"])
            player.vx = 0.0
        elif player.x > spec["x1"]:
            player.x = float(spec["x1"])
            player.vx = 0.0
        player.y = float(spec["y"])

        moved = False
        if spec["left"] and player.x <= spec["x0"] + 0.6 and ix < -0.2:
            land = PLACES[spec["left"]]
            _enter(player, spec["left"], land["x1"] - 2)
            moved = True
            if spec["left"] == "avanto":
                events.append("avanto")
            elif player.place == "porch":
                events.append("exit")
        elif spec["right"] and player.x >= spec["x1"] - 0.6 and ix > 0.2:
            land = PLACES[spec["right"]]
            spot = land["x0"] + 4 if spec["right"] != "avanto" else land["x1"] - 2
            if spec["right"] == "floor":
                spot = land["x0"] + 3
            _enter(player, spec["right"], spot)
            moved = True
            if spec["right"] == "avanto":
                events.append("avanto")
            elif player.place == "floor":
                events.append("enter")
        near_ladder = spec["climb_x"] is not None and abs(player.x - spec["climb_x"]) <= 11
        if not moved and near_ladder:
            if iy < -0.5 and spec["up"]:
                _start_climb(player, spec["up"])
            elif iy > 0.5 and spec["down"]:
                _start_climb(player, spec["down"])

    if act and player.mode == "move" and player.place == "floor" and player.x >= STOVE_X and player.loyly_cd <= 0:
        events.append("loyly")

    _apply_body(player, room)
    if room.item is not None and player.mode == "move" and player.place == room.item.place:
        if abs(player.x - room.item.x) <= 9:
            events.append(_take(player, room))
    if try_faint(player):
        events.append("faint")
    player.anim += 1
    return events


def _apply_body(player, room):
    if player.mode == "climb":
        place = _hotter(player.place, player.climb_to, room.heat)
        points = min(POINT_RATE[player.place], POINT_RATE[player.climb_to])
    else:
        place = player.place
        points = POINT_RATE[place]
    rate = heat_rate(place, room.heat)
    if player.cool_t > 0 and rate > 0:
        rate *= 0.5
    player.heat += rate / FPS
    if player.heat < 0:
        player.heat = 0.0
    elif player.heat > HEAT_MAX:
        player.heat = HEAT_MAX
    player.score += points / FPS


def throw_into(thrower, players, room):
    """Heat the room. The thrower is cooked a little less than everyone else inside."""
    room.heat = min(100.0, room.heat + LOYLY_ROOM)
    room.loyly_t = 46
    thrower.loyly_cd = LOYLY_CD
    for player in players:
        if player.mode == "faint" or not player.inside:
            continue
        add = LOYLY_SELF if player is thrower else LOYLY_OTHER
        player.heat = min(HEAT_MAX, player.heat + add)
    return "loyly"


def _take(player, room):
    kind = room.item.kind
    if kind == "olut":
        player.heat = max(0.0, player.heat - OLUT_COOL)
    else:
        player.heat = max(0.0, player.heat - TOWEL_COOL)
        player.cool_t = TOWEL_TIME
    room.took_item()
    return kind


def try_faint(player):
    if player.mode == "faint" or player.heat < HEAT_MAX:
        return False
    if player.mode == "climb":
        lower = player.place if PLACES[player.place]["y"] >= PLACES[player.climb_to]["y"] else player.climb_to
        _enter(player, lower, player.x)
    player.mode = "faint"
    player.vx = 0.0
    player.heat = HEAT_MAX
    player.score *= FAINT_KEEP
    if player.score < 0:
        player.score = 0.0
    return True


def separate(players):
    """Unstack people who are just standing. A walker can pass; nobody is shoved off."""
    groups = {}
    for player in players:
        if player.mode != "move":
            continue
        groups.setdefault(player.place, []).append(player)
    for place, group in groups.items():
        if len(group) < 2:
            continue
        group.sort(key=lambda p: p.x)
        spec = PLACES[place]
        for i in range(len(group) - 1):
            a = group[i]
            b = group[i + 1]
            if abs(a.vx) >= 0.35 or abs(b.vx) >= 0.35:
                continue
            gap = b.x - a.x
            if gap < BODY:
                push = (BODY - gap) * 0.45
                a.x -= push
                b.x += push
        for player in group:
            if player.x < spec["x0"]:
                player.x = float(spec["x0"])
            elif player.x > spec["x1"]:
                player.x = float(spec["x1"])


def bench_x(player, place):
    """Each seat is a different spot, so two bots do not fight over one plank."""
    spec = PLACES[place]
    left = spec["x0"] + 8
    right = spec["x1"] - 10
    if right <= left:
        return (spec["x0"] + spec["x1"]) * 0.5
    return left + (right - left) * (player.idx / 3.0)


# ----- bots, shared by autoplay and the playtest -----

PROFILES = {
    "ahne": {"target": "high", "leave": 86, "back": 34, "throw_at": 74, "item": 0.22, "troll": False, "lock": 0.22},
    "tasainen": {"target": "mid", "leave": 66, "back": 30, "throw_at": 60, "item": 0.7, "troll": False, "lock": 0.05},
    "arka": {"target": "low", "leave": 48, "back": 22, "throw_at": 92, "item": 0.9, "troll": False, "lock": 0.0},
    "kiusa": {"target": "low", "leave": 72, "back": 32, "throw_at": 42, "item": 0.28, "troll": True, "lock": 0.02},
}
PROFILE_ORDER = ("ahne", "tasainen", "arka", "kiusa")


class Bot:
    """Greed decides when to sit, when to run for the lake, and when to throw."""

    def __init__(self, profile, rng):
        if isinstance(profile, str):
            profile = PROFILES[profile]
        self.profile = profile
        self.rng = rng
        self.plan = "bench"
        self.lock = 0
        self.command = "idle"

    def decide(self, player, room, players):
        des = blank()
        self.command = "idle"
        if player.mode == "faint":
            return des
        self._plan(player, room, players)
        if self.plan == "cool":
            self._toward(player, "avanto", bench_x(player, "avanto"), des)
        elif self.plan == "throw":
            stove = min(PLACES["floor"]["x1"] - 4, STOVE_X + 8 + player.idx * 5)
            self._toward(player, "floor", stove, des)
            if player.mode == "move" and player.place == "floor" and player.x >= STOVE_X and player.loyly_cd <= 0:
                des["jump"] = True
                self.plan = "bench"
                self.command = "act"
        elif self.plan == "item" and room.item is not None:
            self._toward(player, room.item.place, room.item.x, des)
        else:
            target = self.profile["target"]
            self._toward(player, target, bench_x(player, target), des)
        if des["x"] or des["y"] or des["jump"]:
            if self.command != "act":
                self.command = "move" if (des["x"] or des["y"]) else "act"
        return des

    def _plan(self, player, room, players):
        profile = self.profile
        if self.lock > 0:
            self.lock -= 1
        inside = player.place in INSIDE or player.mode == "climb"
        if inside and player.heat >= profile["leave"] and self.lock <= 0:
            self.plan = "cool"
            return
        if player.place in ("porch", "avanto") and player.heat > profile["back"]:
            self.plan = "cool"
            return
        if self.plan == "cool" and player.heat <= profile["back"]:
            self.plan = "bench"
        if self.plan == "item" and (room.item is None or player.heat < 28):
            self.plan = "bench"
        if self.plan == "throw" and player.loyly_cd > 30:
            self.plan = "bench"
        if self.plan != "bench":
            return
        if player.mode != "move":
            return
        # Decide a few times a second so the plan does not flicker every frame.
        if player.anim % 20 != 0:
            return
        if profile["lock"] and player.heat > profile["leave"] - 18 and self.rng.random() < profile["lock"]:
            self.lock = 50 + self.rng.randint(0, 40)
            return
        if self._wants_throw(player, players):
            self.plan = "throw"
            return
        if room.item is not None and player.heat > 36 and self.rng.random() < profile["item"]:
            self.plan = "item"

    def _wants_throw(self, player, players):
        if player.loyly_cd > 0 or player.heat > self.profile["leave"] - 10:
            return False
        threshold = self.profile["throw_at"]
        for other in players:
            if other is player or other.mode == "faint" or not other.inside:
                continue
            if other.heat >= threshold:
                return True
            if self.profile["troll"] and ORDER.index(other.place if other.mode != "climb" else other.climb_to) > ORDER.index("low"):
                if other.heat >= threshold - 12:
                    return True
        return False

    def _toward(self, player, place, x, des):
        if player.mode == "climb":
            dest_y = PLACES[player.climb_to]["y"]
            des["y"] = -1.0 if dest_y < player.y else 1.0
            return
        if player.mode != "move":
            return
        if player.place != place:
            here = ORDER.index(player.place)
            there = ORDER.index(place)
            if there > here:
                if player.place in ("avanto", "porch"):
                    des["x"] = 1.0
                else:
                    self._climb_aim(player, des, up=True)
            elif player.place == "porch" and place == "avanto":
                des["x"] = -1.0
            elif player.place == "floor":
                des["x"] = -1.0
            elif player.place in ("low", "mid", "high"):
                self._climb_aim(player, des, up=False)
            else:
                des["x"] = 1.0
            return
        if player.x < x - 3:
            des["x"] = 1.0
        elif player.x > x + 3:
            des["x"] = -1.0

    def _climb_aim(self, player, des, up):
        spec = PLACES[player.place]
        cx = spec["climb_x"]
        if player.x < cx - 4:
            des["x"] = 1.0
        elif player.x > cx + 4:
            des["x"] = -1.0
        else:
            des["y"] = -1.0 if up else 1.0
