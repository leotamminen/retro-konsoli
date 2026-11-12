"""Settings + save round-trip, corrupt/missing/backup handling, via the real game objects."""
import os, json, glob
from lib import *
S = G["SETTINGS"]; fails = []
def check(c, m):
    if not c: fails.append(m); print("FAIL", m)
sp = os.environ["TUONELA_SETTINGS"]; vp = os.environ["TUONELA_SAVE"]
def clean():
    for f in glob.glob(sp + "*") + glob.glob(vp + "*"): os.remove(f)
# ---- settings ----
clean(); G["load_settings"](); check(S["lang"] == "fi" and S["difficulty"] == "normal", "defaults")
S.update(lang="en", difficulty="tuonela", penalty="mild", music=False, music_vol=3, shake=False, prompts="xbox"); G["save_settings"]()
S.clear(); S.update(G["DEFAULTS"]); G["load_settings"]()
check(S["lang"] == "en" and S["difficulty"] == "tuonela" and S["penalty"] == "mild" and S["music"] is False and S["music_vol"] == 3 and S["shake"] is False and S["prompts"] == "xbox", "settings round trip")
for bad in ("", "{", "[]", "null", '{"lang": 5, "difficulty": "zzz", "music_vol": 99, "shake": "yes", "evil": 1}', "\x00\xff\xfe"):
    open(sp, "w", errors="ignore").write(bad); G["load_settings"]()
    check(S == G["DEFAULTS"] or (bad.startswith('{"lang"') and S["lang"] == "fi" and S["difficulty"] == "normal" and S["music_vol"] == G["DEFAULTS"]["music_vol"]), "bad settings %r" % bad[:12])
open(sp, "wb").write(os.urandom(300)); G["load_settings"](); check(S == G["DEFAULTS"], "random bytes settings")
clean()
# ---- save ----
BF = set(G["BONFIRES"]); sv, st = G["load_save"](vp, BF); check(sv is None and st == "none", "no save -> none")
s = G["new_save"]("sage"); s["stats"]["foc"] = 4; s["souls"] = 123; s["taken"] = ["c_moss"]; s["bosses"] = ["hiisi"]; s["bonfire"] = "b3"; s["seen"] = ["b0", "b3"]
s["stain"] = [{"p": 0, "x": 100.0, "y": 200.0, "souls": 55}]; s["p2"] = {"cls": "hunter", "level": 3, "stats": {"vit": 1, "end": 0, "str": 1, "foc": 0}, "souls": 9}
check(G["write_save"](s, vp), "write ok")
r, st = G["load_save"](vp, BF)
check(st == "ok" and r["cls"] == "sage" and r["souls"] == 123 and r["bonfire"] == "b3" and r["level"] == 5 and r["stain"][0]["souls"] == 55 and r["p2"]["cls"] == "hunter" and r["bosses"] == ["hiisi"], "round trip %s" % st)
s["souls"] = 999; G["write_save"](s, vp); check(os.path.exists(vp + ".bak"), ".bak made")
open(vp, "w").write("{broken"); r, st = G["load_save"](vp, BF); check(st == "backup" and r and r["souls"] == 123, "falls back to .bak (%s)" % st)
open(vp + ".bak", "w").write("garbage"); r, st = G["load_save"](vp, BF); check(st == "corrupt" and r is None and os.path.exists(vp + ".corrupt") and not os.path.exists(vp), "corrupt renamed (%s)" % st)
clean()
for bad in ('[]', '{"cls": "mage"}', '{"cls":"sage","stats":{"vit":"x","end":-5,"str":1e9,"foc":null},"souls":-4,"bonfire":"zz","stain":[{"x":"a"}],"p2":5,"taken":[1,2,"c_moss"]}', 'null', '"x"'):
    open(vp, "w").write(bad); r, st = G["load_save"](vp, BF)
    if r is not None:
        check(r["bonfire"] in BF and r["souls"] >= 0 and all(0 <= v <= 40 for v in r["stats"].values()) and isinstance(r["taken"], list) and r["stain"] == [] and r["p2"] is None, "sanitised %r" % bad[:20])
    clean()
# a hostile save loaded for real into a Game must not crash
open(vp, "w").write(json.dumps({"cls": "hunter", "stats": {"vit": 40, "end": 40, "str": 40, "foc": 40}, "souls": 10**12, "bonfire": "b8", "taken": ["nonsense"], "opened": ["nonsense", "lv_gate"], "bosses": ["hiisi", "turso", "x"], "stain": [{"p": 0, "x": -9999, "y": 99999, "souls": 5}]}))
r, st = G["load_save"](vp, BF); g = new_game(); start(g, save=r, bonfire=r["bonfire"]); step(g, 120)
check(0 <= g.players[0].x <= G["COLS"] * 16, "hostile save runs")
# autosave from a real game: rest at a bonfire writes the file
clean(); g = new_game(); pad = start(g, "hunter", "b0"); g.players[0].souls = 77; g.save_game()
r, st = G["load_save"](vp, BF); check(st == "ok" and r["cls"] == "hunter", "autosave file")
# menu flow: Continue exists with a save, corrupt save shows no crash
g = new_game(); step(g, 30); check(g.state_name in ("title", "menu"), "title state %s" % g.state_name)
print("save tests:", "OK" if not fails else "%d FAIL" % len(fails)); raise SystemExit(1 if fails else 0)
