"""v1.1 map fog of war: unexplored cells hidden, frontier as silhouettes, boss rooms secret until seen, saved in the save."""
from lib import *
import json
fails = []
def ok(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c: fails.append(m)
BG = (10, 8, 14)
def map_px(g, tx, ty):
    """canvas pixel of world tile (tx, ty) on the map screen"""
    for i, (nm, a, b, surf, sil) in enumerate(g.mapimg):
        if a <= tx < b: return ((W - surf.get_width()) // 2 + (tx - a) * 2, 17 + i * 39 + ty)
def solid_tiles(a, b):
    return [(tx, ty) for tx in range(a, b) for ty in range(1, G["ROWS"]) if G["GRID"][ty][tx] == G["SOLID"] and G["GRID"][ty - 1][tx] != G["SOLID"]]
g = new_game(); pad = start(g, "warrior", "b0"); step(g, 10)
ok(g.mapseen and all("," in k for k in g.mapseen) and len(g.mapseen) <= 2, "new game knows only the start (%s)" % sorted(g.mapseen))
g.open_map("play"); g.t_ui = 1; step(g, 1); c = g.canvas
vis, front = g.map_known()
river = [p for p in solid_tiles(300, 440) if (p[0] // 20, p[1] // 11) not in vis | front]
ok(all(tuple(c.get_at(map_px(g, *p)))[:3] == BG for p in river[::25]), "far areas are not drawn at all")
fr = [p for p in solid_tiles(0, 146) if (p[0] // 20, p[1] // 11) in front]
ok(fr and all(tuple(c.get_at(map_px(g, *p)))[:3] in ((34, 32, 42), (28, 30, 46)) for p in fr[::7]), "neighbouring cells are dark silhouettes")
a = G["ARENAS"]["hiisi"]
arena_px = [(tx, ty) for (tx, ty) in solid_tiles(a["x0"] + 2, a["x1"] - 1) if a["y0"] <= ty <= a["ground"]]
def arena_drawn():
    g.track = []; g.draw(); return any(tuple(g.canvas.get_at(map_px(g, *p)))[:3] != BG for p in arena_px)
# explore the whole forest floor except the arena
g.state_name = "play"; p = g.players[0]
for tx in range(2, a["x0"] - 1, 3):
    p.x = tx * 16 + 8; p.y = G["floor_row"](tx, 20) * 16; g.explore()
for tx in range(a["x0"] - 18, a["x0"]):
    g.mapseen.add(G["map_cell"](tx, a["ground"]))
g.mapseen.add(G["map_cell"](a["x0"] + 5, a["ground"]))     # cells around the arena known ...
g.open_map("play"); step(g, 1)
ok(not arena_drawn(), "boss room stays hidden until seen")
shot(g, "22_map_fog", 3)
g.state_name = "play"; p.x = (a["x0"] + 5) * 16; p.y = a["ground"] * 16; g.explore()
ok("arena:hiisi" in g.mapseen, "entering the arena marks it seen")
g.open_map("play"); step(g, 1)
ok(arena_drawn(), "seen boss room is drawn")
# saved + loaded
g.state_name = "play"; g.save_game(); sv, st = G["load_save"](None, set(G["BONFIRES"]))
ok(set(sv["mapseen"]) == g.mapseen, "exploration saved and loaded (%d cells)" % len(sv["mapseen"]))
# 1.0 save without the field
d = dict(G["new_save"]("sage")); d.pop("mapseen"); d.update(seen=["b0", "b1", "b2", "b3"], bosses=["hiisi"], bonfire="b3")
json.dump(d, open(os.environ["TUONELA_SAVE"], "w"))
sv, st = G["load_save"](None, set(G["BONFIRES"])); ok(st == "ok" and sv["mapseen"] is None, "old save loads (mapseen missing -> rebuild)")
g2 = new_game(); pad2 = ScriptPad("x"); g2.add_pad(pad2); g2.start_session(sv, pad2); step(g2, 10)
ok("arena:hiisi" in g2.mapseen and len(g2.mapseen) >= 4, "old save: map rebuilt from bonfires/bosses (%d)" % len(g2.mapseen))
g2.open_map("play"); step(g2, 3); ok(not bad_rects(g2), "map draws")
# junk in the field
for junk in ("abc", 5, [1, 2, None, {"a": 1}, "3,1", "a,b", "1,2,3", "x" * 99], {"k": 1}):
    d = dict(G["new_save"]("hunter")); d["mapseen"] = junk; json.dump(d, open(os.environ["TUONELA_SAVE"], "w"))
    sv, st = G["load_save"](None, set(G["BONFIRES"]))
    g3 = new_game(); pad3 = ScriptPad("y"); g3.add_pad(pad3); g3.start_session(sv, pad3); step(g3, 8); g3.open_map("play"); step(g3, 2)
    ok(st == "ok" and g3.state_name == "map", "junk mapseen %r handled" % (str(junk)[:20],))
print("map:", "OK" if not fails else "FAIL %s" % fails)
sys.exit(1 if fails else 0)
