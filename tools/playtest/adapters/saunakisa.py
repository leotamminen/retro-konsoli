"""Drive Saunakisa through ScriptPad, the same dict the real pad poll fills.

Bots only write that dict. Heat, löyly, the avanto and the round timer stay
inside the game. Greed is different for each seat.
"""
import math
import os
import random
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_GAME = _REPO / "Saunakisa"
if str(_GAME) not in sys.path:
    sys.path.insert(0, str(_GAME))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SAUNAKISA_NO_MUSIC", "1")
os.environ.setdefault("SAUNAKISA_NO_SFX", "1")
os.environ.setdefault("SAUNAKISA_WINDOWED", "1")
os.environ.setdefault("SAUNAKISA_SETTINGS", "/tmp/saunakisa-playtest-settings.json")

import pygame

from highlights import Event
from saunakisa.actors import Bot
from saunakisa.const import FPS, H, PNAMES, W
from saunakisa.game import Game
from saunakisa.input import ScriptPad, blank


class SaunakisaAdapter:
    name = "saunakisa"
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
        self._round_ends = 0
        self._scoreboard_frames = 0
        self._want_next = False
        self._prev_state = "ready"
        self._play_started = None
        self._round_seconds = []
        self._moved_ready = 0
        self._ready_xy = None
        self.difficulty = "vaikea"
        self.human = None

    def start(self, players, seed, rounds):
        if players < 2 or players > 4:
            raise SystemExit("saunakisa needs 2 to 4 players")
        self.rounds = rounds
        self.seed = seed
        diff = self.difficulty or "vaikea"
        pygame.init()
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("SAUNAKISA playtest")
        game = _seat_match(screen, players, seed, rounds, diff)
        game.begin_round()
        self.game = game
        self.human = game.players[0].pad.bot
        self.bots = [p.pad.bot for p in game.players]
        self._profiles = ["ihminen"] + [diff] * (players - 1)
        self._prev = None
        self._stats = dict(game.stats)
        self._round_ends = 0
        self._scoreboard_frames = 0
        self._prev_state = game.state
        self._play_started = None
        self._round_seconds = []
        self._moved_ready = 0
        self._ready_xy = None
        self._stuck_mark = {}

    def write_inputs(self):
        game = self.game
        if game.state == "roundend":
            for player in game.players:
                player.pad.desired = blank()
            if self._want_next and game.t == 48 and game.players:
                des = blank()
                des["jump"] = True
                game.players[0].pad.desired = des
            return
        if game.room is None:
            return
        human = game.players[0]
        human.pad.desired = human.pad.bot.decide(human, game.room, game.players)

    def tick(self):
        self.game.update()

    def draw(self):
        self.game.draw()

    def surface(self):
        return self.game.canvas

    def collect(self, frame):
        game = self.game
        t = frame / float(self.sim_fps)
        self.bots = [p.pad.bot for p in game.players]
        snaps = []
        for player, bot in zip(game.players, self.bots):
            snaps.append({
                "idx": player.idx,
                "name": PNAMES[player.idx],
                "mode": player.mode,
                "place": player.place,
                "x": player.x,
                "y": player.y,
                "heat": player.heat,
                "score": player.score,
                "command": bot.command,
            })
        events = []
        if self._prev is not None:
            events.extend(self._diff(frame, t, snaps))
        self._prev = snaps
        events.extend(self._stat_events(frame, t))
        events.extend(self._ready_check(frame, t))
        if game.state == "roundend":
            self._scoreboard_frames += 1
        else:
            self._scoreboard_frames = 0
        if game.state == "play" and self._play_started is None:
            self._play_started = frame
        return events

    def finished(self):
        return self._round_ends >= self.rounds and self._scoreboard_frames >= self.sim_fps * 4

    def close(self):
        pygame.quit()

    def summary(self):
        game = self.game
        scores = ", ".join(
            "%s %d" % (PNAMES[p.idx], p.round_points) for p in game.players
        )
        return {
            "profiles": " ".join(getattr(self, "_profiles", [])),
            "round_seconds": ", ".join("%.1f" % s for s in self._round_seconds) or "n/a",
            "faints": game.stats.get("faints", 0),
            "loyly": game.stats.get("loyly", 0),
            "dips": game.stats.get("dips", 0),
            "pickups": game.stats.get("pickups", 0),
            "early_end": game.stats.get("early", 0),
            "wipes": game.stats.get("wipes", 0),
            "scores": scores,
            "moved_during_countdown": self._moved_ready,
        }

    def _ready_check(self, frame, t):
        game = self.game
        if game.state != "ready":
            self._ready_xy = None
            return []
        now = [(p.place, round(p.x, 2), round(p.heat, 2)) for p in game.players]
        if self._ready_xy is None:
            self._ready_xy = now
            return []
        if now != self._ready_xy:
            self._moved_ready += 1
            self._ready_xy = now
            if self._moved_ready == 1:
                return [Event(t, frame, "anomaly", "A player moved during the countdown", 100, True)]
        return []

    def _diff(self, frame, t, snaps):
        out = []
        game = self.game
        by_idx = {s["idx"]: s for s in self._prev}
        for snap in snaps:
            old = by_idx.get(snap["idx"])
            if old is None:
                continue
            name = snap["name"]
            if old["mode"] != "faint" and snap["mode"] == "faint":
                out.append(Event(
                    t, frame, "faint",
                    "%s fainted on the %s bench area at %.0f heat" % (name, old["place"], old["heat"]),
                    84,
                ))
            elif old["place"] != "avanto" and snap["place"] == "avanto":
                out.append(Event(t, frame, "avanto", "%s stepped into the avanto" % name, 68))
            elif old["place"] in ("floor", "low", "mid", "high") and snap["place"] == "porch":
                out.append(Event(t, frame, "effect", "%s stepped out to the porch" % name, 46))
            out.extend(self._bounds(frame, t, snap))
            out.extend(self._stuck(frame, t, snap, game.state))
        if self._prev_state != "roundend" and game.state == "roundend":
            winners = [PNAMES[p.idx] for p in game.round_winners] or ["nobody"]
            seconds = 0.0
            if self._play_started is not None:
                seconds = (frame - self._play_started) / float(self.sim_fps)
                self._round_seconds.append(seconds)
            self._play_started = None
            note = "Round %d ended after %.1fs of play. Ahead: %s" % (game.round_no, seconds, ", ".join(winners))
            anomaly = seconds < 12 or seconds > 95
            if anomaly and seconds < 12:
                note += " (ended in a few seconds)"
            if anomaly and seconds > 95:
                note += " (the round dragged)"
            out.append(Event(t, frame, "round_end", note, 76, anomaly))
            self._round_ends += 1
            self._want_next = self._round_ends < self.rounds
        self._prev_state = game.state
        return out

    def _bounds(self, frame, t, snap):
        out = []
        for axis in ("x", "y", "heat", "score"):
            value = snap[axis]
            if not math.isfinite(value):
                out.append(Event(
                    t, frame, "anomaly",
                    "%s has a non-finite %s" % (snap["name"], axis),
                    100, True,
                ))
        return out

    def _stuck(self, frame, t, snap, state):
        if state != "play" or snap["mode"] == "faint" or snap["command"] != "move":
            self._stuck_mark.pop(snap["idx"], None)
            return []
        mark = self._stuck_mark.get(snap["idx"])
        key = (snap["place"], round(snap["x"], 1))
        if mark is None or key != mark[1]:
            self._stuck_mark[snap["idx"]] = (frame, key, False)
            return []
        start, _key, reported = mark
        if reported or frame - start < self.sim_fps * 3:
            return []
        self._stuck_mark[snap["idx"]] = (start, key, True)
        return [Event(
            t, frame, "anomaly",
            "%s tried to move for 3s but stayed at %s x=%.0f" % (snap["name"], snap["place"], snap["x"]),
            100, True,
        )]

    def _stat_events(self, frame, t):
        stats = self.game.stats
        prev = self._stats or {}
        out = []
        if stats.get("loyly", 0) > prev.get("loyly", 0):
            n = stats["loyly"] - prev["loyly"]
            out.append(Event(t, frame, "loyly", "Löyly thrown (%d)" % n, 70))
        if stats.get("pickups", 0) > prev.get("pickups", 0):
            out.append(Event(t, frame, "pickup", "Someone grabbed a cooling pickup", 54))
        if stats.get("gusts", 0) > prev.get("gusts", 0):
            out.append(Event(t, frame, "effect", "A cool gust came through the door", 42))
        if stats.get("flares", 0) > prev.get("flares", 0):
            out.append(Event(t, frame, "effect", "The kiuas flared", 44))
        self._stats = dict(stats)
        return out

    def balance(self, matches, players, rounds, seed):
        report = balance_matches(self.difficulty or "vaikea", matches, rounds, seed, players)
        print(report)
        return report


