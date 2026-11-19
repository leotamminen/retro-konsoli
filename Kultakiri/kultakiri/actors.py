# Runners, the one ghost rescue, bumps and powerups.
# Players never stand on each other and there is no stomp.
import math

from .const import (
    BUMP_VX, COIN_PTS, DIST_DIV, DUR, EY, FALL_Y, GHOST_FRAMES, GLIDE_FALL,
    H, INV_HAZARD, MAGNET_PULL, MAGNET_R, PH, PW, RUN, STUN_HAZARD, W, WIN_PTS,
)
from .physics import Body, rect_hit, step_body
from .text import tr


class Player:
    def __init__(self, idx, pad):
        self.idx = idx
        self.pad = pad
        self.pilot = None
        self.body = Body()
        self.state = "run"
        self.coins = 0
        self.total_coins = 0
        self.max_x = 0.0
        self.bank = 0
        self.wins = 0
        self.rescues = 1
        self.ghost_t = 0
        self.ghost_land = 0
        self.inv = 0
        self.double_t = 0
        self.speed_t = 0
        self.shield_t = 0
        self.shield = False
        self.magnet_t = 0
        self.slow_t = 0
        self.glide_t = 0
        self.face = 1
        self.anim = 0.0
        self.squash = 0.0
        self.popup = None
        self.lost_t = 0
        self.round_pts = 0
        self.round_meters = 0

    def reset_round(self):
        b = self.body
        b.vx = b.vy = 0.0
        b.on_ground = True
        b.coyote = 0
        b.buf = 0
        b.air_jumps = 0
        b.air_max = 0
        b.stun = 0
        b.slow = b.glide = b.speed = False
        b.was_jump = False
        self.state = "run"
        self.coins = 0
        self.rescues = 1
        self.ghost_t = 0
        self.ghost_land = 0
        self.inv = 18
        self.double_t = self.speed_t = self.shield_t = 0
        self.magnet_t = self.slow_t = self.glide_t = 0
        self.shield = False
        self.squash = 0.0
        self.popup = None
        self.round_pts = 0
        self.round_meters = 0
        if self.pilot is not None:
            self.pilot.hold = 0
            self.pilot.did_air = False

    def sync_flags(self):
        b = self.body
        b.speed = self.speed_t > 0
        b.glide = self.glide_t > 0
        b.slow = self.slow_t > 0
        b.air_max = 1 if self.double_t > 0 else 0

    def tick_timers(self):
        for name in ("double_t", "speed_t", "shield_t", "magnet_t", "slow_t", "glide_t"):
            value = getattr(self, name)
            if value > 0:
                setattr(self, name, value - 1)
        if self.shield_t <= 0:
            self.shield = False
        if self.inv > 0:
            self.inv -= 1
        if self.lost_t > 0:
            self.lost_t -= 1
        if self.popup is not None:
            text, left = self.popup
            self.popup = None if left <= 1 else (text, left - 1)
        if self.squash > 0.02:
            self.squash *= 0.72
        else:
            self.squash = 0.0

    def main_power(self):
        best = None
        best_t = 0
        for key, attr in (
            ("double", "double_t"), ("speed", "speed_t"), ("shield", "shield_t"),
            ("magnet", "magnet_t"), ("slow", "slow_t"), ("glide", "glide_t"),
        ):
            value = getattr(self, attr)
            if key == "shield" and not self.shield:
                continue
            if value > best_t:
                best_t = value
                best = key
        return best


def _note(stats, key, n=1):
    if stats is not None:
        stats[key] = stats.get(key, 0) + n


def _got(stats, kind):
    if stats is None:
        return
    got = stats.setdefault("got_powers", [])
    if kind not in got:
        got.append(kind)


def give_power(player, kind, others, stats=None):
    if kind == "double":
        player.double_t = DUR["double"]
        player.body.air_max = 1
        if not player.body.on_ground:
            player.body.air_jumps = max(player.body.air_jumps, 1)
    elif kind == "speed":
        player.speed_t = DUR["speed"]
    elif kind == "shield":
        player.shield = True
        player.shield_t = DUR["shield"]
        _note(stats, "shield_on")
    elif kind == "magnet":
        player.magnet_t = DUR["magnet"]
    elif kind == "slow":
        slowed = False
        for other in others:
            if other is not player and other.state == "run":
                other.slow_t = max(other.slow_t, DUR["slow"])
                slowed = True
        if slowed:
            _note(stats, "slow_on")
    elif kind == "glide":
        player.glide_t = DUR["glide"]
    player.popup = (tr("p_" + kind), 55)
    _got(stats, kind)


