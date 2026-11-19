import json
import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SAUNAKISA_NO_SFX", "1")
os.environ.setdefault("SAUNAKISA_NO_MUSIC", "1")
os.environ.setdefault("SAUNAKISA_WINDOWED", "1")
os.environ["SAUNAKISA_SETTINGS"] = "/tmp/saunakisa-test-settings.json"
os.environ["SAUNAKISA_CRASH_LOG"] = "/tmp/saunakisa-test-crash.log"

import pygame

from saunakisa.actors import Bot, Player, heat_rate, step_player, throw_into, try_faint
from saunakisa.settings import load_settings, save_settings, sanitize_settings, write_crash
from saunakisa.const import (
    FPS, HEAT_MAX, HEAT_RATE, MIN_FRAMES, PLACES, POINT_RATE, ROUND_FRAMES, STOVE_X,
)
from saunakisa.font import has_glyph
from saunakisa.game import Game
from saunakisa.input import Pad, ScriptPad, blank
from saunakisa.text import FI
from saunakisa.version import load_version
from saunakisa.world import Room


def boot(players=4, seed=1):
    screen = pygame.display.get_surface() or pygame.display.set_mode((320, 180))
    game = Game(screen)
    game.seed = seed
    game.rng = random.Random(seed + 3)
    bots = []
    names = ("ihminen", "vaikea", "normaali", "helppo")[:players]
    for i, name in enumerate(names):
        pad = ScriptPad("t%d" % i)
        game.pads[pad.id] = pad
        game.add_player(pad)
        bots.append(Bot(name, random.Random(seed * 100 + i + 1)))
    game.begin_round()
    return game, bots


