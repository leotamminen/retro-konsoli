# The room: löyly in the air, the occasional gust or flare, and one cooling pickup.
from .const import (
    DOOR_DRAFT, DOOR_OPEN, EVENT_MAX, EVENT_MIN, FLARE_BODY, FLARE_ROOM, FPS,
    GUST_BODY, GUST_ROOM, INSIDE, ITEM_EVERY, KIUAS_COOL, OLUT_CHANCE, ROOM_RISE,
    START_ROOM,
)


class Item:
    def __init__(self, kind, place, x):
        self.kind = kind
        self.place = place
        self.x = x


class Room:
    def __init__(self, rng, pickup_every=None, heat_mul=1.0):
        self.rng = rng
        self.heat = START_ROOM
        self.heat_mul = heat_mul if heat_mul > 0 else 1.0
        self.pickup_every = pickup_every or ITEM_EVERY
        self.item = None
        self.item_in = max(4 * FPS, self.pickup_every // 2)
        self.event_in = rng.randint(EVENT_MIN, EVENT_MAX)
        self.fx = None
        self.fx_t = 0
        self.loyly_t = 0
        self.gusts = 0
        self.flares = 0
        self.spawns = 0
        self.age = 0
        self.door_t = 0
        self.kiuas_on = True
        self.announce = None
        self.doors = 0
        self.outages = 0
        self.special = None
        self.special_at = 0
        # About one of these a round, never both. Some rounds stay ordinary.
        if rng.random() < 0.72:
            self.special = "door" if rng.random() < 0.5 else "kiuas"
            self.special_at = rng.randint(14 * FPS, 46 * FPS)

    def tick(self, players):
        """Passive rise, gusts and flares, plus at most one rare event."""
        self.age += 1
        names = []
        if self.special and self.age == self.special_at and self.door_t <= 0 and self.kiuas_on:
            if self.special == "door":
                self.door_t = DOOR_OPEN
                self.doors += 1
                self.announce = "door_msg"
            else:
                self.kiuas_on = False
                self.outages += 1
                self.announce = "kiuas_msg"
            names.append(self.special)
            self.special = None
        if self.door_t:
            self.door_t -= 1
        if self.kiuas_on:
            self.heat = min(100.0, self.heat + ROOM_RISE * self.heat_mul / FPS)
        else:
            self.heat = max(8.0, self.heat - KIUAS_COOL / FPS)
        if self.loyly_t:
            self.loyly_t -= 1
        if self.fx_t:
            self.fx_t -= 1
            if self.fx_t <= 0:
                self.fx = None
        if self.item is None:
            self.item_in -= 1
            if self.item_in <= 0:
                self._spawn()
                names.append("spawn")
        busy = self.door_t > 0 or not self.kiuas_on
        self.event_in -= 1
        if self.event_in <= 0 and not busy:
            kind = "gust" if self.rng.random() < 0.40 else "flare"
            self._event(kind, players)
            names.append(kind)
            self.event_in = self.rng.randint(EVENT_MIN, EVENT_MAX)
        elif self.event_in <= 0:
            self.event_in = self.rng.randint(EVENT_MIN, EVENT_MAX)
        return names

    def _spawn(self):
        if self.rng.random() < 0.68:
            place, x = "porch", self.rng.choice((36, 54, 72))
        else:
            place, x = "low", self.rng.choice((160, 188, 214))
        kind = "olut" if self.rng.random() < OLUT_CHANCE else "pyyhe"
        self.item = Item(kind, place, x)
        self.spawns += 1

    def took_item(self):
        self.item = None
        self.item_in = self.pickup_every

    def _event(self, kind, players):
        self.fx = kind
        self.fx_t = 40
        if kind == "gust":
            self.gusts += 1
            self.heat = max(0.0, self.heat - GUST_ROOM)
            for player in players:
                if player.mode == "faint":
                    continue
                if player.place in ("floor", "porch", "avanto") and player.x < 190:
                    player.heat = max(0.0, player.heat - GUST_BODY)
        else:
            self.flares += 1
            self.heat = min(100.0, self.heat + FLARE_ROOM * self.heat_mul)
            burst = FLARE_BODY * self.heat_mul
            for player in players:
                if player.mode == "faint":
                    continue
                place = player.place if player.mode != "climb" else player.climb_to
                if place in INSIDE:
                    player.heat = min(100.0, player.heat + burst)

    def draft(self):
        self.heat = max(0.0, self.heat - DOOR_DRAFT)
