#!/usr/bin/env python3
# Render the three reference screens with the real game, under a dummy video driver.
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KULTAKIRI_NO_MUSIC"] = "1"
os.environ["KULTAKIRI_NO_SFX"] = "1"
os.environ["KULTAKIRI_WINDOWED"] = "1"

import pygame

from kultakiri.const import H, W
from kultakiri.game import Game
from kultakiri.input import ScriptPad


def save(game, path):
    game.draw()
    big = pygame.transform.scale(game.canvas, (W * 3, H * 3))
    pygame.image.save(big, path)
    print(path)


def boot():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    game = Game(screen)
    game.autoplay = True
    return game


def join_screen(path):
    game = boot()
    for i in range(2):
        pad = ScriptPad("shot%d" % i)
        game.pads[pad.id] = pad
        game.add_player(pad)
    for _ in range(8):
        game.t += 1
        game.draw()
    save(game, path)
    pygame.quit()


def gameplay(path):
    game = boot()
    game.seed = 3
    for i in range(4):
        pad = ScriptPad("run%d" % i)
        pad.skill = 1.0
        pad.auto = True
        game.pads[pad.id] = pad
        game.add_player(pad)
        game.players[-1].pilot.skill = 1.0
    game.begin_round()
    # Skip the countdown so the shot is the race, with pickups still in view.
    game.goto("play")
    found = False
    for _ in range(500):
        game.drive()
        game.poll_pads()
        game.t += 1
        game.up_play()
        alive = sum(p.state == "run" for p in game.players)
        visible = [
            pw for pw in game.world.powers
            if pw.alive and game.camera - 8 <= pw.x <= game.camera + W - 8
        ]
        kinds = {p.main_power() for p in game.players if p.main_power() and p.state == "run"}
        if alive == 4 and len(visible) >= 2 and len(kinds) >= 2:
            found = True
            break
    if not found:
        sys.exit("no gameplay frame with 4 runners and powerups")
    save(game, path)
    pygame.quit()


def results(path):
    game = boot()
    for i, (bank, wins, coins) in enumerate(((980, 2, 40), (640, 1, 28), (410, 0, 22), (260, 0, 11))):
        pad = ScriptPad("end%d" % i)
        game.pads[pad.id] = pad
        player = game.add_player(pad)
        player.bank = bank
        player.wins = wins
        player.total_coins = coins
        player.coins = coins
    game.round_no = 3
    game.goto("results")
    game.t = 10
    save(game, path)
    pygame.quit()


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    join_screen(os.path.join(out, "kultakiri_join.png"))
    gameplay(os.path.join(out, "kultakiri_gameplay.png"))
    results(os.path.join(out, "kultakiri_results.png"))
