import json
import os
import random
import re
import subprocess
import sys
import unittest

import pygame

from kultakiri.actors import (
    Player, award, give_power, pull_coins, separate_bumps, start_ghost, tick_ghost, tick_runner, touch_hazard,
)
from kultakiri.chunks import ALL_CHUNKS, BY_NAME
from kultakiri.const import EY, GLIDE_FALL, JUMP_V, PH, PW, RUN, SPEED_RUN
from kultakiri.font import has_glyph
from kultakiri.input import Pad
from kultakiri.physics import Body, _run_pilot, measure_gap, step_body, validate_chunk
from kultakiri.text import FI, tr
from kultakiri.version import load_version
from kultakiri.world import Coin, Pickup, World


class FakeGC:
    def __init__(self):
        self.axes = {}
        self.buttons = set()

    def get_axis(self, i):
        return self.axes.get(i, 0)

    def get_button(self, i):
        return i in self.buttons


class FakeJS:
    def __init__(self):
        self.axes = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.buttons = [0] * 16
        self.hat = (0, 0)

    def get_numaxes(self):
        return len(self.axes)

    def get_axis(self, i):
        return self.axes[i]

    def get_numhats(self):
        return 1

    def get_hat(self, i):
        return self.hat

    def get_numbuttons(self):
        return len(self.buttons)

    def get_button(self, i):
        return self.buttons[i]


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_version_is_only_in_json(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "version.json"), encoding="utf-8") as fh:
            version = json.loads(fh.read())["version"]
        self.assertEqual(version, load_version())
        self.assertEqual(version, "0.3")
        for dirpath, _dirs, files in os.walk(os.path.join(root, "kultakiri")):
            for name in files:
                if not name.endswith(".py"):
                    continue
                with open(os.path.join(dirpath, name), encoding="utf-8") as fh:
                    text = fh.read()
                self.assertNotIn('"0.1"', text)
                self.assertNotIn("'0.1'", text)

    def test_finnish_glyphs(self):
        for key, text in FI.items():
            cleaned = re.sub(r"%[sd]", "", text)
            for ch in cleaned:
                self.assertTrue(has_glyph(ch), "%s missing %r in %s" % (key, ch, text))
        self.assertEqual(tr("round", 1, 3), "ERÄ 1/3")
        self.assertIn("Ä", tr("p_double") + tr("d_shield") + tr("d_glide"))

    def test_same_mapping_on_gc_and_raw(self):
        gc = FakeGC()
        gc.axes[pygame.CONTROLLER_AXIS_LEFTX] = -32768
        gc.buttons.add(pygame.CONTROLLER_BUTTON_A)
        gc.buttons.add(pygame.CONTROLLER_BUTTON_START)
        gc.buttons.add(pygame.CONTROLLER_BUTTON_Y)
        pad = Pad("gc", gc, iid=1)
        pad.poll({})
        self.assertLess(pad.cur["x"], -0.5)
        self.assertTrue(pad.cur["jump"])
        self.assertTrue(pad.cur["start"])
        self.assertTrue(pad.cur["alt"])
        raw = FakeJS()
        raw.axes[0] = -1
        raw.buttons[Pad.RAW_JUMP] = 1
        raw.buttons[Pad.RAW_OPTIONS] = 1
        raw.buttons[Pad.RAW_TRIANGLE] = 1
        raw.hat = (1, 1)
        other = Pad("js", raw, iid=2)
        other.poll({})
        # Hat wins over the stick, same as a d-pad on the GameController path.
        gc.buttons.add(pygame.CONTROLLER_BUTTON_DPAD_RIGHT)
        gc.buttons.add(pygame.CONTROLLER_BUTTON_DPAD_UP)
        pad.poll({})
        self.assertEqual(pad.cur["jump"], other.cur["jump"])
        self.assertEqual(pad.cur["start"], other.cur["start"])
        self.assertEqual(pad.cur["alt"], other.cur["alt"])
        self.assertGreater(pad.cur["x"], 0.5)
        self.assertGreater(other.cur["x"], 0.5)
        self.assertLess(pad.cur["y"], -0.5)
        self.assertLess(other.cur["y"], -0.5)
        # Circle is jump too, on both paths.
        bare = Pad("gc", FakeGC(), iid=3)
        bare.dev.buttons.add(pygame.CONTROLLER_BUTTON_B)
        bare.poll({})
        self.assertTrue(bare.cur["jump"])
        raw2 = FakeJS()
        raw2.buttons[Pad.RAW_CIRCLE] = 1
        raw_pad = Pad("js", raw2, iid=4)
        raw_pad.poll({})
        self.assertTrue(raw_pad.cur["jump"])

    def test_jump_envelope_and_chunks(self):
        self.assertGreaterEqual(measure_gap(0), 40)
        self.assertGreater(measure_gap(0), measure_gap(24))
        self.assertGreater(measure_gap(0, speed=True), measure_gap(0))
        for chunk in ALL_CHUNKS:
            validate_chunk(chunk)
            _run_pilot(chunk, speed=True)

    def test_short_hop_is_shorter(self):
        def apex(hold):
            body = Body()
            body.y = 0
            body.on_ground = True
            body.coyote = 6
            best = 0
            for frame in range(80):
                step_body(body, 1, frame < hold, frame == 0, [])
                best = min(best, body.y)
            return best
        self.assertLess(apex(40), apex(6) - 10)

    def test_scroll_is_faster_than_a_normal_run(self):
        from kultakiri.const import MAX_RISE, RUN, SCROLL0, SCROLL_MAX, SPEED_RUN, TILE
        self.assertGreater(SCROLL0, RUN)
        self.assertGreater(SCROLL_MAX, RUN)
        self.assertGreaterEqual(SCROLL_MAX, SCROLL0)
        self.assertGreater(SPEED_RUN, SCROLL_MAX)
        self.assertEqual(MAX_RISE, TILE * 2)

    def test_settings_survive_a_missing_or_broken_file(self):
        import tempfile
        from kultakiri.settings import load_settings, save_settings
        missing = load_settings(os.path.join(tempfile.gettempdir(), "no-such-kultakiri.json"))
        self.assertEqual(missing["cpu_diff"], "normaali")
        self.assertGreater(missing["scroll0"], 1.8)
        broken = os.path.join(tempfile.gettempdir(), "kultakiri-broken.json")
        with open(broken, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertEqual(load_settings(broken)["rounds"], 3)
        nasty = os.path.join(tempfile.gettempdir(), "kultakiri-nasty.json")
        with open(nasty, "w", encoding="utf-8") as fh:
            fh.write('{"cpu_players": 9, "cpu_diff": "mahdoton", "scroll0": 0.2, "rounds": "x"}')
        safe = load_settings(nasty)
        self.assertLessEqual(safe["cpu_players"], 3)
        self.assertEqual(safe["cpu_diff"], "normaali")
        self.assertGreater(safe["scroll0"], 1.8)
        self.assertEqual(safe["rounds"], 3)
        path = os.path.join(tempfile.gettempdir(), "kultakiri-ok.json")
        self.assertTrue(save_settings(safe, path))
        self.assertEqual(load_settings(path)["sfx_vol"], safe["sfx_vol"])

    def test_opening_and_no_double_hard(self):
        from kultakiri.const import SCROLL_MAX
        world = World(random.Random(2))
        world.ensure(9000, SCROLL_MAX)
        names = [chunk.name for _o, chunk in world.placed]
        self.assertEqual(names[0], "alku")
        self.assertIn("maali", names)
        self.assertIn("katto", names)
        self.assertIn("murea", names)
        self.assertIn("liuku", names)
        for left, right in zip(names, names[1:]):
            self.assertNotEqual(left, right)
            self.assertFalse(BY_NAME[left].hard and BY_NAME[right].hard)
        self.assertTrue(any(chunk.tier >= 2 for _o, chunk in world.placed))

    def test_countdown_locks_movement_until_go(self):
        from kultakiri.game import Game
        from kultakiri.input import ScriptPad
        screen = pygame.display.set_mode((320, 180))
        game = Game(screen)
        pad = ScriptPad("count")
        game.pads[pad.id] = pad
        game.add_player(pad)
        game.begin_round()
        x0 = game.players[0].body.x
        while game.state == "ready":
            pad.desired = {"x": 1.0, "y": 0.0, "jump": True, "start": False, "back": False, "alt": False}
            game.update()
            if game.state == "ready":
                self.assertEqual(game.players[0].body.x, x0)
                self.assertEqual(game.camera, 0)
                self.assertEqual(game.players[0].body.vx, 0)
        self.assertEqual(game.state, "play")
        self.assertGreater(game.camera, 0)
        self.assertGreater(game.go_flash, 0)

    def test_powerups_do_what_they_say(self):
        ground = [(-20, EY, 400)]
        player = Player(0, None)
        other = Player(1, None)
        player.body.x = 10
        player.body.y = EY - PH
        player.body.on_ground = True
        other.body.x = 40
        other.body.y = EY - PH
        other.body.on_ground = True
        other.state = "run"
        stats = {"got_powers": []}
        give_power(player, "speed", [player, other], stats)
        for _ in range(20):
            tick_runner(player, 1, False, False, ground, stats)
        self.assertGreater(player.body.vx, RUN + 0.2)
        self.assertGreater(stats["speed_fast"], 0)
        give_power(player, "slow", [player, other], stats)
        self.assertGreater(other.slow_t, 0)
        self.assertEqual(player.slow_t, 0)
        give_power(player, "glide", [player, other], stats)
        player.body.on_ground = False
        player.body.vy = 3
        player.body.coyote = 0
        tick_runner(player, 1, True, False, [], stats)
        self.assertAlmostEqual(player.body.vy, GLIDE_FALL, places=2)
        self.assertGreater(stats["glide_frames"], 0)
        give_power(player, "double", [player, other], stats)
        player.body.on_ground = False
        player.body.coyote = 0
        player.body.air_jumps = 1
        player.body.vy = 1
        before = player.body.vy
        did = tick_runner(player, 1, True, True, [], stats)
        self.assertEqual(did, "airjump")
        self.assertLess(player.body.vy, before)
        self.assertAlmostEqual(player.body.vy, JUMP_V + 0.28, places=2)
        give_power(player, "shield", [player, other], stats)
        self.assertTrue(player.shield)
        hazards = [(player.body.x, player.body.y, PW, PH)]
        self.assertEqual(touch_hazard(player, hazards, stats), "block")
        self.assertFalse(player.shield)
        self.assertGreater(stats["shield_block"], 0)
        player.inv = 0
        self.assertEqual(touch_hazard(player, hazards, stats), "hit")
        self.assertLess(player.body.vx, 0)
        give_power(player, "magnet", [player, other], stats)
        coin = Coin(player.body.x + 40, player.body.y)
        player.state = "run"
        pull_coins([player], [coin], stats)
        self.assertLess(coin.x, player.body.x + 40)
        self.assertGreater(stats["magnet_pulls"], 0)
        self.assertEqual(len(stats["got_powers"]), 6)

    def test_bump_is_not_a_stomp(self):
        a = Player(0, None)
        b = Player(1, None)
        a.state = b.state = "run"
        a.body.x, b.body.x = 0, 4
        a.body.y = b.body.y = EY - PH
        a.body.vy = b.body.vy = 0
        separate_bumps([a, b], {})
        self.assertLess(a.body.vx, 0)
        self.assertGreater(b.body.vx, 0)
        self.assertEqual(a.body.vy, 0)
        self.assertEqual(b.body.vy, 0)
        # Landing on a head does not bounce, kill, or become a platform.
        a.body.x, b.body.x = 0, 1
        a.body.y = EY - PH
        b.body.y = a.body.y - PH + 2
        b.body.vy = 2
        a_state, b_state = a.state, b.state
        separate_bumps([a, b], {})
        self.assertEqual(a.state, a_state)
        self.assertEqual(b.state, b_state)
        self.assertGreater(b.body.vy, 0)
        ground = [(-10, EY, 80)]
        for _ in range(25):
            step_body(b.body, 0, False, False, ground)
        self.assertGreaterEqual(b.body.feet(), EY - 1)
        self.assertEqual(a.state, "run")

    def test_ghost_rescue_then_out(self):
        player = Player(0, None)
        player.body.y = 400
        self.assertEqual(start_ghost(player, 0), "ghost")
        self.assertEqual(player.rescues, 0)
        solids = [(40, EY, 220)]
        revived = False
        for _ in range(90):
            # Steer down onto the ledge under the ghost.
            result = tick_ghost(player, 0.2, 1, solids, 0, 1.0)
            if result == "revive":
                revived = True
                break
        self.assertTrue(revived)
        self.assertEqual(player.state, "run")
        self.assertEqual(start_ghost(player, 0), "out")
        self.assertEqual(player.state, "out")
        # Coins still count while a ghost is in play: covered by collect() allowing ghosts.
        ghost = Player(1, None)
        start_ghost(ghost, 0)
        from kultakiri.actors import collect
        coin = Coin(ghost.body.x + PW * 0.5, ghost.body.y + PH * 0.5)
        collect(ghost, [coin], [], [ghost], {})
        self.assertEqual(ghost.coins, 1)
        self.assertFalse(coin.alive)

    def test_award_prefers_the_last_runner(self):
        a = Player(0, None)
        b = Player(1, None)
        a.max_x, b.max_x = 100, 500
        a.coins, b.coins = 20, 0
        a.state, b.state = "out", "run"
        winners = award([a, b])
        self.assertEqual(winners, [b])
        self.assertGreater(b.bank, a.bank)


class BootTests(unittest.TestCase):
    def test_main_and_long_sim(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env = dict(os.environ)
        env.update({
            "SDL_VIDEODRIVER": "dummy",
            "SDL_AUDIODRIVER": "dummy",
            "KULTAKIRI_WINDOWED": "1",
            "KULTAKIRI_NO_MUSIC": "1",
            "KULTAKIRI_NO_SFX": "1",
            "PYTHONPATH": root,
            "SDL_GAMECONTROLLER_ALLOW_BACKGROUND_EVENTS": "1",
        })
        boot = dict(env)
        boot["KULTAKIRI_FRAMES"] = "45"
        subprocess.run([sys.executable, "-m", "kultakiri"], cwd=root, env=boot, check=True, timeout=60)
        subprocess.run([sys.executable, os.path.join(root, "build.py")], cwd=root, check=True, timeout=60)
        version = load_version()
        built = os.path.join(root, "Kultakiri%s.pygame" % version)
        self.assertTrue(os.path.isfile(built))
        with open(built, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("return '%s'" % version, text)
        subprocess.run([sys.executable, built], cwd=root, env=boot, check=True, timeout=60)
        sim = dict(env)
        sim["KULTAKIRI_AUTOPLAY"] = "1"
        sim["KULTAKIRI_FRAMES"] = str(60 * 180)
        sim["KULTAKIRI_SEED"] = "1"
        proc = subprocess.run(
            [sys.executable, built], cwd=root, env=sim, check=True, timeout=180, capture_output=True, text=True,
        )
        line = [ln for ln in proc.stdout.splitlines() if ln.startswith("KULTAKIRI_STATS ")]
        self.assertTrue(line, proc.stdout[-500:] + proc.stderr[-500:])
        stats = json.loads(line[-1].split(" ", 1)[1])
        self.assertGreaterEqual(stats["frames"], 60 * 180)
        self.assertEqual(stats["chunk_fail"], 0)
        self.assertGreaterEqual(stats["validated"], 12)
        self.assertGreaterEqual(stats["chunk_types"], 8)
        self.assertGreaterEqual(stats["power_types"], 6)
        self.assertIn("double", stats["got_powers"])
        self.assertGreaterEqual(stats["speed_fast"], 1)
        self.assertGreaterEqual(stats["shield_on"], 1)
        self.assertGreaterEqual(stats["magnet_pulls"], 1)
        self.assertGreaterEqual(stats["slow_on"], 1)
        self.assertGreaterEqual(stats["glide_frames"], 1)
        self.assertGreaterEqual(stats["ghosts"], 1)
        self.assertGreaterEqual(stats["bumps"], 1)
        self.assertGreaterEqual(stats["rounds_ended"], 1)


if __name__ == "__main__":
    unittest.main()
