"""Takes the documentation screenshots into screenshots/. View them by eye."""
from lib import *
LANG = ["fi"]
def sess(cls, bf, diff="normal", n=60, **kw):
    SETTINGS["difficulty"] = diff
    g = new_game(); SETTINGS["lang"] = LANG[0]; pad = start(g, cls, bf, diff=diff); step(g, n); return g, pad
# title + class + settings
setlang("fi")
g = new_game(); pad = ScriptPad("a"); g.add_pad(pad); g.last_pad = pad
step(g, 90); shot(g, "01_title")
tap(g, pad, "jump"); step(g, 20); shot(g, "02_class")
tap(g, pad, "right"); step(g, 20); shot(g, "02b_class_sage")
tap(g, pad, "back"); g.open_settings("title"); step(g, 10); shot(g, "03_settings")
for i in range(5): tap(g, pad, "down", after=1)
step(g, 5); shot(g, "03b_settings_lower")
# areas
for name, cls, bf, pos in (("04_forest", "warrior", "b1", 0), ("05_swamp", "sage", "b4", 0), ("06_river", "hunter", "b7", 0)):
    g, pad = sess(cls, bf, n=90)
    for i in range(70): pad.nextc = dict(pad.blank(), right=True); step(g)
    pad.nextc = None; step(g, 10); shot(g, name)
# bosses
for key, cls in (("hiisi", "warrior"), ("turso", "hunter"), ("tytti", "sage")):
    g, pad = sess(cls, "b2" if key == "hiisi" else ("b5" if key == "turso" else "b8"), n=10)
    a = G["ARENAS"][key]; p = g.players[0]; p.spawn((a["x0"] + 6) * 16, a["ground"] * 16)
    g.start_boss(key); g.boss.hp *= 1; step(g, 150); shot(g, "07_boss_" + key)
    g.boss.hp *= 0.45; step(g, 120); shot(g, "07_boss_%s_p2" % key)
# bonfire + level-up
g, pad = sess("warrior", "b2", n=20); g.players[0].souls = 900 if hasattr(g.players[0], "souls") else 0
g.save["souls"] = 900 if "souls" in g.save else 0
g.open_bonfire(); step(g, 10); shot(g, "08_bonfire")
g.lv_who = 0; g.lv_i = 0; g.state_name = "levelup"; step(g, 10); shot(g, "09_levelup")
g.state_name = "play"; g.open_map("pause"); step(g, 10); shot(g, "10_map")
g.open_pause(); step(g, 10); shot(g, "10b_pause")
# co-op
g, pad = sess("warrior", "b1", n=30); p2 = ScriptPad("b"); g.add_pad(p2); g.add_p2("hunter", p2); step(g, 90); shot(g, "11_coop")
# english
LANG[0] = "en"; setlang("en"); g, pad = sess("sage", "b4", n=60); shot(g, "12_en_swamp")
g.open_pause(); step(g, 5); shot(g, "12b_en_pause")
# dialog text: overwrite confirmation (fi) and the bonfire menu in English
setlang("fi"); G["write_save"](G["new_save"]("warrior"))
g = new_game(); SETTINGS["lang"] = "fi"; pad = ScriptPad("c"); g.add_pad(pad); g.last_pad = pad; g.open_title(); step(g, 5)
tap(g, pad, "down"); tap(g, pad, "jump"); step(g, 10); shot(g, "23_dialog_confirm")
LANG[0] = "en"; g, pad = sess("hunter", "b3", n=30); g.open_bonfire(); step(g, 10); shot(g, "24_en_bonfire_menu")
print("done")