def run_round(players=4, seed=1, draw=False):
    game, bots = boot(players, seed)
    frames = 0
    limit = FPS * 100
    while game.state != "roundend" and frames < limit:
        for bot, player in zip(bots, game.players):
            if game.state in ("ready", "play"):
                player.pad.desired = bot.decide(player, game.room, game.players)
            else:
                player.pad.desired = blank()
        game.update()
        if draw:
            game.draw()
        frames += 1
        for player in game.players:
            if player.heat != player.heat or player.score != player.score:
                raise AssertionError("non-finite body")
    return game, frames


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320, 180))

    def test_version_comes_from_json(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "version.json"), encoding="utf-8") as fh:
            version = json.loads(fh.read())["version"]
        self.assertEqual(version, "0.3")
        self.assertEqual(load_version(), version)
        quoted = '"%s"' % version
        squoted = "'%s'" % version
        for dirpath, _dirs, files in os.walk(os.path.join(root, "saunakisa")):
            for name in files:
                if not name.endswith(".py"):
                    continue
                with open(os.path.join(dirpath, name), encoding="utf-8") as fh:
                    text = fh.read()
                self.assertNotIn(quoted, text)
                self.assertNotIn(squoted, text)

    def test_finnish_glyphs_exist(self):
        for key, text in FI.items():
            shown = text.replace("%s", "X").replace("%d", "1")
            for ch in shown:
                self.assertTrue(has_glyph(ch), "%s uses %r" % (key, ch))

    def test_higher_bench_is_hotter_and_richer(self):
        self.assertGreater(heat_rate("high", 40), heat_rate("mid", 40))
        self.assertGreater(heat_rate("mid", 40), heat_rate("low", 40))
        self.assertGreater(heat_rate("low", 40), heat_rate("floor", 40))
        self.assertLess(HEAT_RATE["avanto"], 0)
        self.assertGreater(POINT_RATE["high"], POINT_RATE["mid"])
        self.assertEqual(POINT_RATE["porch"], 0)
        self.assertEqual(POINT_RATE["avanto"], 0)

    def test_quiet_high_bench_faints_before_the_clock_low_does_not(self):
        room = Room(random.Random(1))
        room.event_in = 10 ** 9
        high = Player(0, ScriptPad("h"))
        low = Player(1, ScriptPad("l"))
        high.reset_round("high", 196)
        low.reset_round("low", 186)
        faint_at = None
        for frame in range(ROUND_FRAMES):
            room.heat = min(100.0, room.heat + 0.40 / FPS)
            step_player(high, 0, 0, False, room)
            step_player(low, 0, 0, False, room)
            if faint_at is None and high.mode == "faint":
                faint_at = frame
        self.assertIsNotNone(faint_at)
        self.assertGreater(faint_at, 40 * FPS)
        self.assertLess(faint_at, 70 * FPS)
        self.assertEqual(low.mode, "move")
        self.assertGreater(high.score, 0)
        kept = high.score
        self.assertLess(kept, POINT_RATE["high"] * (faint_at / FPS))
        self.assertAlmostEqual(kept, POINT_RATE["high"] * (faint_at / FPS) * 0.70, delta=POINT_RATE["high"])

    def test_avanto_cools_and_scores_nothing(self):
        room = Room(random.Random(2))
        room.event_in = 10 ** 9
        player = Player(0, ScriptPad("a"))
        player.reset_round("avanto", 30)
        player.heat = 80
        before = player.score
        for _ in range(3 * FPS):
            step_player(player, 0, 0, False, room)
        self.assertLess(player.heat, 20)
        self.assertAlmostEqual(player.score, before, places=3)
        self.assertEqual(player.mode, "move")

    def test_loyly_cooks_the_room_and_the_rival_more_than_the_thrower(self):
        room = Room(random.Random(3))
        room.event_in = 10 ** 9
        thrower = Player(0, ScriptPad("t"))
        rival = Player(1, ScriptPad("r"))
        thrower.reset_round("floor", STOVE_X + 10)
        rival.reset_round("high", 196)
        thrower.heat = 20
        rival.heat = 20
        room.heat = 30
        events = step_player(thrower, 0, 0, True, room)
        self.assertIn("loyly", events)
        throw_into(thrower, [thrower, rival], room)
        self.assertGreater(room.heat, 30)
        self.assertAlmostEqual(thrower.heat, 25, delta=0.2)
        self.assertAlmostEqual(rival.heat, 28, delta=0.2)
        self.assertGreater(thrower.loyly_cd, FPS)

    def test_faint_drops_points_and_stops_the_body(self):
        room = Room(random.Random(4))
        room.event_in = 10 ** 9
        player = Player(0, ScriptPad("f"))
        player.reset_round("high", 196)
        player.score = 100
        player.heat = HEAT_MAX
        self.assertTrue(try_faint(player))
        self.assertEqual(player.mode, "faint")
        self.assertAlmostEqual(player.score, 70, places=3)
        for _ in range(FPS):
            step_player(player, 1, -1, True, room)
        self.assertEqual(player.mode, "faint")
        self.assertAlmostEqual(player.score, 70, places=3)
        self.assertAlmostEqual(player.x, 196, places=3)

    def test_climb_door_and_avanto_connect(self):
        room = Room(random.Random(5))
        room.event_in = 10 ** 9
        player = Player(0, ScriptPad("m"))
        player.reset_round("floor", PLACES["floor"]["climb_x"])
        climbed = False
        for _ in range(FPS * 3):
            step_player(player, 0, -1, False, room)
            if player.place == "high":
                climbed = True
                break
        self.assertTrue(climbed)
        self.assertGreaterEqual(player.x, PLACES["high"]["x0"])
        self.assertLessEqual(player.x, PLACES["high"]["x1"])

        player.reset_round("floor", PLACES["floor"]["x0"])
        exited = False
        for _ in range(FPS):
            events = step_player(player, -1, 0, False, room)
            if "exit" in events or player.place == "porch":
                exited = True
                break
        self.assertTrue(exited)

        dipped = False
        for _ in range(FPS * 3):
            events = step_player(player, -1, 0, False, room)
            if "avanto" in events:
                dipped = True
                break
        self.assertTrue(dipped)
        self.assertEqual(player.place, "avanto")

    def test_bots_finish_a_round_in_the_window(self):
        game, frames = run_round(4, seed=1)
        self.assertEqual(game.state, "roundend")
        play_frames = frames - 180
        self.assertGreater(play_frames, MIN_FRAMES - 30)
        self.assertLess(play_frames, ROUND_FRAMES + 200)
        scores = [p.round_points for p in game.players]
        self.assertGreater(max(scores), 40)
        self.assertTrue(any(p.place in ("high", "mid", "low", "floor", "porch", "avanto") for p in game.players))
        for player in game.players:
            spec = PLACES[player.place]
            self.assertGreaterEqual(player.x, spec["x0"] - 1)
            self.assertLessEqual(player.x, spec["x1"] + 1)

    def test_two_player_round_also_finishes(self):
        game, frames = run_round(2, seed=2)
        self.assertEqual(game.state, "roundend")
        self.assertGreater(frames, MIN_FRAMES)
        self.assertGreater(max(p.round_points for p in game.players), 30)

    def test_join_needs_two_and_options_starts(self):
        screen = pygame.display.get_surface()
        game = Game(screen)
        pad_a = ScriptPad("a")
        pad_b = ScriptPad("b")
        game.pads[pad_a.id] = pad_a
        game.pads[pad_b.id] = pad_b
        pad_a.desired = {"x": 0, "y": 0, "jump": True, "start": False, "back": False, "alt": False}
        game.update()
        self.assertEqual(len(game.players), 1)
        self.assertEqual(game.state, "lobby")
        pad_a.desired = blank()
        pad_b.desired = {"x": 0, "y": 0, "jump": True, "start": False, "back": False, "alt": False}
        game.update()
        self.assertEqual(len(game.players), 2)
        pad_b.desired = blank()
        game.update()
        pad_a.desired = {"x": 0, "y": 0, "jump": False, "start": True, "back": False, "alt": False}
        game.update()
        self.assertEqual(game.state, "ready")
        self.assertTrue(game.version)

    def setUp(self):
        path = os.environ["SAUNAKISA_SETTINGS"]
        if os.path.exists(path):
            os.remove(path)

    def test_settings_ignore_missing_and_corrupt(self):
        self.assertEqual(sanitize_settings(None)["rounds"], 3)
        bad = sanitize_settings({"cpus": 9, "difficulty": "nope", "sfx_vol": True, "rounds": 5})
        self.assertEqual(bad["cpus"], 0)
        self.assertEqual(bad["difficulty"], "normaali")
        self.assertEqual(bad["rounds"], 5)
        path = "/tmp/saunakisa-corrupt.json"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertEqual(load_settings(path)["heat"], "normaali")
        self.assertEqual(load_settings("/tmp/saunakisa-does-not-exist.json")["round_secs"], 78)
        saved = dict(load_settings())
        saved["difficulty"] = "vaikea"
        self.assertTrue(save_settings(saved, "/tmp/saunakisa-roundtrip.json"))
        self.assertEqual(load_settings("/tmp/saunakisa-roundtrip.json")["difficulty"], "vaikea")

    def test_square_adds_cpu_and_options_starts(self):
        screen = pygame.display.get_surface()
        game = Game(screen)
        pad = ScriptPad("solo")
        game.pads[pad.id] = pad
        pad.desired = blank()
        pad.desired["jump"] = True
        game.update()
        self.assertEqual(len(game.players), 1)
        self.assertFalse(game.players[0].cpu)
        pad.desired = blank()
        pad.desired["cpu"] = True
        game.update()
        self.assertEqual(len(game.players), 2)
        self.assertEqual(sum(p.cpu for p in game.players), 1)
        pad.desired = blank()
        game.update()
        pad.desired = blank()
        pad.desired["start"] = True
        game.update()
        self.assertEqual(game.state, "ready")

    def test_joined_pads_can_fill_every_cpu_slot(self):
        for n in (1, 2, 3):
            game = self._fresh()
            game.state = "lobby"
            pads = []
            for i in range(n):
                pad = Pad("js", _QuietStick(), iid=50 + i)
                game.pads[pad.id] = pad
                pads.append(pad)
            # The keyboard hears the same X as a connected pad on this console.
            self._tap(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
            for pad in pads:
                iid = int(pad.id[2:])
                self._tap(game, pygame.event.Event(pygame.JOYBUTTONDOWN, instance_id=iid, button=0))
            humans = [p for p in game.players if not p.cpu]
            self.assertEqual(len(humans), n)
            self.assertTrue(all(p.pad.kind != "kb" for p in humans))
            iid = int(pads[0].id[2:])
            for _ in range(6):
                if sum(p.cpu for p in game.players) == 4 - n:
                    break
                self._tap(game, pygame.event.Event(pygame.JOYBUTTONDOWN, instance_id=iid, button=2))
            self.assertEqual(len(game.players), 4)
            self.assertEqual(sum(p.cpu for p in game.players), 4 - n)
            game.begin_round()
            for _ in range(3):
                game.update()
            self.assertIn(game.state, ("ready", "play"))

    def test_fainted_cpu_moves_in_the_next_rounds(self):
        game = self._fresh()
        game.state = "lobby"
        game.settings["cpus"] = 2
        game.settings["rounds"] = 3
        game.sync_cpus()
        human = ScriptPad("mover")
        game.pads[human.id] = human
        game.add_player(human)
        cpus = [p for p in game.players if p.cpu]
        self.assertEqual(len(cpus), 2)
        for _round in range(3):
            for cpu in cpus:
                cpu.heat = 100
                try_faint(cpu)
                cpu.pad.bot.plan = "cool"
                cpu.pad.bot.lock = 90
            game.begin_round()
            self.assertTrue(all(c.mode == "move" for c in cpus))
            self.assertTrue(all(c.pad.bot.plan == "bench" and c.pad.bot.lock == 0 for c in cpus))
            game.state = "play"
            game.round_left = 240
            starts = [(c.place, c.x) for c in cpus]
            for _ in range(150):
                human.desired = blank()
                game.update()
            for cpu, (place, x) in zip(cpus, starts):
                self.assertEqual(cpu.mode, "move")
                self.assertTrue(cpu.place != place or abs(cpu.x - x) > 8)

    def _fresh(self):
        pygame.event.clear()
        screen = pygame.display.get_surface() or pygame.display.set_mode((320, 180))
        game = Game(screen)
        game.state = "settings"
        game.menu_i = 0
        return game

    def _tap(self, game, event):
        pygame.event.post(event)
        game.update()

    def _key(self, game, key):
        self._tap(game, pygame.event.Event(pygame.KEYDOWN, key=key))
        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))
        game.update()

    def test_cpu_row_arrow_does_not_crash_and_wraps(self):
        game = self._fresh()
        self.assertEqual(game.settings["cpus"], 0)
        self._key(game, pygame.K_RIGHT)
        self.assertEqual(game.state, "settings")
        self.assertEqual(game.settings["cpus"], 1)
        self.assertEqual(sum(p.cpu for p in game.players), 1)
        self._key(game, pygame.K_LEFT)
        self.assertEqual(game.settings["cpus"], 0)
        self._key(game, pygame.K_LEFT)
        self.assertEqual(game.settings["cpus"], 4)
        self._key(game, pygame.K_RIGHT)
        self.assertEqual(game.settings["cpus"], 0)

    def test_every_settings_row_from_the_event_queue(self):
        for n_pads in range(5):
            sources = ("key",) if n_pads == 0 else ("key", "hat", "button")
            for source in sources:
                game = self._fresh()
                pads = []
                for i in range(n_pads):
                    dev = _QuietStick()
                    pad = __import__("saunakisa.input", fromlist=["Pad"]).Pad("js", dev, iid=20 + i)
                    game.pads[pad.id] = pad
                    pads.append(pad)
                self._walk_rows(game, source, pads[0].id if pads else "kb")
                self._start_from_here(game)

    def _walk_rows(self, game, source, pad_id):
        original = dict(game.settings)
        rows = game.setting_rows()
        for index in range(len(rows)):
            game.state = "settings"
            game.menu_i = 0
            for _ in range(index):
                self._menu(game, source, pad_id, "down")
            self.assertEqual(game.menu_i, index)
            key = rows[index][0]
            before = game.settings.get(key)
            self._menu(game, source, pad_id, "right")
            self._menu(game, source, pad_id, "left")
            self._menu(game, source, pad_id, "left")
            self._menu(game, source, pad_id, "right")
            if key == "help":
                self.assertEqual(game.settings.get(key, None), before)
            else:
                self.assertEqual(game.settings[key], original[key])
            self.assertEqual(game.state, "settings")

    def _menu(self, game, source, pad_id, way):
        if source == "key":
            key = {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "down": pygame.K_DOWN, "up": pygame.K_UP}[way]
            self._key(game, key)
            return
        if source == "hat":
            value = {"left": (-1, 0), "right": (1, 0), "down": (0, -1), "up": (0, 1)}[way]
            iid = int(pad_id[2:])
            self._tap(game, pygame.event.Event(pygame.JOYHATMOTION, instance_id=iid, hat=0, value=value))
            return
        button = {
            "left": pygame.CONTROLLER_BUTTON_DPAD_LEFT,
            "right": pygame.CONTROLLER_BUTTON_DPAD_RIGHT,
            "down": pygame.CONTROLLER_BUTTON_DPAD_DOWN,
            "up": pygame.CONTROLLER_BUTTON_DPAD_UP,
        }[way]
        iid = int(pad_id[2:])
        self._tap(game, pygame.event.Event(
            pygame.CONTROLLERBUTTONDOWN, instance_id=iid, button=button,
        ))

    def _start_from_here(self, game):
        game.state = "lobby"
        game.settings["cpus"] = min(3, int(game.settings["cpus"]))
        game.sync_cpus()
        if not any(not p.cpu for p in game.players):
            pad = ScriptPad("starter")
            game.pads[pad.id] = pad
            game.add_player(pad)
        if len(game.players) < 2:
            game.settings["cpus"] = 1
            game.sync_cpus()
        game.begin_round()
        for _ in range(4):
            game.update()
        self.assertIn(game.state, ("ready", "play"))
        for player in game.players:
            self.assertGreaterEqual(player.x, 0)

    def test_crash_log_is_written(self):
        path = write_crash("boom\n")
        self.assertEqual(path, os.environ["SAUNAKISA_CRASH_LOG"])
        with open(path, encoding="utf-8") as fh:
            self.assertIn("boom", fh.read())


class _QuietStick:
    def get_numaxes(self):
        return 2

    def get_axis(self, i):
        return 0.0

    def get_numhats(self):
        return 1

    def get_hat(self, i):
        return (0, 0)

    def get_numbuttons(self):
        return 16

    def get_button(self, i):
        return 0


if __name__ == "__main__":
    unittest.main()
