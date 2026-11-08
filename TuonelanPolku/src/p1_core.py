#!/usr/bin/env python3
# TUONELAN POLKU (Path of Tuonela) - light 2D soulslike for Batocera (pygame 2.6.1).
# Single file, no assets, no numpy. Copy to /userdata/roms/pygame/
# Settings and save game are written next to this file.
import os, sys, math, random, array, json, threading, time
import pygame

W, H = 320, 180
TILE = 16
VERSION = "1.2"
FPS = 60

# ---------------- physics constants (shared by the game and the traversal tests) ----------------
GRAV = 0.30
JUMP_V = -5.4          # apex ~48.6 px (3 tiles)
MAX_FALL = 7.0
RUN = 1.5
DJ_V = -4.8
PW_, PH_ = 10, 18      # player hitbox

# ---------------- difficulty ----------------
DIFFS = ["easy", "normal", "hard", "brutal", "tuonela"]
DIFF = {
    "easy":    dict(dmg=0.55, hp=0.75, spd=0.92, tele=1.35, flask=1.35, aggr=0.60, souls=1.25, parry=1.5),
    "normal":  dict(dmg=1.00, hp=1.00, spd=1.00, tele=1.00, flask=1.00, aggr=1.00, souls=1.00, parry=1.0),
    "hard":    dict(dmg=1.50, hp=1.25, spd=1.08, tele=0.85, flask=0.85, aggr=1.30, souls=1.10, parry=0.9),
    "brutal":  dict(dmg=2.10, hp=1.60, spd=1.18, tele=0.70, flask=0.70, aggr=1.70, souls=1.20, parry=0.8),
    "tuonela": dict(dmg=3.40, hp=2.20, spd=1.32, tele=0.52, flask=0.50, aggr=2.50, souls=1.50, parry=0.7),
}

# ---------------- settings ----------------
LANGS = ["fi", "en"]
DEFAULTS = {"lang": "fi", "difficulty": "normal", "penalty": "classic", "music": True, "music_vol": 6,
            "sfx": True, "sfx_vol": 8, "shake": True, "dmgnum": True, "flash": True, "prompts": "ps",
            "runmode": "auto", "hints": True, "perf": False, "test_weapon": False}
CHOICES = {"difficulty": DIFFS, "penalty": ["classic", "mild"], "prompts": ["ps", "xbox", "kb"],
           "runmode": ["auto", "analog"], "lang": LANGS}
SETTINGS = dict(DEFAULTS)

def _here():
    return os.path.dirname(os.path.abspath(__file__))
def settings_path():
    return os.environ.get("TUONELA_SETTINGS") or os.path.join(_here(), "tuonelan_polku_settings.json")
def save_path():
    return os.environ.get("TUONELA_SAVE") or os.path.join(_here(), "tuonelan_polku_save.json")

def sanitize_settings(d):
    st = dict(DEFAULTS)
    if not isinstance(d, dict): return st
    for k, v in d.items():
        if k not in DEFAULTS: continue
        dv = DEFAULTS[k]
        if isinstance(dv, bool):
            if isinstance(v, bool): st[k] = v
        elif k in ("music_vol", "sfx_vol"):
            if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 10: st[k] = v
        elif k in CHOICES:
            if isinstance(v, str) and v in CHOICES[k]: st[k] = v
    return st

def load_settings(path=None):
    try:
        with open(path or settings_path()) as f: d = json.load(f)
    except Exception:
        d = {}
    st = sanitize_settings(d)
    SETTINGS.clear(); SETTINGS.update(st)
    return st

def atomic_write_json(path, data):
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(data, f, indent=1); f.flush()
            try: os.fsync(f.fileno())
            except OSError: pass
        os.replace(tmp, path)
        return True
    except Exception as e:
        print("not saved:", e)
        try: os.remove(tmp)
        except OSError: pass
        return False

def save_settings(path=None):
    return atomic_write_json(path or settings_path(), SETTINGS)

def D():
    return DIFF[SETTINGS["difficulty"]]
def tele(n):
    """Telegraph length in frames, scaled by difficulty (never below 11 frames)."""
    return max(11, int(n * D()["tele"]))
def rest(n):
    """Idle time between enemy actions: shorter when more aggressive."""
    return max(4, int(n / D()["aggr"]))

# ---------------- save game ----------------
STAT_KEYS = ["vit", "end", "str", "foc"]
CLASSES = ["warrior", "sage", "hunter"]
def level_cost(lv):
    return int(40 + 24 * lv + 0.9 * lv * lv)
MAX_LEVEL = 40

def new_save(cls="warrior"):
    return {"v": 1, "cls": cls, "level": 1, "stats": {k: 0 for k in STAT_KEYS}, "souls": 0,
            "taken": [], "opened": [], "bosses": [], "seen": [], "bonfire": "b0",
            "stain": [], "p2": None, "deaths": 0, "time": 0, "done": False, "flasks": 0,
            "mapseen": [], "louhi_unlocked":False, "vellamo_unlocked":False, "vellamo_visited":False, "aino_freed":False, "vellamo_done":False, "ng": 0, "ng_ready": False}

def _int(v, lo, hi, dflt):
    if isinstance(v, bool) or not isinstance(v, int): return dflt
    return max(lo, min(hi, v))

def _strlist(v, allowed=None):
    if not isinstance(v, list): return []
    out = []
    for x in v:
        if isinstance(x, str) and len(x) < 40 and (allowed is None or x in allowed) and x not in out: out.append(x)
    return out

