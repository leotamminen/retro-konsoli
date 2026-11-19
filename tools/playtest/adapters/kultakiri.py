"""Drive Kultakiri through ScriptPad, the same dict the real pad poll fills.

Bots only write that dict. Joining, physics, ghosts, pickups and the round
timer all stay inside the game.
"""
import math
import os
import random
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_GAME = _REPO / "Kultakiri"
if str(_GAME) not in sys.path:
    sys.path.insert(0, str(_GAME))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("KULTAKIRI_NO_MUSIC", "1")
os.environ.setdefault("KULTAKIRI_NO_SFX", "1")
os.environ.setdefault("KULTAKIRI_WINDOWED", "1")

import pygame

from highlights import Event
from kultakiri.const import FALL_Y, FPS, H, PNAMES, W
from kultakiri.game import Game
from kultakiri.input import ScriptPad, blank
from kultakiri.physics import Pilot, ghost_steer


class RunnerBot:
    """Hold right, jump gaps and brambles, sometimes miss or steer the wrong way."""

    def __init__(self, skill, rng):
        self.rng = rng
        self.pilot = Pilot(skill, rng)
        self.command_x = 1.0

    def decide(self, player, solids, hazards):
        des = blank()
        if player.state == "ghost":
            ix, iy = ghost_steer(player.body, solids)
            if self.rng.random() < 0.1:
                iy = -iy
            des["x"] = ix
            des["y"] = iy
            self.command_x = ix
            return des
        if player.state != "run":
            self.command_x = 0.0
            return des
        _ix, held, pressed = self.pilot.decide(
            player.body, solids, hazards,
            glide=player.glide_t > 0,
            air_jumps=player.body.air_jumps,
        )
        ix = -1.0 if self.rng.random() < 0.025 else 1.0
        des["x"] = ix
        des["jump"] = bool(held or pressed)
        self.command_x = ix
        return des


