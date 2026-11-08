
# ---------------- world: hand-designed tile map ----------------
ROWS = 44
COLS = 486
AIR, SOLID, PLAT, LADDER, THORN, WATER = 0, 1, 2, 3, 4, 5
AREAS = [("forest", 0, 146), ("swamp", 146, 292), ("river", 292, 446), ("pohjola", 446, COLS)]
def area_at(tx):
    for n, a, b in AREAS:
        if a <= tx < b: return n
    return "pohjola" if tx>=446 else "river"

def _build():
    G = [[SOLID] * COLS for _ in range(ROWS)]
    def fill(x0, y0, x1, y1, v):
        for y in range(max(0, y0), min(ROWS, y1)):
            for x in range(max(0, x0), min(COLS, x1)): G[y][x] = v
    S = lambda x0, y0, x1, y1: fill(x0, y0, x1, y1, SOLID)
    C = lambda x0, y0, x1, y1: fill(x0, y0, x1, y1, AIR)
    P = lambda x, y, w: fill(x, y, x + w, y + 1, PLAT)
    L = lambda x, y0, y1: fill(x, y0, x + 1, y1, LADDER)
    T = lambda x0, y, x1: fill(x0, y, x1, y + 1, THORN)
    Wt = lambda x0, y0, x1, y1: fill(x0, y0, x1, y1, WATER)
    # ======== METSA (forest) 0..146 ========
    C(0, 0, 126, 30)
    # hole into the root cave + its return platforms
    C(28, 30, 34, 35); P(30, 33, 2); P(28, 31, 2)
    C(34, 31, 50, 35)                         # cave 1
    C(40, 37, 48, 41)                         # secret alcove (wall tiles at col 47 are dynamic)
    C(48, 35, 52, 41); L(51, 35, 41)          # shaft
    C(52, 35, 72, 41)                         # cave 2
    T(58, 40, 64); P(59, 39, 2); P(62, 39, 2)
    C(70, 30, 71, 35); L(70, 30, 41)          # ladder to the surface (east of the gate)
    S(52, 0, 53, 24)                          # gate pillar (gate itself is a dynamic tile, rows 24..29)
    S(78, 29, 80, 30); S(80, 28, 114, 30)     # hill
    C(92, 28, 96, 38); T(92, 37, 96); P(93, 29, 2)
    P(102, 26, 3); P(106, 24, 3); P(110, 22, 3); P(114, 24, 3)
    # boss arena 1: x126..145 (door col 126), exit door col 146
    S(124, 0, 126, 22)
    C(126, 18, 146, 30)
    S(147, 0, 148, 22)
    C(146, 22, 148, 30)
    # ======== SUO (swamp) 146..292 ========
    C(148, 0, 270, 32)
    # pools with boardwalks
    C(158, 32, 166, 38); Wt(158, 33, 166, 38); P(158, 31, 8)
    C(176, 32, 183, 38); Wt(176, 33, 183, 38); S(178, 31, 180, 32); P(176, 30, 2); P(181, 30, 2)
    S(188, 31, 196, 32)
    # ruined tower x200..210
    S(200, 9, 201, 28)                              # left wall (entrance rows 28..31)
    S(211, 14, 226, 32)
    for (x, y) in ((204, 30), (201, 28), (205, 26), (201, 24), (205, 22), (201, 20), (205, 18)): P(x, y, 3)
    P(207, 16, 3)
    S(209, 14, 211, 15)
    # roof walkway = top of S(211,14,226,32), cliff ladder down into the mire
    C(226, 32, 270, 34)
    L(226, 14, 34)
    C(232, 34, 240, 39); Wt(232, 35, 240, 39); P(232, 33, 8)
    C(246, 34, 255, 39); Wt(246, 35, 255, 39); P(246, 33, 9)
    S(240, 33, 244, 34); S(257, 32, 260, 34)
    P(236, 29, 3); P(241, 25, 3); P(246, 21, 3); P(251, 25, 3)
    # boss arena 2 x272..291, door col 272, exit door col 292
    S(270, 0, 272, 22); C(270, 22, 272, 34)
    C(272, 22, 292, 34)
    C(292, 28, 300, 34)
    # ======== TUONELAN JOKI 292..446 ========
    C(300, 10, 398, 34)
    C(311, 34, 332, 44); Wt(311, 37, 332, 44)
    for x in (312, 316, 320, 324, 328): S(x, 34, x + 2, 37)
    S(350, 24, 358, 34)
    T(358, 33, 372)
    S(372, 24, 424, 34)
    C(340, 34, 343, 41); L(342, 34, 41)
    C(341, 37, 381, 41)
    C(333, 38, 340, 41)                       # secret alcove (wall at col 339)
    C(380, 24, 381, 37); L(380, 24, 41)
    L(349, 24, 34)
    # tower
    C(398, 2, 424, 24)
    for (x, y) in ((400, 22), (405, 20), (400, 18), (405, 16), (400, 14), (407, 14)): P(x, y, 3)
    S(412, 12, 424, 24)
    P(410, 18, 2); P(409, 15, 2)
    # boss arena 3 x424..443, door col 424
    C(424, 2, 444, 12)
    # ======== POHJOLA: isolated, short walk from checkpoint to Louhi ========
    C(446, 0, 484, 20)
    S(446, 20, 484, 22)
    S(462, 0, 464, 8)
    # world borders
    S(0, 0, 1, ROWS); S(COLS - 2, 0, COLS, ROWS)
    S(0, ROWS - 2, COLS, ROWS)
    return G

