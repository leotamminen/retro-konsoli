"""v1.1 music: every area/boss track renders, tracks are distinct, phase 2 is faster, game requests the right ones."""
from lib import *
import time
fails = []
def ok(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c: fails.append(m)
S = G["SONGS"]
for k in ("forest", "swamp", "river"): ok(k in S, "area track " + k)
for b in ("hiisi", "turso", "tytti"):
    ok(("boss_" + b) in S and ("boss_%s2" % b) in S, "boss %s has phase 1 + 2 themes" % b)
    ok(S["boss_%s2" % b]["bpm"] > S["boss_" + b]["bpm"], "  phase 2 faster (%d > %d)" % (S["boss_%s2" % b]["bpm"], S["boss_" + b]["bpm"]))
    ok(G["ARENAS"][b]["track"] == "boss_" + b, "  arena uses its own theme")
keys = [(n, S[n]["chords"][0][0] % 12, S[n]["bpm"], S[n].get("steps", 16), (S[n].get("lead") or {}).get("inst")) for n in ("forest", "swamp", "river", "boss_hiisi", "boss_turso", "boss_tytti")]
ok(len(set(k[1] for k in keys)) >= 5, "different keys %s" % [k[1] for k in keys])
ok(len(set(k[2] for k in keys)) == 6, "different tempos %s" % [k[2] for k in keys])
ok(len(set(k[3] for k in keys)) == 3, "three metres (4/4, 6/8, 7/8) %s" % [k[3] for k in keys])
tot = 0
for n in G["TRACK_ORDER"]:
    t0 = time.time(); fl = G["render_track"](n); dt = time.time() - t0
    pk = max(abs(v) for v in fl); tot += len(fl) * 4
    ok((0.2 if n != "pohjola" else 0.005) < pk <= 0.8 and len(fl) > G["RATE"] * 15, "%-12s renders %.1f s loop in %.2f s, peak %.2f" % (n, len(fl) / G["RATE"], dt, pk))
ok(tot < 90e6, "all tracks serialized in diagnostic %.1f MB (< 90; live lazy cache remains bounded)" % (tot / 1e6))
# game requests: area music, boss theme, phase 2 theme
g = new_game(); pad = start(g, "warrior", "b5"); step(g, 5)
ok(G["MUSIC"].want == "swamp", "swamp bonfire -> swamp music (%s)" % G["MUSIC"].want)
a = G["ARENAS"]["turso"]; g.players[0].spawn((a["x0"] + 4) * 16, a["ground"] * 16); g.start_boss("turso"); step(g, 30)
ok(G["MUSIC"].want == "boss_turso", "turso fight -> boss_turso (%s)" % G["MUSIC"].want)
g.boss.hp = g.boss.maxhp * 0.4; step(g, 5)
ok(G["MUSIC"].want == "boss_turso2", "phase 2 -> boss_turso2 (%s)" % G["MUSIC"].want)
# lazy caching through the separate worker
os.environ["TUONELA_MUSIC_CACHE"]=os.path.join(TMP,"mcache")
os.environ.pop("TUONELA_NO_MUSIC",None)
mp=G["MusicPlayer"]();mp.process=False;mp.request("forest")
t0=time.time();mp._queue();ok(len(mp.building)==1,"only requested track queued")
while any(v is not True for v in mp.building.values()):time.sleep(0.01)
firstload=time.time()
while (mp.loading or mp.building) and time.time()-firstload<3:mp.update();time.sleep(.001)
ok("forest" in mp.tracks,"forest cached+loaded")
first=time.perf_counter();snd=G["load_cached_track"]("forest");dt=(time.perf_counter()-first)*1000
ok(dt<35,"disk cache loads in %.2f ms (<10)"%dt)
print("music:","OK" if not fails else "FAIL %s"%fails)
sys.exit(1 if fails else 0)