class KultakiriAdapter:
    name = "kultakiri"
    width = W
    height = H
    sim_fps = FPS
    video_fps = 30

    def __init__(self):
        self.game = None
        self.bots = []
        self.rounds = 1
        self.seed = 1
        self._prev = None
        self._stats = None
        self._stuck_mark = {}
        self._quiet = {}
        self._round_ends = 0
        self._scoreboard_frames = 0
        self._want_next = False
        self._prev_state = "ready"
        self.right_hits = 0
        self.right_seen = 0
        self.moved_before_go = 0
        self._ready_xy = None
        self._seen_chunks = set()
        self._speed_until = {}
        self.round_log = []
        self._play_t = 0.0

    def start(self, players, seed, rounds, cpus=0, difficulty="normaali"):
        total = players + cpus
        if players < 1 or total < 2 or total > 4:
            raise SystemExit("kultakiri needs 2 to 4 participants")
        self.rounds = rounds
        self.seed = seed
        self.round_log = []
        self._play_t = 0.0
        self._speed_until = {}
        pygame.init()
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("KULTAKIRI playtest")
        game = Game(screen)
        game.seed = seed
        game.rng = random.Random(seed + 3)
        # A settings file on disk must not change the race we are measuring.
        for player in list(game.players):
            game.players.remove(player)
            if getattr(player, "is_cpu", False):
                game.pads.pop(player.pad.id, None)
        game.settings["cpu_diff"] = difficulty
        game.settings["rounds"] = max(rounds, game.settings["rounds"])
        game.match_rounds = game.settings["rounds"]
        game.settings["scroll0"] = game.settings.get("scroll0") or game.scroll
        rng = random.Random(seed)
        skills = (0.94, 0.86, 0.64, 0.78)[:players]
        if players == 2 and cpus == 0:
            skills = (0.9, 0.66)
        elif players == 1:
            skills = (0.88,)
        self.bots = []
        for i, skill in enumerate(skills):
            pad = ScriptPad("bot%d" % i)
            pad.auto = False
            game.pads[pad.id] = pad
            game.add_player(pad)
            self.bots.append(RunnerBot(skill, random.Random(rng.randrange(1, 10 ** 9))))
        for _ in range(cpus):
            game.add_cpu(save=False)
        game.begin_round()
        self.game = game
        self._prev = None
        self._stats = {k: v for k, v in game.stats.items() if not isinstance(v, list)}
        self._round_ends = 0
        self._scoreboard_frames = 0
        self._prev_state = game.state
        self._quiet = {}
        self.right_hits = 0
        self.right_seen = 0
        self.moved_before_go = 0
        self._ready_xy = None
        self._seen_chunks = set()

    def write_inputs(self):
        game = self.game
        if game.state == "roundend":
            for player in game.players:
                player.pad.desired = blank()
            if self._want_next and game.t == 40 and game.players:
                des = blank()
                des["jump"] = True
                game.players[0].pad.desired = des
            return
        for bot, player in zip(self.bots, game.players):
            solids = game._solids(player.body.x - 80, player.body.x + 150)
            hazards = game._hazards(player.body.x - 20, player.body.x + 100)
            player.pad.desired = bot.decide(player, solids, hazards)

    def tick(self):
        self.game.update()

    def draw(self):
        self.game.draw()

    def surface(self):
        return self.game.canvas

    def collect(self, frame):
        game = self.game
        t = frame / float(self.sim_fps)
        snaps = []
        for i, player in enumerate(game.players):
            bot = self.bots[i] if i < len(self.bots) else None
            body = player.body
            snaps.append({
                "idx": player.idx,
                "name": PNAMES[player.idx],
                "state": player.state,
                "x": body.x, "y": body.y, "vx": body.vx, "vy": body.vy,
                "command_x": bot.command_x if bot is not None else player.pad.cur.get("x", 0),
                "double": player.double_t, "speed": player.speed_t,
                "shield": player.shield_t, "magnet": player.magnet_t,
                "slow": player.slow_t, "glide": player.glide_t,
                "cpu": bool(getattr(player, "is_cpu", False)),
            })
        events = []
        if self._prev is not None:
            events.extend(self._diff(frame, t, snaps))
        self._prev = snaps
        events.extend(self._stat_events(frame, t))
        events.extend(self._race_checks(frame, t))
        events.extend(self._course_sights(frame, t))
        if game.state == "roundend":
            self._scoreboard_frames += 1
        else:
            self._scoreboard_frames = 0
        return events

    def finished(self):
        return self._round_ends >= self.rounds and self._scoreboard_frames >= self.sim_fps * 4

    def close(self):
        pygame.quit()

    def summary(self):
        return {
            "right_edge_without_speed": self.right_hits,
            "right_edge_samples": self.right_seen,
            "moved_before_go": self.moved_before_go,
            "rounds": list(self.round_log),
        }

    def _race_checks(self, frame, t):
        game = self.game
        out = []
        if game.state == "ready":
            now = [(round(p.body.x, 2), round(p.body.y, 2), round(p.body.vx, 2)) for p in game.players]
            if self._ready_xy is None:
                self._ready_xy = now
            elif now != self._ready_xy:
                self.moved_before_go += 1
                if self.moved_before_go == 1:
                    out.append(Event(t, frame, "anomaly", "A player moved during the countdown, before NYT", 100, True))
        if game.state == "play":
            limit = W - 12 - 8
            for player in game.players:
                if player.speed_t > 0:
                    # A speed boost may touch the edge. The rule is about a normal run.
                    self._speed_until[player.idx] = frame + self.sim_fps * 4
                if player.state != "run" or player.speed_t > 0:
                    continue
                if frame < self._speed_until.get(player.idx, -1):
                    continue
                self.right_seen += 1
                if player.body.x - game.camera >= limit:
                    self.right_hits += 1
                    if self.right_hits == 1:
                        out.append(Event(
                            t, frame, "anomaly",
                            "%s reached the right edge without the speed powerup" % PNAMES[player.idx],
                            100, True,
                        ))
        return out

    def _diff(self, frame, t, snaps):
        out = []
        game = self.game
        by_idx = {s["idx"]: s for s in self._prev}
        for snap in snaps:
            old = by_idx.get(snap["idx"])
            if old is None:
                continue
            name = snap["name"]
            if old["state"] == "run" and snap["state"] == "ghost":
                cause = "fell off" if old["y"] > FALL_Y - 40 else "was left behind the screen"
                out.append(Event(t, frame, "fall", "%s %s" % (name, cause), 72))
                out.append(Event(t, frame, "ghost", "%s is a ghost and can still collect coins" % name, 58))
            elif old["state"] == "run" and snap["state"] == "out":
                cause = "fell off" if old["y"] > FALL_Y - 40 else "was left behind the screen"
                out.append(Event(t, frame, "out", "%s %s and is out (no rescue left)" % (name, cause), 76))
            elif old["state"] == "ghost" and snap["state"] == "run":
                out.append(Event(t, frame, "return", "%s landed and is back in the round" % name, 84))
            elif old["state"] == "ghost" and snap["state"] == "out":
                out.append(Event(t, frame, "out", "%s faded out before finding a ledge" % name, 66))
            for key, label in (
                ("double", "double jump"), ("speed", "speed"), ("shield", "shield"),
                ("magnet", "magnet"), ("glide", "glide"),
            ):
                if old[key] <= 0 and snap[key] > 0:
                    out.append(Event(t, frame, "pickup", "%s picked up %s" % (name, label), 52))
            if old["slow"] <= 0 and snap["slow"] > 0:
                out.append(Event(t, frame, "effect", "%s is caught in a slow bubble" % name, 63))
            if snap["state"] in ("run", "ghost"):
                out.extend(self._bounds(frame, t, snap))
                out.extend(self._stuck(frame, t, snap, game.state))
        if self._prev_state == "ready" and game.state == "play":
            self._play_t = t
        if self._prev_state != "roundend" and game.state == "roundend":
            winners = list(game.round_winners)
            names = [PNAMES[p.idx] for p in winners] or ["nobody"]
            length = t - getattr(self, "_play_t", t)
            cpu_win = any(getattr(p, "is_cpu", False) for p in winners)
            self.round_log.append({
                "seconds": round(length, 2),
                "names": names,
                "cpu_win": cpu_win,
                "human_win": bool(winners) and not cpu_win,
            })
            out.append(Event(
                t, frame, "round_end",
                "Round %d ended after %.1fs. Ahead: %s" % (game.round_no, length, ", ".join(names)),
                70,
            ))
            self._round_ends += 1
            self._want_next = self._round_ends < self.rounds
        self._prev_state = game.state
        return out

    def _course_sights(self, frame, t):
        """Note the first time a hand-built set piece scrolls into view."""
        game = self.game
        if game.world is None or game.state != "play":
            return []
        show = {
            "katto": "Spike ceiling, short hop",
            "piikit": "Spikes on the floor and on a step",
            "murea": "Crumbling bridge",
            "liuku": "Moving platform",
            "haara": "High road with a powerup, low road with a bramble",
            "raput": "Staircase up and down",
            "portaat": "Steps up to a higher route",
            "nousu": "Climb to a powerup",
        }
        out = []
        cam = game.camera
        for origin, chunk in game.world.placed:
            if chunk.name not in show or chunk.name in self._seen_chunks:
                continue
            if origin < cam + W - 20 and origin + chunk.w > cam + 40:
                self._seen_chunks.add(chunk.name)
                out.append(Event(t, frame, "course", "%s: %s" % (chunk.name, show[chunk.name]), 78))
        return out

    def _bounds(self, frame, t, snap):
        out = []
        for axis in ("x", "y", "vx", "vy"):
            value = snap[axis]
            if not math.isfinite(value):
                out.append(Event(
                    t, frame, "anomaly",
                    "%s has a non-finite %s (%s)" % (snap["name"], axis, value),
                    100, True,
                ))
        if snap["state"] == "run" and snap["y"] > FALL_Y + 80:
            out.append(Event(
                t, frame, "anomaly",
                "%s is still running at y=%.0f, past the fall line" % (snap["name"], snap["y"]),
                100, True,
            ))
        cam = self.game.camera
        if snap["state"] == "run" and snap["x"] < cam - 40:
            out.append(Event(
                t, frame, "anomaly",
                "%s is running at x=%.0f, behind the screen (camera %.0f)" % (snap["name"], snap["x"], cam),
                100, True,
            ))
        return out

    def _stuck(self, frame, t, snap, state):
        if state != "play" or snap["state"] not in ("run", "ghost") or snap["command_x"] <= 0.5:
            self._stuck_mark.pop(snap["idx"], None)
            return []
        mark = self._stuck_mark.get(snap["idx"])
        if mark is None or snap["x"] > mark[1] + 1.5:
            self._stuck_mark[snap["idx"]] = (frame, snap["x"], False)
            return []
        start_frame, start_x, reported = mark
        if reported or frame - start_frame < self.sim_fps * 3:
            return []
        self._stuck_mark[snap["idx"]] = (start_frame, start_x, True)
        return [Event(
            t, frame, "anomaly",
            "%s held right for 3s but barely moved (x %.0f -> %.0f)" % (snap["name"], start_x, snap["x"]),
            100, True,
        )]

    def _stat_events(self, frame, t):
        stats = self.game.stats
        prev = self._stats or {}
        out = []
        if stats.get("double_air", 0) > prev.get("double_air", 0):
            out.append(Event(t, frame, "effect", "A double jump actually fired", 64))
        if stats.get("shield_block", 0) > prev.get("shield_block", 0):
            out.append(Event(t, frame, "effect", "A shield soaked a bramble hit", 67))
        if stats.get("bumps", 0) > prev.get("bumps", 0):
            n = stats["bumps"] - prev["bumps"]
            out.append(Event(t, frame, "bump", "Players bumped (%d)" % n, 28))
        for key, label in (
            ("speed_fast", "Speed boost is moving someone faster"),
            ("glide_frames", "Glide is holding a fall"),
            ("magnet_pulls", "Magnet is pulling coins"),
        ):
            grew = stats.get(key, 0) > prev.get(key, 0)
            if grew and self._quiet.get(key, 999) >= self.sim_fps:
                out.append(Event(t, frame, "effect", label, 48))
            self._quiet[key] = 0 if grew else self._quiet.get(key, 0) + 1
        self._stats = {k: v for k, v in stats.items() if not isinstance(v, (list, set, dict))}
        return out
