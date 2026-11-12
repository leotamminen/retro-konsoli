"""v1.1 bug: after beating the game, 'New game' went straight to the ending. Plays the whole flow through the menus."""
from lib import *
import json
fails = []
def ok(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c: fails.append(m)
def menu(g, pad, *keys):
    for k in keys: tap(g, pad, k, after=3)
for cls in ("warrior", "hunter"):
    g = new_game(); pad = ScriptPad("t1"); g.add_pad(pad); g.last_pad = pad
    sv = G["new_save"](cls); sv["bosses"] = ["hiisi", "turso"]; sv["bonfire"] = "b8"; sv["seen"] = list(G["BONFIRES"]); sv["opened"] = list(G["DYN"].keys())[:3]
    g.start_session(sv, pad); step(g, 5)
    a = G["ARENAS"]["tytti"]; g.players[0].spawn((a["x0"] + 5) * 16, a["ground"] * 16)
    g.start_boss("tytti"); step(g, 30); b = g.boss
    b.hp = 1; b.phase = 2
    for _ in range(600):
        if b.dead: break
        b.hp = min(b.hp, 1); b.invuln = False; b.take(9999, g.players[0], 0) if hasattr(b, "take") else None; step(g, 1, draw=False)
    ok(b.dead, "%s: Tuonen Tytti beaten" % cls)
    for _ in range(600):
        if g.state_name == "ending": break
        step(g, 1, draw=False)
    ok(g.state_name == "ending", "ending reached")
    ok(G["load_save"](None, set(G["BONFIRES"]))[0]["done"], "save marked done")
    for _ in range(4): step(g, 70); tap(g, pad, "jump", after=3)
    step(g,400,draw=False)
    g.back_to_title()
    ok(g.state_name in ("title","play"), "fake ending/return completed (%s)"%g.state_name)
    ks=[k for k,_ in g.title_items()];ok(ks[0]=="cont" and "new" in ks and (ks[1]!="vellamo" or g.title_save.get("vellamo_unlocked")), "title Continue + New game + completed Vellamo option")
    menu(g, pad, *(["down"] * [k for k,_ in g.title_items()].index("new")), "jump")
    ok(g.state_name == "confirm", "overwrite confirmation shown")
    menu(g, pad, "jump")                 # default answer must be 'No'
    ok(g.state_name == "title" and G["load_save"](None, set(G["BONFIRES"]))[0]["done"], "default No keeps the finished save")
    ok(g.title_items()[g.menu_i["title"]][0] == "new", "cursor still on New game")
    menu(g, pad, "jump", "up", "jump")
    ok(g.state_name == "class", "class select reached (%s)" % g.state_name)
    shot(g, "21_newgame_class") if cls == "warrior" else None
    menu(g, pad, "jump")
    step(g, 5)
    ok(g.state_name == "play", "new game is playable (%s)" % g.state_name)
    sv2 = g.save
    ok(sv2["bosses"] == [] and not sv2["done"] and sv2["opened"] == [] and sv2["bonfire"] == "b0" and sv2["souls"] == 0 and sv2["level"] == 1, "progress fully reset")
    ok(g.area == "forest" and g.players[0].x < 20 * 16 and g.ending_t == 0 and g.boss is None, "starts in the forest at the first bonfire")
    ok(all(not k.startswith("arena:") for k in g.mapseen) and len(g.mapseen) <= 3, "map exploration reset (%d cells)" % len(g.mapseen))
    for _ in range(400): step(g, 1, draw=False)
    ok(g.state_name == "play", "still playing after 400 frames, no ending (%s)" % g.state_name)
    disk = json.load(open(os.environ["TUONELA_SAVE"]))
    ok(disk["bosses"] == [] and disk["done"] is False, "new save written to disk")
    # Continue on a finished save also plays (does not loop into the ending)
    g2 = new_game(); pad2 = ScriptPad("t2"); g2.add_pad(pad2); g2.last_pad = pad2
    sv3 = G["new_save"](cls); sv3.update(bosses=["hiisi", "turso", "tytti"], done=True, bonfire="b8"); G["write_save"](sv3)
    g2.open_title(); step(g2, 3); menu(g2, pad2, "jump"); step(g2, 400, draw=False)
    ok(g2.state_name == "play" and g2.save["bonfire"]=="b9", "Continue after fake ending reaches Pohjola (%s)" % g2.state_name)
print("newgame:", "OK" if not fails else "FAIL %s" % fails)
sys.exit(1 if fails else 0)
