# Shared numbers for the sauna. Heat tests and the match loop both use these.
FPS = 60
W, H = 320, 180
PW, PH = 12, 16

ROUNDS = 3
COUNTDOWN = 180
ROUND_FRAMES = 78 * FPS
MIN_FRAMES = 48 * FPS
LAST_BONUS = 55
SOLO_HOLD = 100

HEAT_MAX = 100.0
START_HEAT = 10.0
START_ROOM = 22.0
ROOM_RISE = 0.40
ROOM_MULT0 = 0.66
ROOM_MULT1 = 1.08
FAINT_KEEP = 0.70

# Heat per second. Positive cooks, negative cools. Room heat scales only the cook.
HEAT_RATE = {
    "high": 1.42,
    "mid": 0.78,
    "low": 0.40,
    "floor": 0.16,
    "porch": -8.0,
    "avanto": -26.0,
}
# Points per second. The floor is a corridor, the top bench is the prize.
POINT_RATE = {
    "high": 6.4,
    "mid": 3.6,
    "low": 2.0,
    "floor": 0.35,
    "porch": 0.0,
    "avanto": 0.0,
}

WALK = 1.72
ACCEL = 1.05
CLIMB_SPEED = 2.35
BODY = 14

LOYLY_CD = int(4.4 * FPS)
LOYLY_ROOM = 9.0
LOYLY_OTHER = 8.0
LOYLY_SELF = 5.0
STOVE_X = 276

OLUT_COOL = 30.0
TOWEL_COOL = 14.0
TOWEL_TIME = 4 * FPS
ITEM_FIRST = 7 * FPS
ITEM_EVERY = 12 * FPS

EVENT_MIN = 9 * FPS
EVENT_MAX = 14 * FPS
GUST_ROOM = 15.0
GUST_BODY = 7.0
FLARE_ROOM = 11.0
FLARE_BODY = 5.0
DOOR_DRAFT = 4.0

# x0, x1, feet y. climb_x is where up/down changes bench.
# link_left / link_right are the door and the avanto, taken by walking off the end.
PLACES = {
    "avanto": {"x0": 14, "x1": 48, "y": 168, "climb_x": None, "up": None, "down": None, "left": None, "right": "porch"},
    "porch": {"x0": 6, "x1": 96, "y": 148, "climb_x": None, "up": None, "down": None, "left": "avanto", "right": "floor"},
    "floor": {"x0": 114, "x1": 308, "y": 156, "climb_x": 252, "up": "low", "down": None, "left": "porch", "right": None},
    "low": {"x0": 128, "x1": 264, "y": 120, "climb_x": 250, "up": "mid", "down": "floor", "left": None, "right": None},
    "mid": {"x0": 142, "x1": 254, "y": 86, "climb_x": 242, "up": "high", "down": "low", "left": None, "right": None},
    "high": {"x0": 156, "x1": 242, "y": 52, "climb_x": 230, "up": None, "down": "mid", "left": None, "right": None},
}
INSIDE = ("floor", "low", "mid", "high")
ORDER = ("avanto", "porch", "floor", "low", "mid", "high")

PCOLORS = (
    ((232, 72, 64), (92, 24, 28)),
    ((64, 148, 240), (18, 48, 112)),
    ((72, 196, 96), (20, 96, 44)),
    ((244, 196, 48), (148, 96, 16)),
)
PNAMES = ("PUNAINEN", "SININEN", "VIHREÄ", "KELTAINEN")

# Centre of a bench, where a bot sits if it is not going anywhere.
SEAT = {
    "high": 196,
    "mid": 190,
    "low": 186,
    "floor": 168,
    "porch": 52,
    "avanto": 30,
}
