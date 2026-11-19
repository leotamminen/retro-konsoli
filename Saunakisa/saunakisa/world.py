# The room: löyly in the air, the occasional gust or flare, and one cooling pickup.
from .const import (
    DOOR_DRAFT, EVENT_MAX, EVENT_MIN, FLARE_BODY, FLARE_ROOM, FPS, GUST_BODY,
    GUST_ROOM, INSIDE, ITEM_EVERY, ITEM_FIRST, ROOM_RISE, START_ROOM,
)


class Item:
    def __init__(self, kind, place, x):
        self.kind = kind
        self.place = place
        self.x = x


class Room:
    def __init__(self, rng):
        self.rng = rng
        self.heat = START_ROOM
        self.item = None
        self.item_in = ITEM_FIRST
        self.event_in = rng.randint(EVENT_MIN, EVENT_MAX)
        self.fx = None
        self.fx_t = 0
        self.loyly_t = 0
        self.gusts = 0
        self.flares = 0
        self.spawns = 0

    def tick(self, players):
        """Passive rise, then a gust or a flare. Returns event names."""
        self.heat = min(100.0, self.heat + ROOM_RISE / FPS)
        if self.loyly_t:
            self.loyly_t -= 1
        if self.fx_t:
            self.fx_t -= 1
            if self.fx_t <= 0:
                self.fx = None
        names = []
        if self.item is None:
            self.item_in -= 1
            if self.item_in <= 0:
                self._spawn()
                names.append("spawn")
        self.event_in -= 1
        if self.event_in <= 0:
            kind = "gust" if self.rng.random() < 0.46 else "flare"
            self._event(kind, players)
            names.append(kind)
            self.event_in = self.rng.randint(EVENT_MIN, EVENT_MAX)
        return names

    def _spawn(self):
        if self.rng.random() < 0.68:
            place, x = "porch", self.rng.choice((36, 54, 72))
        else:
            place, x = "low", self.rng.choice((160, 188, 214))
        kind = "olut" if self.rng.random() < 0.55 else "pyyhe"
        self.item = Item(kind, place, x)
        self.spawns += 1

    def took_item(self):
        self.item = None
        self.item_in = ITEM_EVERY

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
            self.heat = min(100.0, self.heat + FLARE_ROOM)
            for player in players:
                if player.mode == "faint":
                    continue
                place = player.place if player.mode != "climb" else player.climb_to
                if place in INSIDE:
                    player.heat = min(100.0, player.heat + FLARE_BODY)

    def draft(self):
        self.heat = max(0.0, self.heat - DOOR_DRAFT)
