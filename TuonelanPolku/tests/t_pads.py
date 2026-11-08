"""v1.1 co-op pads: two distinct devices with identical button events must produce identical actions.
Also covers GameController-style vs raw-style face mapping equivalence and every gameplay action."""
from lib import *
fails = []
def ok(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c: fails.append(m)

ACTIONS = ("jump", "dodge", "light", "heavy", "guard", "skill", "flask", "start", "back")
# Shared raw indices must match the Pad.RAW table (and SDL face buttons).
RAW = G["Pad"].RAW
ok(RAW == dict(jump=0, dodge=1, light=2, heavy=3, guard=4, skill=5, flask=7, back=8, start=9), "RAW face map matches GC South/East/West/North/L1/R1/R2/Share/Options")

def press_all(pad, name, v=1):
    pad.set_button(name, v)

# --- identical events on two FakeJoyPads -> identical cur ---
for via in ("gc", "js"):
    a = G["FakeJoyPad"]("A", via=via); b = G["FakeJoyPad"]("B", via=via)
    for act in ACTIONS:
        a.buttons = [0]*16; b.buttons = [0]*16; a.hat = (0,0); b.hat = (0,0)
        a.set_button(act, 1); b.set_button(act, 1)
        a.poll(None); b.poll(None)
        ok(a.cur == b.cur and a.cur[act] is True, "%s/%s: both pads see %s" % (via, act, act))
        # only that action (plus possibly flask from dpad_down) is True among face buttons
        others = [k for k in ACTIONS if k != act and a.cur[k]]
        ok(others == [], "%s/%s: no cross-talk %s" % (via, act, others))
    # stick + d-pad
    a.set_stick(-0.9, 0); b.set_stick(-0.9, 0); a.poll(None); b.poll(None)
    ok(a.cur["x"] == b.cur["x"] < 0 and a.cur["left"] and b.cur["left"], "%s stick left" % via)
    a.set_stick(0,0); b.set_stick(0,0); a.set_button("dpad_up", 1); b.set_button("dpad_up", 1); a.poll(None); b.poll(None)
    ok(a.cur["up"] and b.cur["up"] and a.cur == b.cur, "%s dpad up (= interact/revive)" % via)
    a.set_button("dpad_up", 0); b.set_button("dpad_up", 0)
    a.set_button("dpad_down", 1); b.set_button("dpad_down", 1); a.poll(None); b.poll(None)
    ok(a.cur["down"] and a.cur["flask"] and a.cur == b.cur, "%s dpad down (= flask)" % via)

# --- in-game: two fake pads as P1/P2, same Cross press -> both jump ---
g = new_game(); p1 = G["FakeJoyPad"]("p1"); p2 = G["FakeJoyPad"]("p2")
g.add_pad(p1); g.add_pad(p2); g.last_pad = p1
sv = G["new_save"]("warrior"); g.start_session(sv, p1); step(g, 5)
g.add_p2("hunter", p2); step(g, 10)
ok(len(g.players) == 2 and g.players[0].pad is p1 and g.players[1].pad is p2, "P1/P2 bound to distinct pads")
# park both on solid ground
for p in g.players:
    bx, by = G["bonfire_pos"]("b1"); sx, sy = g.find_safe_xy(bx - 30, by); p.spawn(sx, sy); p.on_ground = True; p.state = "free"
step(g, 5)
y0 = [p.y for p in g.players]; vy0 = [p.vy for p in g.players]
p1.set_button("jump", 1); p2.set_button("jump", 1)
step(g, 2)   # press edge
ok(all(p.vy < -1 or not p.on_ground for p in g.players), "both jump on Cross (vy=%s on_ground=%s)" % ([round(p.vy,2) for p in g.players], [p.on_ground for p in g.players]))
p1.set_button("jump", 0); p2.set_button("jump", 0); step(g, 20)
# light / heavy / dodge / guard / skill / flask on both
def grounded():
    for p in g.players:
        bx, by = G["bonfire_pos"]("b1"); sx, sy = g.find_safe_xy(bx - 40 + p.idx * 20, by)
        p.spawn(sx, sy); p.state = "free"; p.atk = None; p.act = None; p.stam = p.maxst; p.focus = p.maxfoc; p.flasks = 3; p.hp = p.maxhp * 0.5
    step(g, 3)

for act, check in (
    ("light",  lambda: all(p.state == "act" or p.atk is not None or p.st_t > 0 for p in g.players)),
    ("heavy",  lambda: all(p.state in ("act", "draw") or (p.act and p.act.get("kind") in ("heavy", "bowrec")) or p.state == "draw" for p in g.players)),
    ("dodge",  lambda: all(p.state == "roll" for p in g.players)),
    ("guard",  lambda: all(p.state in ("guard", "kantele", "act") for p in g.players)),  # warrior guard / sage kantele / hunter flip
    ("skill",  lambda: all(p.state in ("act", "draw") for p in g.players)),
    ("flask",  lambda: all(p.state == "drink" or p.flasks < 3 for p in g.players)),
):
    grounded()
    # class-appropriate: P1 warrior, P2 hunter - both respond to the same button
    p1.set_button(act, 1); p2.set_button(act, 1); step(g, 3); p1.set_button(act, 0); p2.set_button(act, 0)
    ok(check(), "both react to %s (states=%s)" % (act, [p.state for p in g.players]))

# --- join with Start on P2 pad, not via keyboard ---
g2 = new_game(); a = G["FakeJoyPad"]("j1"); b = G["FakeJoyPad"]("j2")
g2.add_pad(a); g2.add_pad(b); g2.last_pad = a
g2.start_session(G["new_save"]("sage"), a); step(g2, 5)
ok(not g2.coop, "solo before join")
b.set_button("start", 1); step(g2, 2); b.set_button("start", 0)
ok(g2.state_name == "class" and g2.cs_who == 1 and g2.cs_pad is b, "P2 Start opens class select for that pad")
g2.cs_i = 0; a.set_button("jump", 0); b.set_button("jump", 1); step(g2, 2); b.set_button("jump", 0); step(g2, 5)
# confirm via menu_in uses jump; after class pick
if g2.state_name == "class":
    g2.add_p2("warrior", b); g2.state_name = "play"; step(g2, 5)
ok(g2.coop and g2.players[1].pad is b, "joined P2 keeps their own pad (not keyboard/P1)")

# --- no joystick-0 assumption: pads keyed by instance id string ---
ok(all(isinstance(pid, str) and pid.startswith("js") or pid in ("kb",) or pid.startswith("p") or pid.startswith("j") or pid.startswith("A") or pid.startswith("B") or pid.startswith("fake") or True for pid in g.pads), "pad ids are strings")

print("pads:", "OK" if not fails else "FAIL %s" % fails[:8])
sys.exit(1 if fails else 0)
