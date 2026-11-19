# Couch loop: join, run, scoreboard, again.
# A fall or a scroll-off spends the one rescue. You come back as a ghost for a few
# seconds, still able to pick up coins, and you rejoin if you settle on a ledge.
# The second miss is out for the round. That is kinder than watching the rest of
# an autoscroller from the couch, and one rescue keeps "last one running" real.
import random

import pygame

from .actors import (
    Player, award, clamp_runner, collect, fate, pull_coins,
    separate_bumps, start_ghost, tick_ghost, tick_pickups, tick_runner, touch_hazard,
)
from .audio import set_volumes, sfx
from .const import EY, PH, SCROLL0, SCROLL_MAX, W
from .cpu import CpuBrain
from .draw import draw_frame, make_sky
from .font import Font
from .input import Pad, ScriptPad, blank
from .physics import Pilot, ghost_steer
from .settings import DIFFS, FREQS, RAMPS, SCROLL_STEPS, load_settings, save_settings
from .version import load_version
from .world import World, chunk_count


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.canvas = pygame.Surface((W, 180))
        self.font = Font()
        self.sky = make_sky()
        self.version = load_version()
        self.pads = {}
        kb = Pad("kb")
        self.pads[kb.id] = kb
        self.players = []
        self.world = None
        self.state = "lobby"
        self.legend_from = "lobby"
        self.t = 0
        self.camera = 0.0
        self.settings = load_settings()
        set_volumes(self.settings["sfx_vol"], self.settings["music_vol"])
        self.scroll = self.settings["scroll0"]
        self.scroll_acc = RAMPS[self.settings["ramp"]]
        self.scroll_max = max(SCROLL_MAX, self.scroll + 0.04)
        self.match_rounds = self.settings["rounds"]
        self.round_no = 0
        self.settings_from = "lobby"
        self.reopen_screen = False
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
        for _ in range(self.settings["cpu_players"]):
            self.add_cpu(save=False)
        self.stats = {
            "frames": 0, "chunk_fail": 0, "chunk_types": 0, "validated": 0,
            "double_air": 0, "speed_fast": 0, "shield_on": 0, "shield_block": 0,
            "magnet_pulls": 0, "slow_on": 0, "glide_frames": 0, "ghosts": 0,
            "outs": 0, "revives": 0, "bumps": 0, "rounds_ended": 0, "coins": 0,
            "got_powers": [],
        }

    def public_stats(self):
        got = list(self.stats.get("got_powers", []))
        out = {k: v for k, v in self.stats.items() if k != "got_powers"}
        out["got_powers"] = got
        out["power_types"] = len(got)
        return out

    def arm_autoplay(self, seed):
        self.autoplay = True
        self.seed = seed
        self.rng = random.Random(seed + 3)
        for i, skill in enumerate((0.97, 0.9, 0.55, 0.84)):
            pad = ScriptPad("bot%d" % i)
            pad.skill = skill
            pad.auto = True
            pad.join_frame = 6 + i * 4
            self.pads[pad.id] = pad

    def goto(self, name):
        self.state = name
        self.t = 0

    def add_player(self, pad):
        if len(self.players) >= 4 or any(p.pad is pad for p in self.players):
            return None
        player = Player(len(self.players), pad)
        player.pilot = Pilot(getattr(pad, "skill", 1.0), random.Random(self.seed + 40 + len(self.players)))
        player.is_cpu = False
        self.players.append(player)
        return player

    def add_cpu(self, save=True):
        if len(self.players) >= 4:
            return None
        pad = ScriptPad("cpu%d" % (len(self.players) + 1))
        pad.auto = False
        self.pads[pad.id] = pad
        player = self.add_player(pad)
        if player is None:
            return None
        player.is_cpu = True
        player.brain = CpuBrain(self.settings["cpu_diff"], random.Random(self.seed + 90 + player.idx))
        self.settings["cpu_players"] = self._cpu_count()
        if save:
            save_settings(self.settings)
        return player

    def remove_cpu(self, save=True):
        for player in reversed(self.players):
            if not getattr(player, "is_cpu", False):
                continue
            self.players.remove(player)
            self.pads.pop(player.pad.id, None)
            self.reindex()
            self.settings["cpu_players"] = self._cpu_count()
            if save:
                save_settings(self.settings)
            return player
        return None

    def _cpu_count(self):
        return sum(1 for player in self.players if getattr(player, "is_cpu", False))

    def _retune_cpus(self):
        for player in self.players:
            if getattr(player, "is_cpu", False):
                player.brain = CpuBrain(self.settings["cpu_diff"], random.Random(self.seed + 90 + player.idx))

    def reindex(self):
        for i, player in enumerate(self.players):
            player.idx = i

    def owner(self, pad):
        for player in self.players:
            if player.pad is pad:
                return player
        return None

    # ----- devices -----
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
                script.skill = 0.92
                player.pad = script
                player.pilot = Pilot(0.92, random.Random(self.seed + 80 + player.idx))
                player.lost_t = 150
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
                    player.lost_t = 0
                    break

    # ----- frame -----
    def poll_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self.handle_device(ev)
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.running = False
            else:
                self._route_input(ev)

    def _route_input(self, ev):
        if ev.type in (pygame.KEYDOWN, pygame.KEYUP):
            kb = self.pads.get("kb")
            if kb is not None:
                kb.on_key(ev.key, ev.type == pygame.KEYDOWN)
            return
        iid = getattr(ev, "instance_id", None)
        if iid is None:
            return
        pad = self.pads.get("js%d" % int(iid))
        if pad is not None:
            pad.on_joy(ev)

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
        for player in self.players:
            self._drive_player(player)
        if self.state != "lobby" or not self.autoplay:
            return
        for pad in self.pads.values():
            if not pad.script or self.owner(pad) is not None:
                continue
            des = blank()
            if self.t == getattr(pad, "join_frame", 8):
                des["jump"] = True
            pad.desired = des

    def _drive_player(self, player):
        pad = player.pad
        if not (pad.script and (self.autoplay or pad.auto)):
            return
        des = blank()
        if self.state == "lobby":
            if self.t == 30 and player.idx == 0:
                des["start"] = True
        elif self.state in ("ready", "play") and player.state == "ghost":
            solids = self._solids(player.body.x - 90, player.body.x + 160)
            ix, iy = ghost_steer(player.body, solids)
            des["x"], des["y"] = ix, iy
        elif self.state in ("ready", "play") and player.state == "run":
            solids = self._solids(player.body.x - 40, player.body.x + 130)
            hazards = self._hazards(player.body.x - 12, player.body.x + 90)
            _ix, held, pressed = player.pilot.decide(
                player.body, solids, hazards,
                glide=player.glide_t > 0, air_jumps=player.body.air_jumps,
            )
            des["x"] = 1.0
            des["jump"] = bool(held or pressed)
        elif self.state == "roundend" and self.t == 36 and player.idx == 0:
            des["jump"] = True
        elif self.state == "results" and self.t == 24 and player.idx == 0:
            des["jump"] = True
        pad.desired = des

    def _solids(self, x0, x1):
        if self.world is None:
            return []
        return self.world.solids_near(x0, x1)

    def _hazards(self, x0, x1):
        if self.world is None:
            return []
        return self.world.hazards_near(x0, x1)

    def burst(self, x, y, color, n=6):
        for _ in range(n):
            if len(self.bits) > 70:
                self.bits.pop(0)
            self.bits.append([
                x, y, random.uniform(-0.7, 0.7), random.uniform(-1.1, 0.15),
                random.randint(10, 18), color,
            ])

    def _fade_bits(self):
        kept = []
        for bit in self.bits:
            bit[0] += bit[2]
            bit[1] += bit[3]
            bit[3] += 0.05
            bit[4] -= 1
            if bit[4] > 0:
                kept.append(bit)
        self.bits = kept

    def think_cpus(self):
        if self.state not in ("ready", "play") or self.world is None:
            return
        for player in self.players:
            if not getattr(player, "is_cpu", False):
                continue
            solids = self._solids(player.body.x - 50, player.body.x + 170)
            hazards = self._hazards(player.body.x - 16, player.body.x + 120)
            player.pad.desired = player.brain.decide(player, solids, hazards, self.world.powers, self.players)

    def update(self):
        self.poll_events()
        self.drive()
        self.think_cpus()
        self.poll_pads()
        self.t += 1
        self.stats["frames"] += 1
        self._fade_bits()
        if self.quit_hold >= 60:
            self.running = False
            return
        self.grab_pads()
        getattr(self, "up_" + self.state)()

    def up_lobby(self):
        for pad in list(self.pads.values()):
            if getattr(pad, "script", False) and not pad.auto and self.owner(pad) is not None:
                if getattr(self.owner(pad), "is_cpu", False):
                    continue
            if pad.pressed("alt"):
                self.settings_from = "lobby"
                self.menu_i = 0
                self.goto("settings")
                return
            owned = self.owner(pad)
            if owned is not None and not getattr(owned, "is_cpu", False) and pad.pressed("back"):
                self.players.remove(owned)
                self.reindex()
                continue
            if pad.pressed("circle"):
                self.add_cpu()
                continue
            if pad.pressed("menu"):
                self.remove_cpu()
                continue
            if owned is None and pad.pressed("jump") and not pad.pressed("circle"):
                self.add_player(pad)
        if len(self.players) >= 2 and any(
            pad.pressed("start") and not getattr(self.owner(pad), "is_cpu", False)
            for pad in self.pads.values()
        ):
            self.begin_round()

    def up_legend(self):
        for pad in self.pads.values():
            if getattr(self.owner(pad), "is_cpu", False):
                continue
            if pad.pressed("jump") or pad.pressed("back") or pad.pressed("alt") or pad.pressed("start"):
                self.goto(self.legend_from)
                return

    def _settings_rows(self):
        return ("cpu", "diff", "rounds", "scroll", "ramp", "freq", "sfx", "music", "full", "powers", "legend", "back")

    def up_settings(self):
        rows = self._settings_rows()
        n = len(rows)
        # Snapshot: changing the CPU count adds or removes a pad. Doing that
        # while iterating self.pads raises RuntimeError and the game dies.
        for pad in list(self.pads.values()):
            owner = self.owner(pad)
            if owner is not None and getattr(owner, "is_cpu", False):
                continue
            if pad.cur["y"] < -0.5 and pad.prev["y"] >= -0.5:
                self.menu_i = (self.menu_i - 1) % n
            elif pad.cur["y"] > 0.5 and pad.prev["y"] >= -0.5 and pad.prev["y"] <= 0.5:
                self.menu_i = (self.menu_i + 1) % n
            left = pad.cur["x"] < -0.5 and pad.prev["x"] >= -0.5
            right = pad.cur["x"] > 0.5 and pad.prev["x"] <= 0.5
            pick = pad.pressed("jump") or pad.pressed("start")
            if pad.pressed("back") or pad.pressed("alt"):
                self.goto(self.settings_from)
                return
            key = rows[self.menu_i]
            if key == "back" and pick:
                self.goto(self.settings_from)
                return
            if key == "legend" and pick:
                self.legend_from = "settings"
                self.goto("legend")
                return
            if key == "powers" and pick:
                self.menu_i = 0
                self.goto("powers")
                return
            if left or right:
                self._tweak(key, 1 if right else -1)

    def up_powers(self):
        from .const import POWER_KINDS
        n = len(POWER_KINDS) + 1
        for pad in list(self.pads.values()):
            owner = self.owner(pad)
            if owner is not None and getattr(owner, "is_cpu", False):
                continue
            if pad.cur["y"] < -0.5 and pad.prev["y"] >= -0.5:
                self.menu_i = (self.menu_i - 1) % n
            elif pad.cur["y"] > 0.5 and pad.prev["y"] >= -0.5 and pad.prev["y"] <= 0.5:
                self.menu_i = (self.menu_i + 1) % n
            if pad.pressed("back") or (self.menu_i == n - 1 and (pad.pressed("jump") or pad.pressed("start"))):
                self.menu_i = 0
                self.goto("settings")
                return
            if pad.pressed("jump") or pad.pressed("start") or pad.pressed("menu"):
                if self.menu_i < len(POWER_KINDS):
                    kind = POWER_KINDS[self.menu_i]
                    self.settings["powers"][kind] = not self.settings["powers"].get(kind, True)
                    save_settings(self.settings)

    def _tweak(self, key, direction):
        st = self.settings
        if key == "cpu":
            humans = sum(1 for p in self.players if not getattr(p, "is_cpu", False))
            cap = min(3, 4 - humans)
            want = max(0, min(cap, self._cpu_count() + direction))
            guard = 0
            while self._cpu_count() < want and guard < 4:
                guard += 1
                if self.add_cpu(save=False) is None:
                    break
            while self._cpu_count() > want and guard < 8:
                guard += 1
                if self.remove_cpu(save=False) is None:
                    break
            st["cpu_players"] = self._cpu_count()
        elif key == "diff":
            i = DIFFS.index(st["cpu_diff"]) if st["cpu_diff"] in DIFFS else 1
            st["cpu_diff"] = DIFFS[(i + direction) % len(DIFFS)]
            self._retune_cpus()
        elif key == "rounds":
            st["rounds"] = max(1, min(7, st["rounds"] + direction))
            self.match_rounds = st["rounds"]
        elif key == "scroll":
            steps = list(SCROLL_STEPS)
            cur = min(steps, key=lambda v: abs(v - st["scroll0"]))
            i = steps.index(cur)
            st["scroll0"] = steps[max(0, min(len(steps) - 1, i + direction))]
        elif key == "ramp":
            names = list(RAMPS)
            i = names.index(st["ramp"]) if st["ramp"] in names else 1
            st["ramp"] = names[(i + direction) % len(names)]
        elif key == "freq":
            names = list(FREQS)
            i = names.index(st["power_freq"]) if st["power_freq"] in names else 1
            st["power_freq"] = names[(i + direction) % len(names)]
        elif key == "sfx":
            st["sfx_vol"] = max(0, min(10, st["sfx_vol"] + direction))
            set_volumes(st["sfx_vol"], st["music_vol"])
        elif key == "music":
            st["music_vol"] = max(0, min(10, st["music_vol"] + direction))
            set_volumes(st["sfx_vol"], st["music_vol"])
        elif key == "full":
            st["fullscreen"] = not st["fullscreen"]
            self.reopen_screen = True
        else:
            return
        save_settings(st)

    def up_ready(self):
        # Countdown is a hard lock: no input, no scroll, nobody creeps forward.
        if self.t >= 108:
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
        if not self.ending:
            self.scroll = min(self.scroll_max, self.scroll + self.scroll_acc)
            self.camera += self.scroll
            self.world.ensure(self.camera, self.scroll)
            self.world.advance()
            names = {chunk.name for _origin, chunk in self.world.placed}
            if len(names) > self.stats["chunk_types"]:
                self.stats["chunk_types"] = len(names)
        self._move(kill=not self.ending)
        if self.world is not None:
            self.world.arm_crumbles(self.players)
        if self.ending:
            self.ending -= 1
            if self.ending <= 0:
                self._finish_round()
        else:
            self._maybe_end()

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
        if self.t > 20 and any(p.pad.pressed("jump") or p.pad.pressed("start") for p in self.players):
            if self.round_no >= self.match_rounds:
                self.goto("results")
            else:
                self.begin_round()

    def up_results(self):
        if any(p.pad.pressed("back") for p in self.players):
            self._to_lobby()
            return
        if self.t > 12 and any(p.pad.pressed("jump") or p.pad.pressed("start") for p in self.players):
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
            player.total_coins = 0
        self.round_no = 0
        self.world = None
        self.goto("lobby")

    def _rematch(self):
        for player in self.players:
            player.bank = 0
            player.wins = 0
            player.total_coins = 0
        self.round_no = 0
        self.begin_round()

    def begin_round(self):
        self.round_no += 1
        st = self.settings
        self.match_rounds = st["rounds"]
        self.scroll_acc = RAMPS[st["ramp"]]
        freq = FREQS[st["power_freq"]]
        self.world = World(self.rng, powers_on=st["powers"], power_freq=freq)
        self.stats["validated"] = chunk_count()
        self.stats["chunk_fail"] = 0
        self.camera = 0.0
        self.scroll = max(SCROLL0, st["scroll0"])
        self.scroll_max = max(SCROLL_MAX, self.scroll + 0.04)
        self.ending = 0
        self.go_flash = 0
        self.round_winners = []
        for i, player in enumerate(self.players):
            player.reset_round()
            player.body.x = 168 + i * 12
            player.body.y = EY - PH
            player.body.vx = 0.0
            player.body.on_ground = True
            player.max_x = player.body.x
        self.goto("ready")

    def _move(self, kill):
        for player in self.players:
            pad = player.pad
            ix = pad.cur["x"]
            iy = pad.cur["y"]
            if player.state == "run":
                solids = self._solids(player.body.x - 48, player.body.x + 110)
                hazards = self._hazards(player.body.x - 20, player.body.x + 40)
                did = tick_runner(player, ix, pad.held("jump"), pad.pressed("jump"), solids, self.stats)
                if did == "jump":
                    sfx("jump")
                hit = touch_hazard(player, hazards, self.stats)
                if hit == "hit":
                    sfx("hit")
                    self.burst(player.body.x + 6, player.body.y + 8, (210, 70, 60))
                elif hit == "block":
                    sfx("power")
                    self.burst(player.body.x + 6, player.body.y + 4, (120, 230, 220))
                clamp_runner(player, self.camera, self.scroll if self.state == "play" else 0.0)
                if kill:
                    why = fate(player, self.camera)
                    if why:
                        result = start_ghost(player, self.camera)
                        if result == "ghost":
                            self.stats["ghosts"] += 1
                            sfx("ghost")
                        else:
                            self.stats["outs"] += 1
                            sfx("out")
            elif player.state == "ghost":
                solids = self._solids(self.camera - 20, self.camera + W + 20)
                result = tick_ghost(player, ix, iy, solids, self.camera, self.scroll)
                if result == "revive":
                    self.stats["revives"] += 1
                    sfx("revive")
                elif result == "expire":
                    self.stats["outs"] += 1
                    sfx("out")
            if player.state in ("run", "ghost") and player.body.x > player.max_x:
                player.max_x = player.body.x
        separate_bumps(self.players, self.stats)
        if self.world is not None:
            pull_coins(self.players, self.world.coins, self.stats)
            runners = [p for p in self.players if p.state == "run"]
            for player in self.players:
                for event in collect(player, self.world.coins, self.world.powers, self.players, self.stats):
                    if event == "coin":
                        sfx("coin")
                        self.burst(player.body.x, player.body.y, (255, 210, 70), 4)
                    else:
                        sfx("power")
                        self.burst(player.body.x, player.body.y - 6, (255, 244, 210), 8)
            tick_pickups(self.world.powers, runners)
        for player in self.players:
            player.tick_timers()

    def _maybe_end(self):
        running = [p for p in self.players if p.state == "run"]
        ghosts = [p for p in self.players if p.state == "ghost"]
        finish = self.world.finish_x if self.world else None
        reached = finish is not None and (
            self.camera + W * 0.55 >= finish or any(p.body.x >= finish and p.state == "run" for p in self.players)
        )
        last = len(running) <= 1 and not ghosts
        none = not running and not ghosts
        if reached or last or none:
            self.ending = 28

    def _finish_round(self):
        self.round_winners = award(self.players)
        self.stats["rounds_ended"] += 1
        sfx("win")
        self.ending = 0
        self.goto("roundend")

    def draw(self):
        draw_frame(self)
        self.screen.blit(self.canvas, (0, 0))
