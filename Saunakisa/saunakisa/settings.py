# Couch settings, written next to the game. A missing or broken file never stops play.
import json
import os

DEFAULTS = {
    "cpus": 0,
    "difficulty": "normaali",
    "rounds": 3,
    "round_secs": 78,
    "heat": "normaali",
    "pickups": "normaali",
    "sfx_vol": 8,
    "music_vol": 6,
}

CHOICES = {
    "cpus": (0, 1, 2, 3),
    "difficulty": ("helppo", "normaali", "vaikea"),
    "rounds": (1, 3, 5),
    "round_secs": (60, 78, 90),
    "heat": ("hidas", "normaali", "nopea"),
    "pickups": ("harvoin", "normaali", "usein"),
    "sfx_vol": tuple(range(11)),
    "music_vol": tuple(range(11)),
}

HEAT_MUL = {"hidas": 0.75, "normaali": 1.0, "nopea": 1.25}
PICKUP_SEC = {"harvoin": 18, "normaali": 11, "usein": 6}


def game_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    # Package layout keeps the file beside version.json. The bundled
    # .pygame is one script, so __file__ is already that file's folder.
    parent = os.path.dirname(here)
    if os.path.basename(here) == "saunakisa" and os.path.isfile(os.path.join(parent, "version.json")):
        return parent
    return here


def crash_log_path():
    override = os.environ.get("SAUNAKISA_CRASH_LOG")
    if override:
        return override
    return os.path.join(game_dir(), "saunakisa_crash.log")


def write_crash(text):
    path = crash_log_path()
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
            if text and not text.endswith("\n"):
                fh.write("\n")
        return path
    except Exception:
        return None


def settings_path():
    override = os.environ.get("SAUNAKISA_SETTINGS")
    if override:
        return override
    return os.path.join(game_dir(), "saunakisa_settings.json")


def sanitize_settings(data):
    clean = dict(DEFAULTS)
    if not isinstance(data, dict):
        return clean
    for key, default in DEFAULTS.items():
        value = data.get(key, default)
        if key in ("sfx_vol", "music_vol", "cpus", "rounds", "round_secs"):
            if isinstance(value, bool) or not isinstance(value, int):
                continue
            if value in CHOICES[key]:
                clean[key] = value
            continue
        if isinstance(value, str) and value in CHOICES.get(key, ()):
            clean[key] = value
    return clean


def load_settings(path=None):
    path = path or settings_path()
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        data = {}
    return sanitize_settings(data)


def save_settings(settings, path=None):
    path = path or settings_path()
    clean = sanitize_settings(settings)
    tmp = path + ".tmp"
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(clean, fh, indent=1, sort_keys=True)
            fh.write("\n")
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        os.replace(tmp, path)
        return True
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False
