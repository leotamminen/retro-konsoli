import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("KULTAKIRI_NO_MUSIC", "1")
os.environ.setdefault("KULTAKIRI_NO_SFX", "1")
os.environ.setdefault("KULTAKIRI_WINDOWED", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
