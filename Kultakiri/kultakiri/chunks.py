# Hand-built chunks. The runner is an endless shuffle of these, never raw noise:
# every chunk is proved clearable by kultakiri.physics.validate_chunk.
from .const import CH_W, EY
from .physics import validate_chunk


class Chunk:
    def __init__(self, name, plats, hazards=(), coins=(), powers=(), hard=False, w=CH_W):
        self.name = name
        self.w = w
        self.hard = hard
        self.plats = tuple((float(x), float(y), float(pw)) for x, y, pw in plats)
        self.hazards = tuple((float(x), float(y), float(hw), float(hh)) for x, y, hw, hh in hazards)
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


# Wide opening so four players can spread out before the first gap.
ALKU = Chunk(
    "alku",
    plats=[_ground(520)],
    coins=_coins_on(70, 460, step=28, lift=20),
    powers=[(200, EY - 16), (250, EY - 16), (300, EY - 16), (350, EY - 16), (400, EY - 16), (450, EY - 16)],
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
    powers=[(128, EY - 16)],
)

KOLIKOT = Chunk(
    "kolikot",
    plats=[_ground(CH_W)],
    coins=[(78, EY - 26), (100, EY - 40), (122, EY - 52), (144, EY - 40), (166, EY - 26)],
    powers=[(104, EY - 16)],
)

# gap 32 (envelope on flat ground is 46, lint keeps a 6px margin)
PIKKUKUILU = Chunk(
    "pikkukuilu",
    plats=[_ground(88), _ground(88, 120)],
    coins=[(40, EY - 26), (148, EY - 26), (170, EY - 26)],
    powers=[(156, EY - 16)],
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
)

OKAPUU = Chunk(
    "okapuu",
    plats=[_ground(CH_W)],
    hazards=[_thorn(100, 16, 10), _thorn(168, 14, 10)],
    coins=[(70, EY - 26), (124, EY - 36), (186, EY - 26)],
    powers=[(124, EY - 40)],
)

KAPEA = Chunk(
    "kapea",
    plats=[_ground(72), (104, EY, 44), (156, EY, 52)],
    coins=[(36, EY - 26), (120, EY - 28), (176, EY - 26)],
    hard=True,
)

SIKSAK = Chunk(
    "siksak",
    plats=[_ground(80), (64, EY - 18, 52), (112, EY - 34, 40), (150, EY, 58)],
    coins=[(36, EY - 26), (80, EY - 42), (128, EY - 58), (176, EY - 26)],
    hard=True,
)

PORTAAT = Chunk(
    "portaat",
    plats=[_ground(86), (70, EY - 16, 50), (112, EY - 30, 46), (154, EY, 54)],
    coins=[(36, EY - 26), (88, EY - 40), (128, EY - 54), (176, EY - 26)],
)

MATALA = Chunk(
    "matala",
    plats=[_ground(74), (92, EY + 26, 52), (152, EY, 56)],
    coins=[(36, EY - 26), (112, EY + 2), (176, EY - 26)],
    powers=[(112, EY + 8)],
)


POOL = (
    TASAMAA, KOLIKOT, PIKKUKUILU, KUILU, KAKSI, NOUSU, LASKU,
    OKAPUU, KAPEA, SIKSAK, PORTAAT, MATALA,
)
ALL_CHUNKS = (ALKU, MAALI) + POOL
BY_NAME = {c.name: c for c in ALL_CHUNKS}


def validate_all():
    for chunk in ALL_CHUNKS:
        validate_chunk(chunk)
    return True
