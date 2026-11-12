# Vellamo topography comes from maps/vellamo.json, embedded by build.py as VELLAMO_LAYOUT.
_L = VELLAMO_LAYOUT
NEWCOLS = int(_L["cols"])
_FLOOR = int(_L["floor"])
for _gy in range(ROWS):
    GRID[_gy].extend([AIR if _gy < _FLOOR else SOLID for _ in range(NEWCOLS - COLS)])
COLS = NEWCOLS
for _block in _L["blocks"]:
    _x, _y, _w, _rows, _code = _block
    for _yy in range(_y, _y + _rows):
        if not (0 <= _yy < ROWS):
            continue
        for _xx in range(_x, _x + _w):
            if 0 <= _xx < COLS:
                GRID[_yy][_xx] = _code
AREAS.extend(tuple(pair) for pair in _L["areas"])
BONFIRES.update({k: int(v) for k, v in _L["bonfires"].items()})
BONFIRE_AREA.update(_L["bonfire_area"])
def _arena_spec(rec, floor):
    """Old saves are [name, x0, x1]. Extra y0/ground, or a dict, are authoritative."""
    if isinstance(rec, dict):
        name = rec.get("name", rec.get("id"))
        return name, int(rec["x0"]), int(rec["x1"]), int(rec.get("y0", 2)), int(rec.get("ground", floor))
    name, x0, x1 = rec[0], int(rec[1]), int(rec[2])
    y0 = int(rec[3]) if len(rec) > 3 else 2
    ground = int(rec[4]) if len(rec) > 4 else floor
    return name, x0, x1, y0, ground
for _rec in _L["arenas"]:
    _key, _x0, _x1, _y0, _ground = _arena_spec(_rec, _FLOOR)
    ARENAS[_key] = dict(x0=_x0, x1=_x1, y0=_y0, ground=_ground, door_in=(_x0, _y0, _ground), door_out=(_x1, _y0, _ground), track=_key)
    DYN["d_%s_in" % _key] = dict(tiles=_col(_x0, _y0, _ground), code=SOLID, active=False, key="vellamo_fog")
    DYN["d_%s_out" % _key] = dict(tiles=_col(_x1, _y0, _ground), code=SOLID, active=True, key="vellamo_fog")
DYN["d_vellamo"] = dict(tiles=_col(486, 2, _FLOOR), code=SOLID, active=True, key="vellamo_fog")
for _key, _raw in _L.get("dyn", {}).items():
    if _key in DYN: continue
    DYN[_key] = dict(tiles=[tuple(t) for t in _raw["tiles"]], code=_raw["code"], active=_raw["active"], key=_raw["key"])
FLYERS += ("poltto", "merikala", "kutri", "lampi")
SPAWNS = [sp for sp in SPAWNS if sp[1] < 446] + [tuple(sp) for sp in _L["spawns"]]
for _id, _tx, _ty, _kind, _pay in _L["items"]:
    ITEMS[_id] = (_tx, _ty, _kind, _pay)
ESPEC.update(joukahainen=dict(hp=900,w=48,h=90,souls=4000,poise=9999,spd=1.,wake=0,dmg=22,fly=True),
 ahti=dict(hp=1100,w=56,h=96,souls=5000,poise=9999,spd=1.,wake=0,dmg=26,fly=True),
 aino=dict(hp=1400,w=48,h=96,souls=6000,poise=9999,spd=1.,wake=0,dmg=24,fly=True),
 vellamo=dict(hp=2000,w=56,h=110,souls=9000,poise=9999,spd=1.,wake=0,dmg=32,fly=True),
 poltto=dict(hp=24,w=15,h=15,souls=16,poise=5,spd=.9,wake=190,dmg=17,fly=True),
 merikala=dict(hp=46,w=20,h=15,souls=24,poise=15,spd=1.25,wake=210,dmg=20,fly=True),
 kutri=dict(hp=54,w=16,h=26,souls=30,poise=30,spd=.4,wake=180,dmg=22,fly=True),
 lampi=dict(hp=18,w=14,h=14,souls=22,poise=4,spd=.7,wake=160,dmg=14,fly=True),
 rapu=dict(hp=40,w=22,h=14,souls=28,poise=18,spd=.55,wake=140,dmg=18,fly=False),
 haaksi=dict(hp=22,w=16,h=12,souls=20,poise=4,spd=.6,wake=170,dmg=12,fly=True),
 koralli=dict(hp=48,w=20,h=14,souls=32,poise=16,spd=.5,wake=150,dmg=16,fly=False),
 ankkuri=dict(hp=70,w=18,h=28,souls=40,poise=28,spd=.35,wake=160,dmg=20,fly=False),
 pylvas=dict(hp=36,w=14,h=28,souls=28,poise=40,spd=0,wake=200,dmg=14,fly=False))
FLYERS += ("haaksi",)
for _k in list(BONFIRES):
    if str(_k).startswith("b") and int(str(_k)[1:]) >= 10:
        BF_START.setdefault(_k, 0)
CURRENTS.extend(tuple(c) for c in _L.get("currents", []))
COLLAPSE.extend(tuple(c) for c in _L.get("collapse", []))
def _walk_row(tx):
    """Lowest surface with room to stand. A ceiling is not a floor."""
    tx = int(tx)
    best = None
    for y in range(3, ROWS):
        if 0 <= tx < COLS and GRID[y][tx] in (SOLID, PLAT) and all(GRID[y - k][tx] == AIR for k in range(1, 4)):
            best = y
    return best if best is not None else floor_row(tx, 0)
BONFIRE_POS.update({k: (int(v) * TILE + 8, _walk_row(v) * TILE) for k, v in BONFIRES.items() if str(k).startswith("b") and int(k[1:]) >= 10})
BF_NAME.update(_L["bonfire_area"])
PAL.update(ranta=dict(sky=((9,33,40),(26,101,114)),lit=(62,139,128),deep=(19,66,67),top=(75,188,153),top2=(49,120,103),stone=(58,128,136),bw=(9,31,42),bwa=185,ambient=(88,154,153),fog=(83,193,193)),
syvanne=dict(sky=((4,12,36),(15,48,88)),lit=(36,80,114),deep=(13,37,68),top=(77,135,165),top2=(36,91,130),stone=(48,70,108),bw=(8,20,39),bwa=140,ambient=(50,87,142),fog=(53,100,165)),
katedraali=dict(sky=((7,12,18),(36,58,49)),lit=(63,95,80),deep=(20,46,43),top=(114,166,134),top2=(75,116,103),stone=(83,99,86),bw=(11,26,21),bwa=150,ambient=(70,107,92),fog=(71,137,117)))
BOSS_NAMES += ("joukahainen", "ahti", "aino", "vellamo")
Boss_V13 = None
