# Bathers, benches, and the little choices that cook you.
from .const import (
    ACCEL, BEER_CAP, BEER_MUL, BEER_TIME, BODY, CLIMB_SPEED, DOOR_POINT,
    DOOR_ZONE_X, FAINT_KEEP, FPS, HEAT_MAX, HEAT_RATE, INSIDE, KIUAS_POINT,
    LOYLY_CD, LOYLY_OTHER, LOYLY_ROOM, LOYLY_SELF, OLUT_COOL, ORDER, PLACES,
    POINT_RATE, RELIGHT_HOLD, ROOM_MULT0, ROOM_MULT1, START_HEAT, STOVE_X,
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
        self.cpu = False
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
        self.beers = 0
        self.beer_t = 0
        self.relight = 0
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
        self.beers = 0
        self.beer_t = 0
        self.relight = 0
        self.climb_t = 0
        self.got_bonus = False
        self.anim = 0
        self.mode = "move"
        bot = getattr(self.pad, "bot", None)
        if bot is not None:
            bot.reset()

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


def step_player(player, ix, iy, act, room, held=False):
    """One frame of feet, heat and points. Returns a list of event names."""
    events = []
    if player.loyly_cd:
        player.loyly_cd -= 1
    if player.cool_t:
        player.cool_t -= 1
    if player.beer_t:
        player.beer_t -= 1
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
                if spec["up"] == "high" and player.beers >= BEER_CAP:
                    player.relight = 0
                else:
                    _start_climb(player, spec["up"])
            elif iy > 0.5 and spec["down"]:
                _start_climb(player, spec["down"])

    if player.mode == "move" and player.place == "floor":
        if room.door_t > 0 and player.x <= PLACES["floor"]["x0"] + 24 and (act or held):
            room.door_t = 0
            events.append("shut")
        elif not room.kiuas_on and player.x >= STOVE_X:
            if held or act:
                player.relight += 1
                if player.relight >= RELIGHT_HOLD:
                    room.kiuas_on = True
                    player.relight = 0
                    events.append("relight")
            else:
                player.relight = 0
        elif act and player.x >= STOVE_X and player.loyly_cd <= 0 and room.kiuas_on:
            events.append("loyly")
            player.relight = 0
        else:
            player.relight = 0

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
    if rate > 0:
        rate *= getattr(room, "heat_mul", 1.0)
        if not getattr(room, "kiuas_on", True):
            rate *= 0.35
    if player.cool_t > 0 and rate > 0:
        rate *= 0.5
    player.heat += rate / FPS
    if player.heat < 0:
        player.heat = 0.0
    elif player.heat > HEAT_MAX:
        player.heat = HEAT_MAX
    if player.beer_t > 0:
        points *= BEER_MUL
    if getattr(room, "door_t", 0) > 0 and _by_door(player):
        points *= DOOR_POINT
    if not getattr(room, "kiuas_on", True):
        points *= KIUAS_POINT
    player.score += points / FPS


def _by_door(player):
    if player.place in ("porch", "avanto"):
        return True
    return player.place == "floor" and player.x < DOOR_ZONE_X


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
        player.beers += 1
        player.beer_t = BEER_TIME
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
    bot = getattr(player.pad, "bot", None)
    if bot is not None:
        bot.reset()
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


# ----- bots that try to win. Difficulty is timing, not a different sport. -----

DIFFICULTY = {
    # Around 76 heat is the exit that still scores. Easy overstays. Hard hits that exit and snipes the leader.
    # Vaikea leaves on time and only throws a killing löyly when already cool.
    # A hot throw used to cook Vaikea itself, so Normaali outscored it.
    "helppo": {"leave": 96, "back": 20, "jitter": 4, "mistake": 0.55, "throw_heat": 99, "lead": 120, "self_max": 90, "react": 36, "item_at": 90, "item_p": 0.05},
    "normaali": {"leave": 81, "back": 30, "jitter": 8, "mistake": 0.16, "throw_heat": 84, "lead": 40, "self_max": 64, "react": 14, "item_at": 48, "item_p": 0.6},
    "vaikea": {"leave": 79, "back": 30, "jitter": 0, "mistake": 0.0, "throw_heat": 83, "lead": 10, "self_max": 52, "solo_throw": True, "react": 1, "item_at": 55, "item_p": 0.35},
    "ihminen": {"leave": 77, "back": 30, "jitter": 5, "mistake": 0.09, "throw_heat": 82, "lead": 28, "self_max": 60, "react": 10, "item_at": 32, "item_p": 0.9},
}


class Bot:
    """Sit the top bench, leave just in time, and throw löyly at a leader who is cooking."""

    def __init__(self, name, rng):
        self.name = name if name in DIFFICULTY else "normaali"
        self.profile = DIFFICULTY[self.name]
        self.rng = rng
        self.plan = "bench"
        self.lock = 0
        self.notice = 0
        self.leave_line = self.profile["leave"]
        self.command = "idle"
        self._roll_leave()

    def reset(self):
        """Clear a faint or a finished round so the next round is a fresh plan."""
        self.plan = "bench"
        self.lock = 0
        self.notice = 0
        self.command = "idle"
        self._roll_leave()

    def _roll_leave(self):
        jitter = self.profile["jitter"]
        self.leave_line = self.profile["leave"] + self.rng.randint(-jitter, jitter)

    def decide(self, player, room, players):
        des = blank()
        self.command = "idle"
        if player.mode == "faint":
            return des
        if self._crisis(player, room, players, des):
            return des
        self._plan(player, room, players)
        if self.plan == "cool":
            self._toward(player, "avanto", bench_x(player, "avanto"), des)
        elif self.plan == "throw":
            stove = min(PLACES["floor"]["x1"] - 4, STOVE_X + 8 + player.idx * 5)
            self._toward(player, "floor", stove, des)
            if (
                player.mode == "move" and player.place == "floor" and player.x >= STOVE_X
                and player.loyly_cd <= 0 and getattr(room, "kiuas_on", True)
            ):
                des["jump"] = True
                self.plan = "bench"
                self._roll_leave()
                self.command = "act"
        elif self.plan == "item" and room.item is not None:
            self._toward(player, room.item.place, room.item.x, des)
        else:
            self.plan = "bench"
            goal = "mid" if player.beers >= BEER_CAP else "high"
            self._toward(player, goal, bench_x(player, goal), des)
        if des["x"] or des["y"] or des["jump"]:
            if self.command != "act":
                self.command = "move" if (des["x"] or des["y"]) else "act"
        return des

    def _plan(self, player, room, players):
        profile = self.profile
        if self.lock > 0:
            self.lock -= 1
        inside = player.place in INSIDE or player.mode == "climb"
        if self.plan == "cool":
            if player.heat <= profile["back"] and player.place in ("porch", "avanto"):
                self.plan = "bench"
                self._roll_leave()
            return
        if player.place in ("porch", "avanto") and player.heat > profile["back"]:
            self.plan = "cool"
            return
        if inside and player.heat >= self.leave_line and self.lock <= 0:
            self.notice += 1
            if self.notice >= profile["react"]:
                self.plan = "cool"
                self.notice = 0
            return
        self.notice = 0
        if self.plan == "item" and (room.item is None or player.heat < 24):
            self.plan = "bench"
        if self.plan == "throw" and player.loyly_cd > 20:
            self.plan = "bench"
        if self.plan != "bench" or player.mode != "move":
            return
        if player.anim % 15 != 0:
            return
        if player.heat > self.leave_line - 12 and self.rng.random() < profile["mistake"]:
            self.lock = 45 + self.rng.randint(0, 50)
            return
        if self._wants_throw(player, players) and getattr(room, "kiuas_on", True):
            self.plan = "throw"
            return
        if self._wants_item(player, room):
            self.plan = "item"

    def _crisis(self, player, room, players, des):
        if getattr(room, "door_t", 0) > 0 and player.mode == "move":
            if player.place == "floor" and player.x <= PLACES["floor"]["x0"] + 26:
                des["jump"] = True
                self.command = "act"
                return True
            if player.place in ("porch", "avanto"):
                self._toward(player, "floor", 210, des)
                self.command = "move"
                return True
        if not getattr(room, "kiuas_on", True):
            if self._should_light(player, players):
                if player.place == "floor" and player.x >= STOVE_X:
                    des["jump"] = True
                    self.command = "act"
                else:
                    stove = min(PLACES["floor"]["x1"] - 4, STOVE_X + 10)
                    self._toward(player, "floor", stove, des)
                    self.command = "move"
                return True
        return False

    def _should_light(self, player, players):
        if player.place == "floor" and player.x >= STOVE_X:
            return True
        pool = [p for p in players if p.mode != "faint" and p.heat < 72]
        if not pool:
            pool = [p for p in players if p.mode != "faint"]
        if not pool:
            return False
        hero = min(pool, key=lambda p: p.idx)
        return hero is player

    def _wants_item(self, player, room):
        item = room.item
        if item is None:
            return False
        if item.kind == "olut":
            if player.beers >= BEER_CAP:
                return False
            # The third beer locks you off the top bench. Only the sloppy bot drinks it.
            if player.beers >= BEER_CAP - 1 and self.name != "helppo":
                return False
        if player.heat < self.profile["item_at"] and not (item.kind == "olut" and player.beers < 2 and player.heat > 28):
            return False
        return self.rng.random() < self.profile["item_p"]

    def _wants_throw(self, player, players):
        profile = self.profile
        if player.loyly_cd > 0 or player.heat > profile.get("self_max", self.leave_line - 18):
            return False
        if profile.get("solo_throw"):
            recent = LOYLY_CD - 50
            for other in players:
                if other is not player and other.loyly_cd > recent:
                    return False
        hot = profile["throw_heat"]
        lead = profile["lead"]
        for other in players:
            if other is player or other.mode == "faint" or not other.inside:
                continue
            if other.score < player.score + lead:
                continue
            if other.heat >= hot:
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
