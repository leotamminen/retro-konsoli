# Hand-built chunks. The runner is an endless shuffle of these, never raw noise:
# every chunk is proved clearable by kultakiri.physics.validate_chunk.
from .const import CH_W, EY
from .physics import validate_chunk


class Chunk:
    def __init__(self, name, plats, hazards=(), coins=(), powers=(), hard=False, w=CH_W,
                 crumbles=(), movers=(), ceilings=(), tier=0):
        self.name = name
        self.w = w
        self.tier = 2 if hard else tier
        self.hard = self.tier >= 2
        self.plats = tuple((float(x), float(y), float(pw)) for x, y, pw in plats)
        self.hazards = tuple((float(x), float(y), float(hw), float(hh)) for x, y, hw, hh in hazards)
        self.ceilings = tuple((float(x), float(y), float(hw), float(hh)) for x, y, hw, hh in ceilings)
        self.crumbles = tuple((float(x), float(y), float(pw)) for x, y, pw in crumbles)
        self.movers = tuple((float(x), float(y), float(pw), float(amp), int(period)) for x, y, pw, amp, period in movers)
        self.coins = tuple((float(x), float(y)) for x, y in coins)
        self.powers = tuple((float(x), float(y)) for x, y in powers)


def _ground(w, x=0, top=EY):
    return (x, top, w)


def _thorn(x, w=16, h=10, top=EY):
    return (x, top - h, w, h)


def _coins_on(x0, x1, top=EY, step=22, lift=20):
    out = []
    x = x0
    while x <= x1:
        out.append((x, top - lift))
        x += step
    return out


# Wide opening. Coins on the floor, no free powerups.
ALKU = Chunk(
    "alku",
    plats=[_ground(520)],
    coins=_coins_on(90, 460, step=36, lift=20),
    w=520,
)

MAALI = Chunk(
    "maali",
    plats=[_ground(240)],
    coins=_coins_on(40, 180, step=24, lift=28),
    w=240,
)

TASAMAA = Chunk(
    "tasamaa",
    plats=[_ground(CH_W)],
    coins=_coins_on(78, 168, step=22),
)

KOLIKOT = Chunk(
    "kolikot",
    plats=[_ground(CH_W)],
    coins=[(78, EY - 26), (100, EY - 40), (122, EY - 52), (144, EY - 40), (166, EY - 26)],
    powers=[(122, EY - 58)],
)

# gap 32 (envelope on flat ground is 46, lint keeps a 6px margin)
PIKKUKUILU = Chunk(
    "pikkukuilu",
    plats=[_ground(88), _ground(88, 120)],
    coins=[(40, EY - 26), (148, EY - 26), (170, EY - 26)],
    powers=[(156, EY - 18)],
)

# gap 38, still inside the measured full-jump reach
KUILU = Chunk(
    "kuilu",
    plats=[_ground(84), _ground(86, 122)],
    coins=[(36, EY - 26), (150, EY - 36), (174, EY - 26)],
    hard=True,
)

KAKSI = Chunk(
    "kaksi",
    plats=[_ground(74), (106, EY, 40), (154, EY, 54)],
    coins=[(36, EY - 26), (120, EY - 28), (176, EY - 26)],
)

NOUSU = Chunk(
    "nousu",
    plats=[_ground(104), (82, EY - 20, 78), (146, EY, 62)],
    coins=[(40, EY - 26), (110, EY - 44), (170, EY - 26)],
    powers=[(114, EY - 40)],
)

LASKU = Chunk(
    "lasku",
    plats=[_ground(78), (90, EY + 22, 56), (156, EY, 52)],
    coins=[(36, EY - 26), (112, EY - 4), (176, EY - 26)],
    powers=[(112, EY + 6)],
)

OKAPUU = Chunk(
    "okapuu",
    plats=[_ground(CH_W)],
    hazards=[_thorn(100, 16, 10), _thorn(168, 14, 10)],
    coins=[(70, EY - 26), (124, EY - 36), (186, EY - 26)],
    powers=[(186, EY - 18)],
)