def tick_runner(player, ix, jump_held, jump_pressed, solids, stats=None):
    if player.state != "run":
        return None
    player.sync_flags()
    did, landed = step_body(player.body, ix, jump_held, jump_pressed, solids)
    b = player.body
    if did == "airjump":
        _note(stats, "double_air")
    if player.speed_t > 0 and b.vx > RUN + 0.12:
        _note(stats, "speed_fast")
    if player.glide_t > 0 and jump_held and (not b.on_ground) and abs(b.vy - GLIDE_FALL) < 0.08:
        _note(stats, "glide_frames")
    if b.vx > 0.25:
        player.face = 1
    elif b.vx < -0.25:
        player.face = -1
    if landed is not None:
        player.squash = 0.45
    player.anim += abs(b.vx)
    return did


def touch_hazard(player, hazards, stats=None):
    if player.state != "run" or player.inv > 0:
        return None
    b = player.body
    for hx, hy, hw, hh in hazards:
        if not rect_hit(b.x, b.y, b.w, b.h, hx, hy, hw, hh):
            continue
        if player.shield:
            player.shield = False
            player.shield_t = 0
            player.inv = INV_HAZARD
            b.vy = -2.4
            b.on_ground = False
            _note(stats, "shield_block")
            return "block"
        b.vx = -1.7
        b.vy = -3.1
        b.on_ground = False
        b.stun = STUN_HAZARD
        player.inv = INV_HAZARD
        return "hit"
    return None


def fate(player, camera_x):
    if player.state != "run":
        return None
    if player.body.y > FALL_Y - 10:
        return "fall"
    if player.body.x + player.body.w < camera_x - 1:
        return "behind"
    return None


def start_ghost(player, camera_x):
    """One rescue per round. Coins still count. A second miss is out for the round."""
    if player.rescues <= 0:
        player.state = "out"
        player.popup = (tr("out"), 50)
        return "out"
    player.rescues -= 1
    player.state = "ghost"
    player.ghost_t = GHOST_FRAMES
    player.ghost_land = 0
    player.body.x = camera_x + 56
    player.body.y = 52
    player.body.vx = 0.0
    player.body.vy = 0.0
    player.body.on_ground = False
    player.body.stun = 0
    player.inv = 0
    player.popup = (tr("ghost"), 45)
    return "ghost"


def tick_ghost(player, ix, iy, solids, camera_x, scroll):
    player.ghost_t -= 1
    player.body.vx = scroll + ix * 1.15
    player.body.vy = iy * 1.2 + 0.16
    player.body.x += player.body.vx
    player.body.y += player.body.vy
    lo = camera_x + 2
    hi = camera_x + W - PW - 2
    player.body.x = lo if player.body.x < lo else (hi if player.body.x > hi else player.body.x)
    if player.body.y < 16:
        player.body.y = 16
    elif player.body.y > H - PH - 12:
        player.body.y = H - PH - 12
    feet = player.body.feet()
    cx = player.body.x + PW * 0.5
    top = None
    for px, py, pw in solids:
        if px - 2 <= cx <= px + pw + 2 and abs(feet - py) <= 7:
            top = py
            break
    if top is not None:
        player.ghost_land += 1
        if player.ghost_land >= 8:
            player.body.y = top - PH
            player.body.vy = 0.0
            player.body.vx = max(player.body.vx, scroll)
            player.body.on_ground = True
            player.sync_flags()
            player.body.air_jumps = player.body.air_max
            player.state = "run"
            player.inv = 36
            player.ghost_t = 0
            return "revive"
    else:
        player.ghost_land = 0
    if player.ghost_t <= 0:
        player.state = "out"
        player.popup = (tr("out"), 50)
        return "expire"
    return None


