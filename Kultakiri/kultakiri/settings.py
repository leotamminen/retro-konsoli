# Small JSON file next to the game. A missing or broken file falls back to defaults.
import json
import os

from .const import POWER_KINDS, RUN

DIFFS = ("helppo", "normaali", "vaikea")
RAMPS = {"hidas": 0.000004, "normaali": 0.000008, "nopea": 0.000016}
FREQS = {"harva": 0.45, "normaali": 0.75, "tihea": 1.0}
SCROLL_STEPS = (1.85, 1.88, 1.91, 1.96)

DEFAULTS = {
    "cpu_players": 0,
    "cpu_diff": "normaali",
    "rounds": 3,
    "scroll0": 1.85,
    "ramp": "normaali",
    "power_freq": "normaali",
    "powers": {k: True for k in POWER_KINDS},
    "sfx_vol": 8,
    "music_vol": 5,
    "fullscreen": True,
}


def settings_path():
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(here) == "kultakiri":
        here = os.path.dirname(here)
    return os.path.join(here, "kultakiri_settings.json")


def _clamp_int(value, lo, hi, default):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def load_settings(path=None):
    path = path or settings_path()
    data = {}
    try:
        with open(path, encoding="utf-8") as fh:
            loaded = json.load(fh)
        if isinstance(loaded, dict):
            data = loaded
    except (OSError, ValueError, TypeError):
        data = {}
    out = dict(DEFAULTS)
    out["cpu_players"] = _clamp_int(data.get("cpu_players"), 0, 3, 0)
    diff = data.get("cpu_diff")
    out["cpu_diff"] = diff if diff in DIFFS else "normaali"
    out["rounds"] = _clamp_int(data.get("rounds"), 1, 7, 3)
    try:
        scroll = float(data.get("scroll0", out["scroll0"]))
    except (TypeError, ValueError):
        scroll = out["scroll0"]
    # A normal run must never catch the camera, whatever was saved.
    out["scroll0"] = max(RUN + 0.02, min(2.2, scroll))
    ramp = data.get("ramp")
    out["ramp"] = ramp if ramp in RAMPS else "normaali"
    freq = data.get("power_freq")
    out["power_freq"] = freq if freq in FREQS else "normaali"
    powers = dict(DEFAULTS["powers"])
    raw = data.get("powers")
    if isinstance(raw, dict):
        for key in POWER_KINDS:
            if key in raw:
                powers[key] = bool(raw[key])
    out["powers"] = powers
    out["sfx_vol"] = _clamp_int(data.get("sfx_vol"), 0, 10, 8)
    out["music_vol"] = _clamp_int(data.get("music_vol"), 0, 10, 5)
    out["fullscreen"] = bool(data.get("fullscreen", True)) if "fullscreen" in data else True
    return out


def save_settings(data, path=None):
    path = path or settings_path()
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except OSError:
        return False
    return True
