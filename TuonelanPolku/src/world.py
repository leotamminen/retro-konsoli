# World geometry, spawns and loot live in maps/world.json (embedded as WORLD_LAYOUT).
ROWS = 44
COLS = 486
AIR, SOLID, PLAT, LADDER, THORN, WATER = 0, 1, 2, 3, 4, 5
def _decode_row(spec):
    row = []
    for part in spec.split(","):
        n, code = part.split(":")
        row.extend([int(code)] * int(n))
    return row
def _paint(grid, blocks):
    for x, y, w, h, code in blocks:
        for yy in range(y, y + h):
            if not (0 <= yy < len(grid)):
                continue
            for xx in range(x, x + w):
                if 0 <= xx < len(grid[0]):
                    grid[yy][xx] = code
_W = WORLD_LAYOUT
GRID = [_decode_row(spec) for spec in _W["rows"]]
_paint(GRID, _W.get("extras", {}).get("blocks", []))
COLS = len(GRID[0]); ROWS = len(GRID)
AREAS = [tuple(a) for a in _W["areas"]]
def area_at(tx):
    for n, a, b in AREAS:
        if a <= tx < b: return n
    return "pohjola" if tx >= 446 else "river"
BONFIRES = dict(_W["bonfires"])
BONFIRE_AREA = dict(_W["bonfire_area"])
ARENAS = {}
for _key, _raw in _W["arenas"].items():
    _arena = dict(_raw)
    if isinstance(_arena.get("door_in"), list): _arena["door_in"] = tuple(_arena["door_in"])
    if isinstance(_arena.get("door_out"), list): _arena["door_out"] = tuple(_arena["door_out"])
    ARENAS[_key] = _arena
def _col(x, y0, y1): return [(x, y) for y in range(y0, y1)]
DYN = {}
for _key, _raw in _W["dyn"].items():
    DYN[_key] = dict(tiles=[tuple(t) for t in _raw["tiles"]], code=_raw["code"], active=_raw["active"], key=_raw["key"])
LEVERS = {k: dict(v) for k, v in _W["levers"].items()}
def floor_row(tx, from_row=0):
    """First row at or below from_row whose tile is solid/platform (a standing surface)."""
    for y in range(from_row, ROWS):
        if GRID[y][tx] in (SOLID, PLAT): return y
    return ROWS - 1
ITEMS = {k: tuple(v) for k, v in _W["items"].items()}
for _item in _W.get("extras", {}).get("items", []):
    ITEMS[_item[0]] = tuple(_item[1:])
SPAWNS = [tuple(s) for s in _W["spawns"]] + [tuple(s) for s in _W.get("extras", {}).get("spawns", [])]