def clamp_runner(player, camera_x, scroll):
    if player.state != "run":
        return
    limit = camera_x + W - PW - 3
    if player.body.x > limit:
        player.body.x = limit
        if player.body.vx > scroll:
            player.body.vx = scroll


def separate_bumps(players, stats=None):
    runners = [p for p in players if p.state == "run"]
    for i, a in enumerate(runners):
        for b in runners[i + 1:]:
            ab, bb = a.body, b.body
            if not rect_hit(ab.x, ab.y, ab.w, ab.h, bb.x, bb.y, bb.w, bb.h):
                continue
            if abs((ab.y + ab.h * 0.5) - (bb.y + bb.h * 0.5)) > PH * 0.42:
                continue
            if ab.x <= bb.x:
                ab.vx = min(ab.vx, -BUMP_VX)
                bb.vx = max(bb.vx, BUMP_VX)
                overlap = (ab.x + ab.w) - bb.x
                if overlap > 0:
                    ab.x -= overlap * 0.5 + 0.4
                    bb.x += overlap * 0.5 + 0.4
            else:
                bb.vx = min(bb.vx, -BUMP_VX)
                ab.vx = max(ab.vx, BUMP_VX)
                overlap = (bb.x + bb.w) - ab.x
                if overlap > 0:
                    bb.x -= overlap * 0.5 + 0.4
                    ab.x += overlap * 0.5 + 0.4
            _note(stats, "bumps")


def pull_coins(players, coins, stats=None):
    for player in players:
        if player.state != "run" or player.magnet_t <= 0:
            continue
        cx = player.body.x + PW * 0.5
        cy = player.body.y + PH * 0.5
        for coin in coins:
            if not coin.alive:
                continue
            dx = cx - coin.x
            dy = cy - coin.y
            dist = math.hypot(dx, dy)
            if 1.0 < dist <= MAGNET_R:
                coin.x += dx / dist * MAGNET_PULL
                coin.y += dy / dist * MAGNET_PULL
                _note(stats, "magnet_pulls")


def _near(player, x, y, rx, ry):
    return abs((player.body.x + PW * 0.5) - x) <= rx and abs((player.body.y + PH * 0.45) - y) <= ry


def collect(player, coins, powers, players, stats=None):
    if player.state == "out":
        return []
    events = []
    for coin in coins:
        if coin.alive and _near(player, coin.x, coin.y, 12, 18):
            coin.alive = False
            player.coins += 1
            player.total_coins += 1
            _note(stats, "coins")
            events.append("coin")
    if player.state != "run":
        return events
    for pickup in powers:
        if not pickup.alive or not _near(player, pickup.x, pickup.y, 14, 18):
            continue
        if pickup.shared:
            if player.idx in pickup.got:
                continue
            pickup.got.add(player.idx)
            pickup.linger = 80
            give_power(player, pickup.kind, players, stats)
            events.append(pickup.kind)
            continue
        pickup.alive = False
        give_power(player, pickup.kind, players, stats)
        events.append(pickup.kind)
    return events


def tick_pickups(powers, runners):
    alive_ids = {p.idx for p in runners}
    for pickup in powers:
        if not pickup.alive:
            continue
        pickup.t += 1
        if pickup.shared and pickup.got:
            pickup.linger -= 1
            if pickup.linger <= 0 or alive_ids and alive_ids <= pickup.got:
                pickup.alive = False


def award(players):
    running = [p for p in players if p.state == "run"]
    ghosts = [p for p in players if p.state == "ghost"]
    pool = running or ghosts or list(players)
    best_x = max(p.max_x for p in pool)
    top = [p for p in pool if p.max_x >= best_x - 12]
    best_c = max(p.coins for p in top)
    winners = [p for p in top if p.coins == best_c]
    for player in players:
        won = player in winners
        player.round_meters = int(player.max_x) // 16
        player.round_pts = player.coins * COIN_PTS + int(player.max_x) // DIST_DIV + (WIN_PTS if won else 0)
        player.bank += player.round_pts
        if won:
            player.wins += 1
    return winners


def spawn_feet(player, x):
    player.body.x = float(x)
    player.body.y = EY - PH
    player.body.vx = 0.0
    player.body.vy = 0.0
    player.body.on_ground = True
    player.max_x = player.body.x