def _sanitize_char(c):
    if not isinstance(c, dict) or c.get("cls") not in CLASSES: return None
    st = c.get("stats") if isinstance(c.get("stats"), dict) else {}
    stats = {k: _int(st.get(k), 0, MAX_LEVEL, 0) for k in STAT_KEYS}
    return {"cls": c["cls"], "level": _int(c.get("level"), 1, 4 * MAX_LEVEL, 1) , "stats": stats,
            "souls": _int(c.get("souls"), 0, 99999999, 0)}

def sanitize_save(d, valid_bonfires=None, valid_ids=None):
    """Returns a clean save dict, or None if the data cannot be a save."""
    if not isinstance(d, dict): return None
    ch = _sanitize_char({"cls": d.get("cls"), "level": d.get("level"), "stats": d.get("stats"), "souls": d.get("souls")})
    if ch is None: return None
    s = new_save(ch["cls"])
    s.update(ch)
    s["level"] = 1 + sum(s["stats"].values())     # level is always derived from the stats
    s["taken"] = _strlist(d.get("taken")); s["opened"] = _strlist(d.get("opened"))
    s["bosses"] = _strlist(d.get("bosses")); s["seen"] = _strlist(d.get("seen"))
    bf = d.get("bonfire")
    if not isinstance(bf, str) or (valid_bonfires and bf not in valid_bonfires): bf = "b0"
    s["bonfire"] = bf
    if valid_bonfires: s["seen"] = [b for b in s["seen"] if b in valid_bonfires]
    if bf not in s["seen"]: s["seen"].append(bf)
    stain = []
    if isinstance(d.get("stain"), list):
        for e in d["stain"][:2]:
            if isinstance(e, dict) and all(isinstance(e.get(k), (int, float)) and not isinstance(e.get(k), bool) for k in ("x", "y", "souls")):
                stain.append({"p": _int(e.get("p"), 0, 1, 0), "x": float(e["x"]), "y": float(e["y"]), "souls": _int(e["souls"], 0, 99999999, 0)})
    s["stain"] = stain
    p2 = _sanitize_char(d.get("p2")) if d.get("p2") else None
    if p2: p2["level"] = 1 + sum(p2["stats"].values())
    s["p2"] = p2
    s["deaths"] = _int(d.get("deaths"), 0, 9999999, 0); s["time"] = _int(d.get("time"), 0, 99999999, 0)
    s["done"] = bool(d.get("done")) if isinstance(d.get("done"), bool) else False
    s["flasks"] = _int(d.get("flasks"), 0, 99, 0)
    s["louhi_unlocked"] = bool(d.get("louhi_unlocked", False))
    if "tytti" in s["bosses"]: s["louhi_unlocked"] = True
    # v1.1: explored map cells ("cx,cy" and "arena:<boss>"). Saves from 1.0 have none -> None = rebuild from progress
    s["mapseen"] = _strlist(d.get("mapseen")[:600]) if isinstance(d.get("mapseen"), list) else None
    # The realm opens only after Louhi has fallen in this cycle. A stale flag cannot open it.
    s["ng"] = _int(d.get("ng"), 0, 8, 0)
    s["ng_ready"] = bool(d.get("ng_ready", False)) or bool(d.get("vellamo_done", False)) or s["ng"] > 0
    s['vellamo_unlocked'] = "louhi" in s["bosses"]
    s['vellamo_visited'] = bool(d.get('vellamo_visited', False)) and s['vellamo_unlocked']
    s['aino_freed'] = bool(d.get('aino_freed', False)) and "aino" in s["bosses"]
    s['vellamo_done'] = bool(d.get('vellamo_done', False)) and "vellamo" in s["bosses"]
    if s["vellamo_done"]: s["ng_ready"] = True
    return s

def load_save(path=None, valid_bonfires=None):
    """Returns (save or None, status). status: 'none' | 'ok' | 'backup' | 'corrupt'."""
    path = path or save_path()
    for p, tag in ((path, "ok"), (path + ".bak", "backup")):
        if not os.path.exists(p): continue
        try:
            with open(p) as f: d = json.load(f)
            s = sanitize_save(d, valid_bonfires)
            if s is not None: return s, tag
        except Exception:
            pass
    if os.path.exists(path) or os.path.exists(path + ".bak"):
        try: os.replace(path, path + ".corrupt")
        except OSError: pass
        return None, "corrupt"
    return None, "none"

def write_save(s, path=None):
    path = path or save_path()
    if os.path.exists(path):
        try:     # keep the previous good save as a backup
            with open(path) as f: json.load(f)
            os.replace(path, path + ".bak")
        except Exception:
            pass
    return atomic_write_json(path, s)

# ---------------- translations ----------------
class TStr(str):
    """A string that came out of the translation table (tests check every rendered text is one)."""
TR = {"fi": {}, "en": {}}
def tr(key, *a):
    t = TR.get(SETTINGS.get("lang", "fi"), TR["fi"]).get(key) or TR["en"][key]
    return TStr(t % a if a else t)
def num(v): return TStr(str(v))      # numbers need no translation

def wrap(font, text, width):
    """Word-wrap into lines no wider than width (TStr lines)."""
    out = []
    for para in str(text).split("\n"):
        line = ""
        for wd in para.split(" "):
            t = (line + " " + wd).strip()
            if font.size(t)[0] <= width or not line: line = t
            else: out.append(TStr(line)); line = wd
        out.append(TStr(line))
    return out

# palette entry is defined after PAL in the world renderer
# # palette extension is defined with other environment palettes dict(sky=((5,7,17),(17,12,30)), far=(13,18,34), mid=(14,19,29), solid=(43,49,64), top=(95,113,139), detail=(109,130,161), ambient=(33,33,50), fog=(61,68,104), top2=(86,104,131))
CANVAS_CACHE={}
save_canvas=lambda k,fn: CANVAS_CACHE.setdefault(k,fn())