GRID = _build()

BONFIRES = {   # id: (tx, name key)
    "b0": 5, "b1": 76, "b2": 118, "b3": 153, "b4": 216, "b5": 264, "b6": 304, "b7": 376, "b8": 419, "b9": 450,
}
BONFIRE_AREA = {"b0": "forest", "b1": "forest", "b2": "forest", "b3": "swamp", "b4": "swamp", "b5": "swamp",
                "b6": "river", "b7": "river", "b8": "river", "b9": "pohjola"}

# bosses: arena x0 (door col), door_out col, door rows, ground row
ARENAS = {
    "hiisi":  dict(x0=126, x1=146, y0=18, ground=30, door_in=(126, 18, 30), door_out=(146, 22, 30), track="boss_hiisi"),
    "turso":  dict(x0=272, x1=292, y0=22, ground=34, door_in=(272, 22, 34), door_out=(292, 28, 34), track="boss_turso"),
    "tytti":  dict(x0=424, x1=444, y0=2, ground=12, door_in=(424, 2, 12), door_out=None, track="boss_tytti"),
    "louhi":  dict(x0=464, x1=484, y0=2, ground=20, door_in=(464, 2, 20), door_out=None, track="louhi"),
}

# dynamic tiles: id -> (list of (tx,ty), code when ACTIVE, initially active?)
def _col(x, y0, y1): return [(x, y) for y in range(y0, y1)]
DYN = {
    "gate_f":  dict(tiles=_col(52, 24, 30), code=SOLID, active=True, key="gate"),       # solid until opened
    "lad_s":   dict(tiles=_col(210, 14, 32), code=LADDER, active=False, key="lad"),     # ladder appears when dropped
    "bridge":  dict(tiles=[(x, 24) for x in range(358, 372)], code=SOLID, active=False, key="bridge"),
    "d_hiisi_in":  dict(tiles=_col(126, 18, 30), code=SOLID, active=False, key="fog"),
    "d_hiisi_out": dict(tiles=_col(146, 22, 30), code=SOLID, active=True, key="fog"),
    "d_turso_in":  dict(tiles=_col(272, 22, 34), code=SOLID, active=False, key="fog"),
    "d_turso_out": dict(tiles=_col(292, 28, 34), code=SOLID, active=True, key="fog"),
    "d_tytti_in":  dict(tiles=_col(424, 2, 12), code=SOLID, active=False, key="fog"),
    "d_louhi_in": dict(tiles=_col(464,2,20), code=SOLID,active=False,key="fog"),
    "secret_f":  dict(tiles=[(47, y) for y in range(37, 41)], code=SOLID, active=True, key="wall"),
    "secret_r":  dict(tiles=[(339, y) for y in range(38, 41)], code=SOLID, active=True, key="wall"),
}
# levers: id -> (tx, effect id, hint key)
LEVERS = {
    "lv_gate":   dict(tx=54, ty=30, opens="gate_f"),
    "lv_ladder": dict(tx=211, ty=14, opens="lad_s", xoff=0),
    "lv_bridge": dict(tx=373, ty=24, opens="bridge"),
}

