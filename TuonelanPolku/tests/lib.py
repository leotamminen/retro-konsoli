"""Test harness: loads the built game into a namespace and offers a headless Game."""
import os, sys, tempfile, shutil
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy"); os.environ["TUONELA_NO_MUSIC"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TMP = tempfile.mkdtemp(prefix="tp_test_")
os.environ["TUONELA_SETTINGS"] = os.path.join(TMP, "set.json"); os.environ["TUONELA_SAVE"] = os.path.join(TMP, "save.json")
BUILD = os.environ.get("TP_FILE") or os.path.join(ROOT, "TuonelanPolku1.3.4.pygame")
def load():
    G = {"__name__": "tp"}
    exec(compile(open(BUILD).read(), BUILD, "exec"), G)
    return G
G = load()
import pygame
pygame.init()
screen = pygame.display.set_mode((G["W"], G["H"]))
globals().update({k: G[k] for k in ("W", "H", "tr", "TR", "TStr", "SETTINGS", "Game", "ScriptPad", "IdlePad", "Pad")})
def new_game(**kw):
    G["load_settings"]()
    g = Game(screen, test=True); g.track = []
    return g
def step(g, n=1, draw=True):
    for _ in range(n):
        g.update()
        if draw: g.draw()
def tap(g, pad, *keys, hold=2, after=2, **axes):
    """press keys on a ScriptPad for `hold` frames"""
    for _ in range(hold):
        c = pad.blank()
        for k in keys: c[k] = True
        c.update(axes)
        pad.nextc = c; step(g)
    pad.nextc = None; step(g, after)
def setlang(l): SETTINGS["lang"] = l
SHOTS = os.path.join(ROOT, "screenshots")
def shot(g, name, scale=3):
    os.makedirs(SHOTS, exist_ok=True)
    pygame.image.save(pygame.transform.scale(g.canvas, (G["W"] * scale, G["H"] * scale)), os.path.join(SHOTS, name + ".png"))
def start(g, cls="warrior", bonfire="b0", save=None, pad=None, diff=None):
    """Start a session directly."""
    if diff: SETTINGS["difficulty"] = diff
    sv = save or G["new_save"](cls)
    sv["bonfire"] = bonfire
    pad = pad or ScriptPad("t1")
    g.add_pad(pad); g.last_pad = pad
    g.start_session(sv, pad); step(g, 2)
    return pad
def bad_rects(g):
    out = []
    for e in g.track:
        if e[0] == "rect" and e[2] is not None:
            x, y, w, h = e[2]
            if x < 0 or y < 0 or x + w > G["W"] or y + h > G["H"]: out.append(e)
    return out
def untr(g): return [e for e in g.track if e[0] == "untr"]
def layout_issues(g, overlap=True):
    """text sticking out of a panel it starts in, and text drawn over other text (menus)."""
    out = []; pans = []; txt = []
    for e in g.track:                      # in draw order: a panel hides the text drawn before it
        if e[0] != "rect" or e[2] is None: continue
        r = pygame.Rect(e[2])
        if e[1] == "panel": pans.append(r); txt = [(t, q) for t, q in txt if not r.contains(q)]
        elif e[1] != "area": txt.append((e[1], r))
    for t, r in txt:
        for p in pans:
            if p.colliderect(r) and not p.contains(r) and p.collidepoint(r.center): out.append(("out_of_panel", t, tuple(r), tuple(p)))
    if overlap:
        for i in range(len(txt)):
            for j in range(i + 1, len(txt)):
                (a, ra), (b, rb) = txt[i], txt[j]
                if a == b and ra == rb: continue
                c = ra.clip(rb)
                if c.w > 1 and c.h > 3: out.append(("text_overlap", a, b, tuple(ra), tuple(rb)))
    return out
