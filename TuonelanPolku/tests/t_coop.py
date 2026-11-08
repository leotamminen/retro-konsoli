"""Co-op: join via second pad + class pick, leave, hot-unplug, revive, both-down = death, boss HP scaling, P1 pad loss."""
from lib import *
fails = []
def check(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c: fails.append(m)
for lang in ("fi", "en"):
    setlang(lang)
    g = new_game(); p1 = start(g, "warrior", "b1"); p2 = ScriptPad("t2"); g.add_pad(p2)
    step(g, 30)
    tap(g, p2, "start"); check(g.state_name == "class" and g.cs_who == 1, "[%s] 2nd pad Start opens class select" % lang)
    step(g, 3); shot(g, "11_coop_class_%s" % lang) if lang == "fi" else None
    tap(g, p2, "right"); tap(g, p2, "jump", hold=2)
    check(g.state_name == "play" and len(g.players) == 2 and g.players[1].ch["cls"] == "sage", "[%s] P2 joined as %s, state %s" % (lang, g.players[1].ch["cls"], g.state_name))
    step(g, 90)
    check(not untr(g) and not bad_rects(g), "[%s] co-op HUD text translated and in bounds" % lang)
    if lang == "fi": shot(g, "12_coop_hud")
    # P2 is its own controller: only P2 moving moves P2
    x1, x2 = g.players[0].x, g.players[1].x
    p2.nextc = dict(p2.blank(), right=True, x=1.0)
    step(g, 40); p2.nextc = None
    check(g.players[1].x > x2 + 10 and abs(g.players[0].x - x1) < 3, "[%s] P2 moves independently" % lang)
    # shared camera leash: P2 walks away far -> teleport/leash keeps both on screen
    g.players[1].x += 200; p2.nextc = dict(p2.blank(), right=True, x=1.0)
    step(g, 240); p2.nextc = None
    cx = g.cam[0]
    check(all(cx - 8 <= p.x <= cx + W + 8 for p in g.players), "[%s] both players inside camera after leash (cam %d, p %d %d)" % (lang, cx, g.players[0].x, g.players[1].x))
    # P2 down -> revive by P1
    d = g.players[1]; d.hp = 1; g.player_down(d)
    check(d.state == "down", "[%s] P2 down while P1 alive" % lang)
    g.enemies = [e for e in g.enemies if e.boss]   # clear nearby trash so a random hit can't cancel the hold
    a = g.players[0]; a.state = "free"; a.atk = None; a.act = None; a.inv = 120
    bx, by = d.x, d.y; a.x = bx - 6; a.y = by; a.on_ground = True; d.x, d.y = bx, by; d.on_ground = True; g.snap_cam(); g.sep_t = 0
    p1.nextc = dict(p1.blank(), up=True); step(g, 100); p1.nextc = None
    check(d.state == "free" and d.hp > 0, "[%s] P1 revives P2 (%s)" % (lang, d.state))
    # both dead -> death flow -> respawn at bonfire, both back
    for p in g.players: p.hp = 1
    g.player_down(g.players[1]); g.player_down(g.players[0])
    step(g, 5); check(g.dying, "[%s] both down = death" % lang)
    step(g, 400)
    check(not g.dying and all(p.alive() for p in g.players) and len(g.players) == 2, "[%s] respawn with both players" % lang)
    # leave through pause menu entry
    g.open_pause(); items = [k for k, _ in g.pause_items()]
    check("p2off" in items, "[%s] pause has Leave entry" % lang)
    i = items.index("p2off"); g.menu_i["pause"] = i; tap(g, p1, "jump")
    check(len(g.players) == 1 and g.state_name in ("play", "pause"), "[%s] P2 left via menu (%s, %d players)" % (lang, g.state_name, len(g.players)))
    g.state_name = "play"; step(g, 10)
    # rejoin, then unplug P2's controller
    tap(g, p2, "start"); tap(g, p2, "jump", hold=2); check(len(g.players) == 2, "[%s] rejoin" % lang)
    g.lose_pad("t2"); step(g, 5)
    check(len(g.players) == 1 and not g.coop, "[%s] unplugging P2 pad removes P2" % lang)
    # P1 pad unplug: game pauses and waits; another pad resumes
    g.lose_pad("t1"); step(g, 3)
    check(g.state_name == "pause" and g.need_pad is not None, "[%s] P1 pad loss pauses" % lang)
    if lang == "fi": step(g, 3); shot(g, "13_need_pad")
    p3 = ScriptPad("t3"); g.add_pad(p3); tap(g, p3, "start")
    check(g.need_pad is None and g.p_pad[0] is p3, "[%s] new pad takes over P1" % lang)
    g.track.clear(); step(g, 1); check(not untr(g) and not bad_rects(g), "[%s] pause text clean" % lang)
# boss hp scaling: the same hit removes less when two play
g = new_game(); start(g, "warrior", "b2"); g.start_boss("hiisi"); g.boss.invuln = False; h = g.boss.hp; g.boss.take(100); d1 = h - g.boss.hp
g2 = new_game(); start(g2, "warrior", "b2"); q = ScriptPad("q"); g2.add_pad(q); g2.add_p2("hunter", q); g2.start_boss("hiisi"); g2.boss.invuln = False; h = g2.boss.hp; g2.boss.take(100); d2 = h - g2.boss.hp
check(d1 > 0 and d2 < d1 * 0.7, "boss HP scales with 2 players (100 dmg -> %.1f solo, %.1f co-op)" % (d1, d2))
print("coop:", "OK" if not fails else "%d FAIL" % len(fails)); raise SystemExit(1 if fails else 0)
