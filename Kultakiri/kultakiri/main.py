# Batocera: copy the built Kultakiri<version>.pygame to /userdata/roms/pygame/
import json
import os

import pygame

from .audio import prepare_audio, start_audio
from .const import FPS, H, W
from .game import Game


def open_screen():
    from .settings import load_settings
    want_full = bool(load_settings().get("fullscreen", True))
    windowed = bool(os.environ.get("KULTAKIRI_WINDOWED")) or not want_full
    fast = bool(os.environ.get("KULTAKIRI_FRAMES") or os.environ.get("KULTAKIRI_AUTOPLAY"))
    dummy = os.environ.get("SDL_VIDEODRIVER") == "dummy"
    flags = 0 if dummy else pygame.SCALED
    if not windowed and not dummy:
        flags |= pygame.FULLSCREEN
    vsync = 0 if fast or dummy else 1
    try:
        return pygame.display.set_mode((W, H), flags, vsync=vsync)
    except TypeError:
        try:
            return pygame.display.set_mode((W, H), flags)
        except pygame.error:
            return pygame.display.set_mode((W, H))
    except pygame.error:
        return pygame.display.set_mode((W, H))


def main():
    os.environ.setdefault("SDL_GAMECONTROLLER_ALLOW_BACKGROUND_EVENTS", "1")
    frames = int(os.environ.get("KULTAKIRI_FRAMES") or "0")
    fast = bool(frames or os.environ.get("KULTAKIRI_AUTOPLAY"))
    prepare_audio()
    pygame.init()
    start_audio()
    try:
        from pygame._sdl2 import controller
        controller.init()
    except Exception:
        pass
    screen = open_screen()
    pygame.display.set_caption("KULTAKIRI")
    pygame.mouse.set_visible(False)
    game = Game(screen)
    if os.environ.get("KULTAKIRI_AUTOPLAY"):
        game.arm_autoplay(int(os.environ.get("KULTAKIRI_SEED") or "1"))
    clock = pygame.time.Clock()
    n = 0
    while game.running:
        game.update()
        if game.reopen_screen:
            game.reopen_screen = False
            screen = open_screen()
            game.screen = screen
        game.draw()
        pygame.display.flip()
        if not fast:
            clock.tick(FPS)
        n += 1
        if frames and n >= frames:
            break
    if game.autoplay:
        print("KULTAKIRI_STATS " + json.dumps(game.public_stats(), separators=(",", ":")))
    pygame.quit()


if __name__ == "__main__":
    main()
