# Shared numbers. Jump reachability tests and the chunk designer both use these.
FPS = 60
W, H = 320, 180
PW, PH = 12, 16

GRAV = 0.28
JUMP_V = -5.15
JUMP_CUT = 0.5
MAX_FALL = 5.1
GLIDE_FALL = 0.62
RUN = 1.82
SPEED_RUN = 2.24
ACCEL = 0.62
COYOTE = 6
JUMP_BUF = 6
SLOW_MUL = 0.5

SCROLL0 = 0.98
SCROLL_MAX = 1.38
SCROLL_ACC = 0.00020

CH_W = 208
EY = 136
LEAD = 18
JUMP_HOLD = 34
FALL_Y = 196
BUMP_VX = 1.45
MAGNET_R = 56
MAGNET_PULL = 3.1

FINISH_X = 5200
ROUNDS = 3
GHOST_FRAMES = 270
INV_HAZARD = 28
STUN_HAZARD = 14

COIN_PTS = 10
DIST_DIV = 24
WIN_PTS = 350

DUR = {
    "double": 360,
    "speed": 300,
    "shield": 420,
    "magnet": 360,
    "slow": 180,
    "glide": 300,
}
POWER_KINDS = ("double", "speed", "shield", "magnet", "slow", "glide")

# Body, outline. Four players, identical controls, distinct colours.
PCOLORS = (
    ((232, 72, 64), (92, 24, 28)),
    ((64, 148, 240), (18, 48, 112)),
    ((72, 196, 96), (20, 96, 44)),
    ((244, 196, 48), (148, 96, 16)),
)
PNAMES = ("PUNAINEN", "SININEN", "VIHREÄ", "KELTAINEN")

POWER_COLORS = {
    "double": (72, 168, 255),
    "speed": (255, 148, 40),
    "shield": (64, 228, 216),
    "magnet": (228, 72, 96),
    "slow": (176, 112, 255),
    "glide": (110, 220, 140),
}