def _seat_match(screen, players, seed, rounds, difficulty):
    """One human-like bot in seat 0, the rest CPU at the given difficulty."""
    game = Game(screen)
    game.seed = seed
    game.rng = random.Random(seed + 3)
    game.settings["cpus"] = players - 1
    game.settings["difficulty"] = difficulty
    game.settings["rounds"] = rounds
    game.settings["round_secs"] = 78
    game.settings["heat"] = "normaali"
    game.settings["pickups"] = "normaali"
    game.sync_cpus()
    human = ScriptPad("human-%d" % seed)
    human.bot = Bot("ihminen", random.Random(seed + 17))
    game.pads[human.id] = human
    game.add_player(human)
    if len(game.players) != players:
        raise SystemExit("seated %d, wanted %d" % (len(game.players), players))
    if game.players[0].cpu:
        raise SystemExit("seat 0 should be the human-like bot")
    return game


def balance_matches(difficulty, matches, rounds, seed, players=4):
    """Headless matches. Returns a short text table of wins, spreads and lengths."""
    os.environ["SAUNAKISA_SETTINGS"] = "/tmp/saunakisa-balance-%s.json" % difficulty
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    rng = random.Random(seed)
    human_wins = 0
    cpu_wins = 0
    ties = 0
    spreads = []
    lengths = []
    human_scores = []
    cpu_best = []
    for _match in range(matches):
        match_seed = rng.randrange(1, 10 ** 9)
        game = _seat_match(screen, players, match_seed, rounds, difficulty)
        game.begin_round()
        guard = 0
        limit = FPS * (rounds * 110 + 20)
        seen_round = 0
        while game.state != "results" and guard < limit:
            human = game.players[0]
            if game.state in ("ready", "play") and game.room is not None:
                human.pad.desired = human.pad.bot.decide(human, game.room, game.players)
            elif game.state == "roundend":
                if game.t == 2 and game.round_no != seen_round:
                    seen_round = game.round_no
                    lengths.append((game.round_total - max(0, game.round_left)) / float(FPS))
                des = blank()
                if game.t == 30:
                    des["jump"] = True
                human.pad.desired = des
            else:
                human.pad.desired = blank()
            game.update()
            guard += 1
        banks = [p.bank for p in game.players]
        best = max(banks) if banks else 0
        leaders = [i for i, value in enumerate(banks) if value == best]
        if len(leaders) != 1:
            ties += 1
        elif leaders[0] == 0:
            human_wins += 1
        else:
            cpu_wins += 1
        ordered = sorted(banks, reverse=True)
        spreads.append(ordered[0] - ordered[1] if len(ordered) > 1 else 0)
        human_scores.append(banks[0])
        cpu_best.append(max(banks[1:]) if len(banks) > 1 else 0)
    mean_len = sum(lengths) / float(len(lengths)) if lengths else 0
    mean_spread = sum(spreads) / float(len(spreads)) if spreads else 0
    lines = [
        "difficulty %s  matches %d  rounds %d  players %d" % (difficulty, matches, rounds, players),
        "human wins %d  cpu wins %d  ties %d" % (human_wins, cpu_wins, ties),
        "mean human score %.0f  mean best cpu %.0f  mean winner margin %.0f" % (
            sum(human_scores) / float(matches),
            sum(cpu_best) / float(matches),
            mean_spread,
        ),
        "round length mean %.1fs  min %.1fs  max %.1fs  n %d" % (
            mean_len,
            min(lengths) if lengths else 0,
            max(lengths) if lengths else 0,
            len(lengths),
        ),
    ]
    return "\n".join(lines)
