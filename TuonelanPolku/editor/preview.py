"""Build a playable preview without touching a shipped TuonelanPolku*.pygame."""
import subprocess
import sys
from pathlib import Path


def preview_path(root):
    return Path(root) / "esikatselu" / "TuonelanPolku-esikatselu.pygame"


def build_preview(root, dest=None):
    root = Path(root)
    dest = Path(dest) if dest else preview_path(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(root / "build.py"), "--maps", str(root / "maps"), str(dest)]
    result = subprocess.run(command, capture_output=True, text=True)
    message = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, message.strip(), dest