KAPEA = Chunk(
    "kapea",
    plats=[_ground(72), (104, EY, 44), (156, EY, 52)],
    coins=[(36, EY - 26), (120, EY - 28), (176, EY - 26)],
    hard=True,
)

SIKSAK = Chunk(
    "siksak",
    plats=[_ground(80), (64, EY - 16, 52), (112, EY - 32, 40), (150, EY, 58)],
    coins=[(36, EY - 26), (80, EY - 40), (128, EY - 54), (176, EY - 26)],
    powers=[(128, EY - 52)],
    hard=True,
)

PORTAAT = Chunk(
    "portaat",
    plats=[_ground(86), (70, EY - 16, 50), (112, EY - 30, 46), (154, EY, 54)],
    coins=[(36, EY - 26), (88, EY - 40), (128, EY - 54), (176, EY - 26)],
    powers=[(128, EY - 46)],
)

MATALA = Chunk(
    "matala",
    plats=[_ground(74), (92, EY + 26, 52), (152, EY, 56)],
    coins=[(36, EY - 26), (112, EY + 2), (176, EY - 26)],
    powers=[(112, EY + 8)],
)


# Spike ceiling over flat ground. A full jump hits it; the fair path is a short hop.
KATTO = Chunk(
    "katto",
    plats=[_ground(CH_W)],
    ceilings=[(100, EY - 58, 40, 12)],
    coins=[(70, EY - 22), (160, EY - 22)],
)

# Floor spikes, then spikes sitting on a raised step, power on that step.
PIIKIT = Chunk(
    "piikit",
    plats=[_ground(CH_W), (58, EY - 16, 52)],
    hazards=[_thorn(64, 10, 8, EY - 16), _thorn(140, 12, 8)],
    coins=[(40, EY - 22), (84, EY - 36), (176, EY - 22)],
    powers=[(86, EY - 32)],
    tier=1,
)

# Bridge that gives way if you hesitate. The power sits on the crumbling span.
MUREA = Chunk(
    "murea",
    plats=[_ground(82), (148, EY, 60)],
    crumbles=[(74, EY, 82)],
    coins=[(40, EY - 24), (176, EY - 24)],
    powers=[(112, EY - 18)],
    tier=1,
)

# A wide slab that slides, but always covers the band between the banks.
LIUKU = Chunk(
    "liuku",
    plats=[_ground(90), (156, EY, 52)],
    movers=[(76, EY, 112, 12, 120)],
    coins=[(40, EY - 24), (180, EY - 24)],
    powers=[(124, EY - 18)],
    tier=1,
)

# Low road has a bramble. High road is two tiles up and holds the power.
HAARA = Chunk(
    "haara",
    plats=[_ground(CH_W), (78, EY - 32, 72)],
    hazards=[_thorn(108, 16, 10)],
    coins=[(40, EY - 24), (100, EY - 54), (176, EY - 24)],
    powers=[(108, EY - 54)],
    tier=1,
)

# Four short steps up to two tiles, then back down to the exit.
RAPUT = Chunk(
    "raput",
    plats=[_ground(70), (58, EY - 16, 40), (90, EY - 32, 40), (122, EY - 16, 40), (150, EY, 58)],
    coins=[(36, EY - 24), (104, EY - 54), (176, EY - 24)],
    powers=[(104, EY - 52)],
    tier=1,
)

POOL = (
    TASAMAA, KOLIKOT, PIKKUKUILU, KUILU, KAKSI, NOUSU, LASKU,
    OKAPUU, KAPEA, SIKSAK, PORTAAT, MATALA,
    KATTO, PIIKIT, MUREA, LIUKU, HAARA, RAPUT,
)
ALL_CHUNKS = (ALKU, MAALI) + POOL
BY_NAME = {c.name: c for c in ALL_CHUNKS}


def validate_all():
    for chunk in ALL_CHUNKS:
        validate_chunk(chunk)
    return True
