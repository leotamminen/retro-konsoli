# Couch loop: join, sweat, scoreboard, again.
import random

import pygame

from .actors import (
    Bot, Player, PROFILE_ORDER, separate, step_player, throw_into, try_faint,
)
from .audio import sfx
from .const import (
    COUNTDOWN, H, LAST_BONUS, MIN_FRAMES, PCOLORS, ROUND_FRAMES, ROUNDS, SOLO_HOLD, W,
)
from .draw import draw_frame, make_background
from .font import Font
from .input import Pad, ScriptPad, blank
from .text import tr
from .version import load_version
from .world import Room


SPOTS = (148, 178, 208, 236)


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.canvas = pygame.Surface((W, H))
        self.font = Font()
        self.bg = make_background()
        self.veil = pygame.Surface((W, H), pygame.SRCALPHA)
        self.veil.fill((28, 16, 12, 150))
        self.version = load_version()
        self.pads = {}
        kb = Pad("kb")
        self.pads[kb.id] = kb
        self.players = []
        self.room = None
        self.state = "lobby"
        self.t = 0
        self.round_no = 0
        self.round_left = 0
        self.round_winners = []
        self.ending = 0
        self.go_flash = 0
        self.menu_i = 0
        self.quit_hold = 0
        self.running = True
        self.autoplay = False
        self.seed = 1
        self.rng = random.Random(1)
        self.bits = []
        self.notes = []
        self.stats = {
            "frames": 0, "faints": 0, "loyly": 0, "dips": 0, "pickups": 0,
            "exits": 0, "gusts": 0, "flares": 0, "rounds_ended": 0,
            "early": 0, "wipes": 0,
        }

    def public_stats(self):
        return dict(self.stats)

    def arm_autoplay(self, seed):
        self.autoplay = True
        self.seed = seed
        self.rng = random.Random(seed + 3)
        for i, name in enumerate(PROFILE_ORDER):
            pad = ScriptPad("bot%d" % i)
            pad.auto = True
            pad.join_frame = 8 + i * 5
            pad.bot = Bot(name, random.Random(seed + 17 + i))
            self.pads[pad.id] = pad

    def goto(self, name):
        self.state = name
        self.t = 0

    def add_player(self, pad):
        if len(self.players) >= 4 or any(p.pad is pad for p in self.players):
            return None
        player = Player(len(self.players), pad)
        player.reset_round("floor", SPOTS[player.idx])
        self.players.append(player)
        sfx("join")
        return player

    def reindex(self):
        for i, player in enumerate(self.players):
            player.idx = i

    def owner(self, pad):
        for player in self.players:
            if player.pad is pad:
                return player
        return None

    def handle_device(self, ev):
        if ev.type == pygame.JOYDEVICEADDED:
            try:
                joy = pygame.joystick.Joystick(ev.device_index)
            except Exception:
                return
            iid = joy.get_instance_id()
            pad = None
            try:
                from pygame._sdl2 import controller
                if not controller.get_init():
                    try:
                        controller.init()
                    except Exception:
                        pass
                if controller.is_controller(ev.device_index):
                    try:
                        con = controller.Controller.from_joystick(joy)
                    except Exception:
                        con = controller.Controller(ev.device_index)
                    pad = Pad("gc", con, iid=iid, joy=joy)
            except Exception:
                pad = None
            if pad is None:
                pad = Pad("js", joy, iid=iid, joy=joy)
            self.pads[pad.id] = pad
        elif ev.type == pygame.JOYDEVICEREMOVED:
            self.drop_pad("js%d" % ev.instance_id)

    def drop_pad(self, pid):
        pad = self.pads.pop(pid, None)
        if pad is None:
            return
        for player in self.players:
            if player.pad is pad:
                script = ScriptPad("auto-%d" % player.idx)
                script.auto = True
                script.bot = Bot("tasainen", random.Random(self.seed + 90 + player.idx))
                player.pad = script
                self.pads[script.id] = script

    def grab_pads(self):
        if self.state not in ("play", "ready"):
            return
        for pad in list(self.pads.values()):
            if self.owner(pad) is not None or not pad.pressed("jump"):
                continue
            for player in self.players:
                if getattr(player.pad, "auto", False):
                    player.pad = pad
                    break

    def poll_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self.handle_device(ev)
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.running = False

    def poll_pads(self):
        ks = pygame.key.get_pressed()
        pads = list(self.pads.values())
        for player in self.players:
            if player.pad not in pads:
                pads.append(player.pad)
        seen = set()
        quitting = False
        for pad in pads:
            if id(pad) in seen:
                continue
            seen.add(id(pad))
            pad.poll(ks)
            if pad.held("start") and pad.held("back"):
                quitting = True
        self.quit_hold = self.quit_hold + 1 if quitting else 0

    def drive(self):
        if self.state == "lobby":
            for pad in self.pads.values():
                if not getattr(pad, "auto", False) or self.owner(pad) is not None:
                    continue
                des = blank()
                if self.t == getattr(pad, "join_frame", 8):
                    des["jump"] = True
                pad.desired = des
        for player in self.players:
            bot = getattr(player.pad, "bot", None)
            if bot is None:
                continue
            if not (self.autoplay or getattr(player.pad, "auto", False)):
                continue
            player.pad.desired = self._auto_desire(player, bot)

    def _auto_desire(self, player, bot):
        if self.state == "lobby":
            des = blank()
            if self.t == 40 and player.idx == 0 and len(self.players) >= 2:
                des["start"] = True
            return des
        if self.state in ("ready", "play") and self.room is not None:
            return bot.decide(player, self.room, self.players)
        if self.state == "roundend" and self.t == 48 and player.idx == 0:
            des = blank()
            des["jump"] = True
            return des
        if self.state == "results" and self.t == 30 and player.idx == 0:
            des = blank()
            des["jump"] = True
            return des
        return blank()

    def note(self, text, x, y, color):
        self.notes.append([text, x, y, 46, color])
        if len(self.notes) > 8:
            del self.notes[0]

    def _tick_notes(self):
        kept = []
        for item in self.notes:
            item[2] -= 0.22
            item[3] -= 1
            if item[3] > 0:
                kept.append(item)
        self.notes = kept

    def _tick_bits(self):
        kept = []
        for bit in self.bits:
            bit[0] += bit[2]
            bit[1] += bit[3]
            bit[4] -= 1
            if bit[4] > 0:
                kept.append(bit)
        self.bits = kept[-70:]

    def puff(self, x, y, color, n=4, speed=0.4):
        for i in range(n):
            if len(self.bits) > 70:
                self.bits.pop(0)
            self.bits.append([
                x + random.uniform(-3, 3), y,
                random.uniform(-speed, speed), random.uniform(-0.7, -0.15),
                random.randint(12, 26), color,
            ])

    def update(self):
        self.poll_events()
        self.drive()
        self.poll_pads()
        self.t += 1
        self.stats["frames"] += 1
        self._tick_notes()
        self._tick_bits()
        if self.quit_hold >= 60:
            self.running = False
            return
        self.grab_pads()
        getattr(self, "up_" + self.state)()

    def up_lobby(self):
        for pad in list(self.pads.values()):
            if pad.pressed("alt"):
                self.goto("legend")
                return
            owned = self.owner(pad)
            if owned is not None and pad.pressed("back"):
                self.players.remove(owned)
                self.reindex()
                continue
            if owned is None and pad.pressed("jump"):
                self.add_player(pad)
        if len(self.players) >= 2 and any(
            self.owner(pad) is not None and pad.pressed("start") for pad in self.pads.values()
        ):
            self.begin_round()

    def up_legend(self):
        for pad in self.pads.values():
            if pad.pressed("jump") or pad.pressed("back") or pad.pressed("alt") or pad.pressed("start"):
                self.goto("lobby")
                return

    def up_ready(self):
        self._ambience()
        if self.t >= COUNTDOWN:
            sfx("go")
            self.go_flash = 28
            self.goto("play")
            self.up_play()

    def up_play(self):
        if self.go_flash:
            self.go_flash -= 1
        if self._wants_pause():
            self.menu_i = 0
            self.goto("paused")
            return
        self._simulate()
        alive = [p for p in self.players if p.mode != "faint"]
        if self.ending:
            self.ending -= 1
            if self.ending <= 0 or not alive:
                self._finish_round()
            return
        if not alive:
            self.stats["wipes"] += 1
            self._finish_round()
            return
        elapsed = ROUND_FRAMES - max(0, self.round_left)
        if len(alive) == 1 and len(self.players) >= 2 and elapsed >= MIN_FRAMES:
            alive[0].score += LAST_BONUS
            alive[0].got_bonus = True
            self.stats["early"] += 1
            self.note(tr("last"), W / 2, 36, (255, 220, 140))
            sfx("win")
            self.ending = SOLO_HOLD
            return
        if self.round_left <= 0:
            self._finish_round()

    def up_paused(self):
        for player in self.players:
            pad = player.pad
            if pad.cur["y"] < -0.5 and pad.prev["y"] >= -0.5:
                self.menu_i = (self.menu_i - 1) % 3
            elif pad.cur["y"] > 0.5 and pad.prev["y"] >= -0.5 and pad.prev["y"] <= 0.5:
                self.menu_i = (self.menu_i + 1) % 3
            if pad.pressed("back"):
                self.goto("play")
                return
            if pad.pressed("jump") or pad.pressed("start"):
                self._pause_pick()
                return

    def up_roundend(self):
        if self.t > 24 and any(p.pad.pressed("jump") or p.pad.pressed("start") for p in self.players):
            if self.round_no >= ROUNDS:
                self.goto("results")
            else:
                self.begin_round()

    def up_results(self):
        if any(p.pad.pressed("back") for p in self.players):
            self._to_lobby()
            return
        if self.t > 16 and any(p.pad.pressed("jump") or p.pad.pressed("start") for p in self.players):
            self._rematch()

    def _wants_pause(self):
        if self.autoplay or self.ending:
            return False
        for player in self.players:
            pad = player.pad
            if pad.pressed("start") and not pad.held("back"):
                return True
        return False

    def _pause_pick(self):
        if self.menu_i == 0:
            self.goto("play")
        elif self.menu_i == 1:
            self._to_lobby()
        else:
            self.running = False

    def _to_lobby(self):
        for player in self.players:
            player.bank = 0
            player.wins = 0
            player.faints = 0
            player.score = 0
        self.round_no = 0
        self.room = None
        self.notes = []
        self.goto("lobby")

    def _rematch(self):
        for player in self.players:
            player.bank = 0
            player.wins = 0
            player.faints = 0
        self.round_no = 0
        self.begin_round()

    def begin_round(self):
        self.round_no += 1
        self.room = Room(self.rng)
        self.round_left = ROUND_FRAMES
        self.ending = 0
        self.go_flash = 0
        self.round_winners = []
        self.bits = []
        self.notes = []
        for i, player in enumerate(self.players):
            player.reset_round("floor", SPOTS[i])
        self.goto("ready")

    def _simulate(self):
        self.round_left -= 1
        self.room.tick(self.players)
        self.stats["gusts"] = self.room.gusts
        self.stats["flares"] = self.room.flares
        thrown = []
        for player in self.players:
            pad = player.pad
            events = step_player(
                player, pad.cur["x"], pad.cur["y"], pad.pressed("jump"), self.room,
            )
            if "exit" in events:
                self.room.draft()
                self.stats["exits"] += 1
            if "avanto" in events:
                self.stats["dips"] += 1
                sfx("dip")
                self.note(tr("avanto"), player.x, player.y - 26, (170, 220, 255))
                self.puff(player.x, player.y - 8, (180, 220, 240), 5, 0.5)
            if "loyly" in events:
                thrown.append(player)
            if "olut" in events or "pyyhe" in events:
                kind = "olut" if "olut" in events else "pyyhe"
                self.stats["pickups"] += 1
                sfx("drink")
                self.note(tr(kind), player.x, player.y - 22, (255, 230, 160))
            if "faint" in events:
                self._on_faint(player)
        for player in thrown:
            throw_into(player, self.players, self.room)
            self.stats["loyly"] += 1
            sfx("loyly")
            self.note(tr("loyly"), 250, 78, (255, 244, 220))
            self.puff(296, 120, (230, 236, 240), 8, 0.55)
        for player in self.players:
            if try_faint(player):
                self._on_faint(player)
        separate(self.players)
        self._ambience()

    def _ambience(self):
        if self.room is None:
            return
        rate = 2 if self.room.heat > 50 or self.room.loyly_t else 4
        if self.t % rate == 0:
            self.puff(296, 118, (236, 240, 244), 2, 0.35)
        for player in self.players:
            if player.mode == "faint" or player.heat < 58:
                continue
            if self.t % 14 == player.idx:
                self.puff(player.x, player.y - 18, (200, 230, 255), 1, 0.2)

    def _on_faint(self, player):
        self.stats["faints"] += 1
        sfx("faint")
        self.note(tr("fainted"), player.x, player.y - 18, PCOLORS[player.idx][0])
        self.puff(player.x, player.y - 10, (255, 220, 80), 4, 0.35)

    def _finish_round(self):
        for player in self.players:
            player.round_points = int(player.score + 0.5)
            player.bank += player.round_points
            if player.mode == "faint":
                player.faints += 1
        self.notes = []
        best = max(player.round_points for player in self.players) if self.players else 0
        self.round_winners = [p for p in self.players if p.round_points == best and best > 0]
        for player in self.round_winners:
            player.wins += 1
        self.stats["rounds_ended"] += 1
        sfx("win")
        self.ending = 0
        self.goto("roundend")

    def draw(self):
        draw_frame(self)
        self.screen.blit(self.canvas, (0, 0))