def floor_row(tx, from_row=0):
    """First row at or below from_row whose tile is solid/platform (a standing surface)."""
    for y in range(from_row, ROWS):
        if GRID[y][tx] in (SOLID, PLAT): return y
    return ROWS - 1

# items: id -> (tx, ty (surface row the item rests on), kind, payload)
ITEMS = {
    "pouch_f1": (42, 30, "souls", 150),
    "c_moss":   (63, 39, "charm", "c_moss"),
    "flask1":   (111, 22, "flask", 1),
    "c_bear":   (44, 41, "charm", "c_bear"),
    "pouch_f2": (120, 30, "souls", 220),
    "pouch_s1": (165, 31, "souls", 300),
    "c_wolf":   (209, 14, "charm", "c_wolf"),
    "flask2":   (247, 21, "flask", 1),
    "pouch_s2": (258, 32, "souls", 420),
    "pouch_s3": (180, 30, "souls", 280),
    "c_ember":  (365, 41, "charm", "c_ember"),
    "flaskpow": (335, 41, "flaskpow", 1),
    "pouch_j1": (338, 34, "souls", 600),
    "pouch_j2": (411, 18, "souls", 700),
    "pouch_j3": (390, 24, "souls", 650),
}
# enemy spawns: (kind, tx, search-from row)  (flyers hover above the ground found from that row; nakki sit on water)
SPAWNS = [
    # forest, surface
    ("peikko", 17, 0), ("peikko", 24, 0), ("korppi", 21, 0), ("peikko", 64, 0), ("jousi", 74, 0),
    # forest, cave 1 and 2
    ("susi", 40, 31), ("peikko", 45, 31), ("susi", 56, 35), ("peikko", 66, 35), ("korppi", 61, 35),
    # forest, hill and canopy
    ("peikko", 86, 0), ("jousi", 90, 0), ("korppi", 98, 0), ("susi", 101, 0), ("jousi", 109, 0), ("susi", 104, 0),
    ("peikko", 121, 0), ("susi", 115, 0),
    # swamp
    ("hukkunut", 156, 0), ("nakki", 162, 0), ("virvatuli", 169, 0), ("hukkunut", 172, 0), ("nakki", 179, 0),
    ("hukkunut", 190, 0), ("virvatuli", 195, 0),
    ("hukkunut", 204, 0), ("virvatuli", 207, 0), ("hukkunut", 215, 0), ("virvatuli", 222, 0),
    ("hukkunut", 230, 0), ("nakki", 236, 0), ("virvatuli", 240, 0), ("hukkunut", 243, 0), ("nakki", 250, 0),
    ("virvatuli", 252, 0), ("hukkunut", 262, 0),
    # river
    ("haamu", 306, 10), ("joutsen", 318, 10), ("joutsen", 326, 10), ("haamu", 348, 37), ("henki", 356, 37), ("haamu", 366, 37),
    ("henki", 372, 37), ("haamu", 353, 10), ("haamu", 388, 10), ("henki", 393, 10), ("haamu", 397, 10),
    ("haamu", 404, 24), ("henki", 409, 24), ("joutsen", 416, 2),
]
