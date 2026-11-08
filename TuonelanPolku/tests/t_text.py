"""Key completeness: every tr("...") literal and dynamic key family exists in both languages; fi/en have same keys."""
from lib import *
import re
src = open(BUILD).read()
keys = set(re.findall(r'\btr\("([A-Za-z0-9_]+)"', src))
fi, en = TR["fi"], TR["en"]
miss = [k for k in sorted(keys) if k not in fi or k not in en]
print("literal keys", len(keys), "missing", miss)
print("fi-only", sorted(set(fi) - set(en)), "en-only", sorted(set(en) - set(fi)))
dyn = []
for cls in ("warrior", "sage", "hunter"):
    dyn += ["cls_" + cls, "cd_" + cls, "c_light_" + cls, "c_heavy_" + cls, "c_guard_" + cls, "c_skill_" + cls, "h_special_" + cls, "st_foc_" + cls, "st_foc_" + cls + "_d"]
for st in ("vit", "end", "str"): dyn += ["st_" + st, "st_%s_d" % st]
for a in ("forest", "swamp", "river"): dyn.append("area_" + a)
for b in G["BONFIRES"]: dyn.append("bf_" + b)
for b in G["ARENAS"]: dyn.append("boss_" + b)
for d in ("easy", "normal", "hard", "brutal", "tuonela"): dyn += ["dn_" + d, "sd_difficulty_" + d]
for p in ("classic", "mild"): dyn += ["pen_" + p, "sd_penalty_" + p]
for it in ("c_moss", "c_bear", "c_wolf", "c_ember", "flask", "flaskpow", "feather"): dyn += ["it_" + it, "it_%s_d" % it]
for l in G["LEVERS"]: dyn.append("lever_" + l)
for r in G["SETTING_ROWS"]: pass
print("setting rows", G["SETTING_ROWS"])
missd = [k for k in dyn if k not in fi or k not in en]
print("dynamic missing", missd)
# find other dynamic: scan for tr("xxx" + ...) or tr(... %
print(sorted(set(re.findall(r'tr\(("[a-z_]+" ?[%+][^)]*)\)', src)))[:40])
print(sorted(set(re.findall(r'tr\(([a-z_\.]+)\)', src)))[:40])
