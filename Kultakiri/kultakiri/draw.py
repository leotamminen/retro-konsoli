# Chunky dawn meadow. One cached sky, everything else is a handful of rects.
import math

import pygame

from .const import EY, H, PCOLORS, PH, POWER_COLORS, PW, W
from .font import blit
from .text import pname, tr

SKY_TOP = (255, 168, 132)
SKY_BOT = (255, 226, 206)
HILL_FAR = (176, 196, 168)
HILL = (104, 168, 112)
RAVINE = (48, 78, 90)
GRASS = (168, 210, 92)
GRASS_DK = (72, 150, 68)
DIRT = (168, 118, 70)
DIRT_DK = (116, 74, 46)
SAND = (228, 190, 112)
CLOUD = (255, 248, 242)


def make_sky():
    surf = pygame.Surface((W, H))
    for y in range(H):
        k = y / (H - 1)
        col = tuple(int(SKY_TOP[i] + (SKY_BOT[i] - SKY_TOP[i]) * k) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (W, y))
    return surf


def _plat_kind(top):
    if top < EY - 6:
        return "high"
    if top > EY + 6:
        return "low"
    return "ground"


def draw_world(g):
    c = g.canvas
    cam = g.camera
    c.blit(g.sky, (0, 0))
    # far hills, then a ravine the ground covers
    for i in range(-1, 22):
        wx = i * 16 + cam * 0.25
        h = 16 + int(7 * math.sin(wx * 0.04))
        x = int(i * 16 - (cam * 0.25) % 16)
        pygame.draw.rect(c, HILL_FAR, (x, EY - 36 - h, 16, h + 8))
    pygame.draw.rect(c, RAVINE, (0, EY + 6, W, H - EY))
    for i in range(-1, 22):
        wx = i * 18 + cam * 0.45
        h = 10 + int(5 * math.sin(wx * 0.07 + 1.2))
        x = int(i * 18 - (cam * 0.45) % 18)
        pygame.draw.rect(c, HILL, (x, EY - 16 - h, 18, h))
    _clouds(c, cam, g.t)
    if g.world is not None:
        _chunks(c, g.world, cam, g.t)
        _coins(c, g.world.coins, cam, g.t)
        _pickups(c, g.world.powers, cam, g.t)
    _bits(c, g.bits, cam)
    for pl in g.players:
        if pl.state == "out":
            continue
        draw_player(c, pl, cam, g.t)
    if g.camera > 8:
        # left-edge warning when someone is about to be left behind
        for pl in g.players:
            if pl.state == "run" and pl.body.x - cam < 28:
                pygame.draw.rect(c, (210, 70, 60), (0, 16, 3, H - 16))
                break
    _hud(g)


def _clouds(c, cam, t):
    specs = ((30, 28, 0.12), (110, 18, 0.18), (200, 36, 0.1), (270, 22, 0.16))
    for i, (bx, by, spd) in enumerate(specs):
        x = int((bx - cam * spd + t * 0.05) % (W + 50) - 24)
        pygame.draw.rect(c, (255, 214, 196), (x + 2, by + 3, 22, 6))
        pygame.draw.rect(c, CLOUD, (x, by, 18, 7))
        pygame.draw.rect(c, CLOUD, (x + 8, by - 4, 14, 6))


def _chunks(c, world, cam, t):
    for origin, chunk in world.placed:
        if origin + chunk.w < cam - 8 or origin > cam + W + 8:
            continue
        for px, top, pw in chunk.plats:
            _platform(c, origin + px - cam, top, pw)
        for hx, hy, hw, hh in chunk.hazards:
            _thorn(c, origin + hx - cam, hy, hw, hh, t)
        for hx, hy, hw, hh in chunk.ceilings:
            _ceiling(c, origin + hx - cam, hy, hw, hh)
        if chunk.name == "maali":
            _banner(c, origin + 56 - cam, g_font=None, font=None, t=t, canvas_font=c)
    for tile in world.crumbles:
        if tile.x + tile.w < cam - 8 or tile.x > cam + W + 8:
            continue
        _crumble(c, tile.x - cam, tile.top, tile.w, tile)
    for slab in world.movers:
        x, top, w = slab.at(world.frame)
        if x + w < cam - 8 or x > cam + W + 8:
            continue
        _mover(c, x - cam, top, w)


def _platform(c, x, top, w):
    x, top, w = int(x), int(top), int(w)
    if x > W or x + w < 0:
        return
    kind = _plat_kind(top)
    if kind == "ground":
        h = H - top + 2
        body, edge = DIRT, DIRT_DK
        cap = GRASS
    elif kind == "high":
        h = 12
        body, edge = (214, 168, 96), (150, 110, 54)
        cap = SAND
    else:
        h = 12
        body, edge = (150, 108, 70), (96, 64, 40)
        cap = (196, 150, 86)
    pygame.draw.rect(c, body, (x, top, w, h))
    cap_h = 7 if kind == "ground" else 4
    pygame.draw.rect(c, cap, (x, top, w, cap_h))
    pygame.draw.rect(c, (210, 230, 120) if kind == "ground" else (255, 236, 190), (x, top, w, 2))
    pygame.draw.line(c, edge, (x, top + h - 1), (x + w - 1, top + h - 1))
    for dx in range(3, w - 2, 7):
        _dot(c, x + dx, top + 6, edge)


def _ceiling(c, x, y, w, h):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if x > W or x + w < 0:
        return
    pygame.draw.rect(c, (70, 48, 58), (x, y, w, 4))
    n = max(2, w // 6)
    for i in range(n):
        bx = x + int(i * w / n)
        pygame.draw.polygon(c, (210, 70, 78), [(bx + 1, y + 3), (bx + 4, y + h), (bx + 7, y + 3)])


def _crumble(c, x, top, w, tile):
    x, top, w = int(x), int(top), int(w)
    if not tile.live:
        return
    shake = (tile.timer // 3) % 2 if tile.armed else 0
    x += shake
    pygame.draw.rect(c, (150, 96, 58), (x, top, w, 10))
    pygame.draw.rect(c, (196, 150, 86), (x, top, w, 3))
    col = (80, 40, 28) if tile.armed else (90, 60, 40)
    for dx in range(4, max(5, w - 4), 8):
        pygame.draw.line(c, col, (x + dx, top + 3), (x + dx + 2, top + 9))


def _mover(c, x, top, w):
    x, top, w = int(x), int(top), int(w)
    pygame.draw.rect(c, (70, 90, 110), (x, top + 8, w, 3))
    pygame.draw.rect(c, (150, 186, 206), (x, top, w, 8))
    pygame.draw.rect(c, (230, 244, 250), (x, top, w, 2))
    pygame.draw.rect(c, (40, 60, 80), (x, top, w, 8), 1)


def _thorn(c, x, y, w, h, t):
    x, y, w, h = int(x), int(y), int(w), int(h)
    pygame.draw.rect(c, (92, 48, 64), (x, y + h - 3, w, 4))
    n = max(2, w // 5)
    for i in range(n):
        bx = x + int(i * w / n)
        pygame.draw.polygon(c, (70, 120, 64), [(bx, y + h), (bx + 3, y + 1), (bx + 6, y + h)])
        tip = (220, 60, 70) if (i + t // 8) % 2 == 0 else (255, 120, 90)
        pygame.draw.line(c, tip, (bx + 3, y + 1), (bx + 3, y + 4))


def _dot(c, x, y, col):
    if 0 <= x < W and 0 <= y < H:
        c.set_at((int(x), int(y)), col)


def _banner(c, x, g_font, font, t, canvas_font):
    x = int(x)
    pole_y = EY - 46
    if x < -40 or x > W + 10:
        return
    pygame.draw.rect(c, (96, 64, 40), (x, pole_y, 3, 46))
    pygame.draw.polygon(c, (240, 96, 84), [(x + 3, pole_y), (x + 28, pole_y + 7), (x + 3, pole_y + 14)])
    pygame.draw.polygon(c, (255, 210, 120), [(x + 3, pole_y), (x + 16, pole_y + 5), (x + 3, pole_y + 8)])
    blit(c, _font(c), tr("finish"), x + 6, pole_y + 3, (255, 248, 230), 1, shadow=False)


def _coins(c, coins, cam, t):
    for coin in coins:
        if not coin.alive:
            continue
        sx = int(coin.x - cam)
        if sx < -8 or sx > W + 8:
            continue
        bob = int(math.sin(t * 0.18 + coin.x * 0.1) * 1.5)
        sy = int(coin.y + bob)
        span = 2 + int(abs(math.sin(t * 0.25 + coin.x)) * 3)
        pygame.draw.rect(c, (120, 72, 20), (sx - span, sy - 3, span * 2, 8))
        pygame.draw.rect(c, (255, 210, 64), (sx - span + 1, sy - 2, max(1, span * 2 - 2), 6))
        _dot(c, sx, sy, (255, 250, 210))


def _pickups(c, powers, cam, t):
    for pw in powers:
        if not pw.alive:
            continue
        sx = int(pw.x - cam)
        if sx < -16 or sx > W + 16:
            continue
        bob = int(math.sin(t * 0.16 + pw.t * 0.2) * 2)
        draw_power_icon(c, pw.kind, sx, int(pw.y + bob), pulse=(t // 6) % 2 == 0)


def draw_power_icon(c, kind, x, y, pulse=False, small=False):
    col = POWER_COLORS[kind]
    s = 6 if small else 8
    pygame.draw.rect(c, (255, 255, 255), (x - s - 1, y - s - 1, s * 2 + 2, s * 2 + 2))
    pygame.draw.rect(c, col, (x - s, y - s, s * 2, s * 2))
    if pulse and not small:
        pygame.draw.rect(c, (255, 244, 180), (x - s - 2, y - s - 2, s * 2 + 4, s * 2 + 4), 1)
    ink = (255, 255, 255)
    if kind == "double":
        pygame.draw.polygon(c, ink, [(x - 3, y + 1), (x, y - 4), (x + 1, y + 1)])
        pygame.draw.polygon(c, ink, [(x + 1, y + 3), (x + 4, y - 2), (x + 5, y + 3)])
    elif kind == "speed":
        pygame.draw.polygon(c, (255, 236, 120), [(x - 2, y - 5), (x + 2, y - 5), (x - 1, y), (x + 3, y), (x - 3, y + 6), (x, y + 1), (x - 4, y + 1)])
    elif kind == "shield":
        pygame.draw.circle(c, ink, (x, y), s - 3, 1)
        pygame.draw.circle(c, (230, 255, 255), (x, y), 2)
    elif kind == "magnet":
        pygame.draw.rect(c, ink, (x - 4, y - 3, 2, 6))
        pygame.draw.rect(c, ink, (x + 2, y - 3, 2, 6))
        pygame.draw.rect(c, ink, (x - 4, y + 1, 8, 2))
    elif kind == "slow":
        pygame.draw.circle(c, ink, (x - 2, y + 1), 3, 1)
        pygame.draw.circle(c, ink, (x + 3, y - 1), 2, 1)
    elif kind == "glide":
        pygame.draw.polygon(c, ink, [(x - 6, y + 1), (x, y - 4), (x + 6, y + 1), (x, y + 2)])
    if small:
        return
    # kind letter is the shape; the ring keeps it readable at a glance


def _bits(c, bits, cam):
    for x, y, vx, vy, life, col in bits:
        sx = int(x - cam)
        if 0 <= sx < W:
            size = 2 if life > 8 else 1
            pygame.draw.rect(c, col, (sx, int(y), size, size))


def draw_player(c, pl, cam, t):
    b = pl.body
    x = int(b.x - cam)
    y = int(b.y)
    ghost = pl.state == "ghost"
    col, dark = PCOLORS[pl.idx]
    if ghost:
        col = tuple((v + 255) // 2 for v in col)
    if pl.slow_t > 0 and not ghost:
        pygame.draw.ellipse(c, POWER_COLORS["slow"], (x - 6, y - 4, PW + 12, PH + 10), 2)
    # shadow
    pygame.draw.ellipse(c, (40, 30, 40), (x + 1, int(b.feet() - cam * 0 + 1) if False else y + PH - 1, PW, 3))
    if pl.glide_t > 0 and not ghost:
        cape = (x - 6, y + 4, 6, 8) if pl.face > 0 else (x + PW, y + 4, 6, 8)
        pygame.draw.rect(c, POWER_COLORS["glide"], cape)
    squash = pl.squash
    bh = max(8, int(PH - 4 - squash * 6))
    bw = PW + int(squash * 6)
    bx = x + (PW - bw) // 2
    by = y + PH - 4 - bh
    pygame.draw.rect(c, dark, (bx - 1, by - 1, bw + 2, bh + 2))
    pygame.draw.rect(c, col, (bx, by, bw, bh))
    pygame.draw.rect(c, tuple(min(255, v + 50) for v in col), (bx + 1, by + 1, max(1, bw - 3), 2))
    # feet
    step = int(pl.anim / 5) % 2 if pl.state == "run" and abs(b.vx) > 0.3 else 0
    pygame.draw.rect(c, dark, (bx + 1 + step, by + bh, 3, 3))
    pygame.draw.rect(c, dark, (bx + bw - 5 - step, by + bh, 3, 3))
    # face
    ex = bx + bw // 2 + pl.face * 2
    pygame.draw.rect(c, (255, 255, 255), (ex - 3, by + 3, 2, 3))
    pygame.draw.rect(c, (255, 255, 255), (ex + 1, by + 3, 2, 3))
    pygame.draw.rect(c, (20, 16, 24), (ex - 2 + (pl.face > 0), by + 4, 1, 2))
    pygame.draw.rect(c, (20, 16, 24), (ex + 2 + (pl.face > 0), by + 4, 1, 2))
    pygame.draw.rect(c, (90, 40, 40), (ex - 1, by + bh - 4, 3, 1))
    _hat(c, pl.idx, bx, by, bw, col)
    if pl.double_t > 0 and not ghost:
        pygame.draw.polygon(c, (210, 235, 255), [(bx - 4, by + 4), (bx - 1, by + 1), (bx - 1, by + 7)])
        pygame.draw.polygon(c, (210, 235, 255), [(bx + bw + 3, by + 4), (bx + bw, by + 1), (bx + bw, by + 7)])
    if pl.speed_t > 0 and not ghost and t % 2 == 0:
        for i in range(3):
            pygame.draw.rect(c, POWER_COLORS["speed"], (bx - 5 - i * 3, by + 3 + i * 3, 3, 1))
    if pl.shield and not ghost:
        pygame.draw.circle(c, POWER_COLORS["shield"], (x + PW // 2, y + PH // 2), 12, 1)
    if pl.magnet_t > 0 and not ghost:
        ang = t * 0.3 + pl.idx
        for k in range(3):
            a = ang + k * 2.1
            _dot(c, int(x + PW / 2 + math.cos(a) * 10), int(y + 4 + math.sin(a) * 6), (255, 220, 80))
    if ghost:
        pygame.draw.circle(c, (255, 255, 255), (x + PW // 2, y - 4), 6, 1)
    # Power names stay on the icons. Only short status words float over a player,
    # otherwise four runners grabbing the same row of pickups paint on top of each other.
    if pl.popup and pl.popup[0] in (tr("ghost"), tr("out"), tr("pad")):
        label, _life = pl.popup
        blit(c, _font(c), label, x + PW // 2, y - 14, (255, 244, 210), 1, center=True)
    if pl.lost_t > 0 and (t // 10) % 2 == 0:
        blit(c, _font(c), tr("pad"), x + PW // 2, y - 22, (255, 180, 160), 1, center=True)


def _hat(c, idx, bx, by, bw, col):
    if idx == 0:
        pygame.draw.rect(c, (40, 120, 48), (bx + bw // 2 - 1, by - 4, 2, 4))
        pygame.draw.rect(c, (70, 160, 60), (bx + bw // 2 - 2, by - 6, 4, 2))
    elif idx == 1:
        pygame.draw.rect(c, (20, 40, 90), (bx + 1, by - 3, bw - 2, 3))
        pygame.draw.rect(c, (20, 40, 90), (bx, by - 1, bw, 2))
    elif idx == 2:
        pygame.draw.polygon(c, (40, 150, 60), [(bx + bw // 2, by - 6), (bx + bw // 2 + 6, by - 1), (bx + bw // 2, by - 1)])
    else:
        pygame.draw.rect(c, (230, 80, 90), (bx + bw // 2 - 2, by - 4, 4, 3))
        pygame.draw.rect(c, (255, 220, 80), (bx + bw // 2 - 1, by - 3, 2, 2))


_FONT = None


def _font(c):
    global _FONT
    if _FONT is None:
        from .font import Font
        _FONT = Font()
    return _FONT


def bind_font(font):
    global _FONT
    _FONT = font


def _hud(g):
    c = g.canvas
    bar = pygame.Surface((W, 15), pygame.SRCALPHA)
    bar.fill((28, 18, 32, 170))
    c.blit(bar, (0, 0))
    font = _font(c)
    blit(c, font, tr("round", g.round_no, 3) if g.round_no else "", 3, 3, (255, 236, 210), 1, shadow=False)
    meters = "%d%s" % (int(g.camera) // 16, tr("meters"))
    mw, _ = font.size(meters, 1)
    blit(c, font, meters, W - mw - 3, 3, (255, 236, 210), 1, shadow=False)
    n = max(1, len(g.players))
    slot = min(70, (W - 78) // n)
    for i, pl in enumerate(g.players):
        x = 52 + i * slot
        col = PCOLORS[pl.idx][0] if pl.state != "out" else (90, 80, 80)
        pygame.draw.rect(c, col, (x, 3, 7, 7))
        label = tr("out") if pl.state == "out" else str(pl.coins)
        blit(c, font, label, x + 9, 3, (255, 248, 230), 1, shadow=False)
        kind = pl.main_power()
        if kind and pl.state == "run":
            draw_power_icon(c, kind, x + 28, 7, small=True)


def draw_lobby(g):
    c = g.canvas
    c.blit(g.sky, (0, 0))
    _clouds(c, 0, g.t)
    pygame.draw.rect(c, HILL, (0, 120, W, 60))
    pygame.draw.rect(c, GRASS, (0, 116, W, 6))
    font = _font(c)
    bob = int(math.sin(g.t * 0.08) * 2)
    blit(c, font, tr("title"), W // 2, 16 + bob, (120, 50, 40), 2, center=True)
    ver = "V" + g.version
    vw, _ = font.size(ver, 1)
    blit(c, font, ver, W - vw - 4, 3, (150, 90, 70), 1, shadow=False)
    blit(c, font, tr("tag"), W // 2, 40, (110, 60, 50), 1, center=True)
    for i in range(4):
        x = 8 + i * 78
        box = pygame.Rect(x, 52, 74, 78)
        pygame.draw.rect(c, (255, 244, 230), box)
        pygame.draw.rect(c, PCOLORS[i][1], box, 2)
        if i < len(g.players):
            pl = g.players[i]
            pl.body.x = x + 30
            pl.body.y = 78 + int(abs(math.sin(g.t * 0.12 + i)) * -4)
            pl.face = 1
            pl.anim = g.t * 0.4
            draw_player(c, pl, 0, g.t)
            blit(c, font, pname(i), x + 37, 116, PCOLORS[i][0], 1, center=True)
        else:
            if (g.t // 25) % 2 == 0:
                blit(c, font, tr("press"), x + 37, 78, (140, 100, 90), 1, center=True)
            blit(c, font, tr("join"), x + 37, 92, (120, 90, 80), 1, center=True)
    hint = tr("start_hint") + "   " + tr("legend_btn") if len(g.players) >= 2 else tr("need")
    blit(c, font, hint, W // 2, 146, (90, 50, 40), 1, center=True)
    blit(c, font, tr("leave_hint") + "   " + tr("quit_hint"), W // 2, 162, (120, 80, 70), 1, center=True)


def draw_legend(g):
    draw_lobby(g) if g.legend_from == "lobby" else draw_world(g)
    _panel_legend(g)


def _panel_legend(g):
    c = g.canvas
    veil = pygame.Surface((W, H), pygame.SRCALPHA)
    veil.fill((24, 14, 20, 180))
    c.blit(veil, (0, 0))
    font = _font(c)
    blit(c, font, tr("legend"), W // 2, 8, (255, 220, 140), 1, center=True)
    kinds = ("double", "speed", "shield", "magnet", "slow", "glide")
    for i, kind in enumerate(kinds):
        y = 24 + i * 22
        draw_power_icon(c, kind, 18, y + 6, pulse=True)
        blit(c, font, tr("p_" + kind), 32, y, POWER_COLORS[kind], 1)
        blit(c, font, tr("d_" + kind), 118, y, (255, 244, 230), 1)
    blit(c, font, tr("controls"), W // 2, 160, (255, 220, 180), 1, center=True)
    blit(c, font, tr("back"), W // 2, 170, (255, 244, 220), 1, center=True)


def draw_count(g):
    font = _font(g.canvas)
    if g.t < 36:
        label, col = "3", (255, 120, 90)
    elif g.t < 72:
        label, col = "2", (255, 170, 80)
    elif g.t < 108:
        label, col = "1", (255, 210, 90)
    else:
        label, col = tr("go"), (255, 244, 160)
    blit(g.canvas, font, label, W // 2, 78, col, 3, center=True)


def draw_round_end(g):
    c = g.canvas
    veil = pygame.Surface((W, H), pygame.SRCALPHA)
    veil.fill((20, 12, 18, 150))
    c.blit(veil, (0, 0))
    font = _font(c)
    panel = pygame.Rect(16, 18, W - 32, H - 36)
    pygame.draw.rect(c, (255, 244, 230), panel)
    pygame.draw.rect(c, (120, 60, 48), panel, 2)
    winners = g.round_winners or []
    if len(winners) == 1:
        title = tr("win", pname(winners[0].idx))
        col = PCOLORS[winners[0].idx][0]
    else:
        title, col = tr("draw"), (120, 60, 48)
    blit(c, font, title, W // 2, 26, col, 1, center=True)
    blit(c, font, tr("board"), W // 2, 40, (120, 70, 50), 1, center=True)
    order = sorted(g.players, key=lambda p: -p.bank)
    for i, pl in enumerate(order):
        y = 54 + i * 22
        pygame.draw.rect(c, PCOLORS[pl.idx][0], (24, y, 8, 8))
        blit(c, font, pname(pl.idx), 36, y - 1, (80, 40, 36), 1)
        line = "%s %d  %s %d  %s %d" % (tr("coins"), pl.coins, tr("meters"), pl.round_meters, tr("total"), pl.bank)
        blit(c, font, line, 36, y + 8, (110, 70, 55), 1)
    if g.t > 20 and (g.t // 20) % 2 == 0:
        blit(c, font, tr("next"), W // 2, 156, (160, 70, 50), 1, center=True)


def draw_results(g):
    c = g.canvas
    c.blit(g.sky, (0, 0))
    pygame.draw.rect(c, HILL, (0, 156, W, 24))
    pygame.draw.rect(c, GRASS, (0, 152, W, 5))
    font = _font(c)
    blit(c, font, tr("results"), W // 2, 6, (120, 50, 40), 1, center=True)
    if g.players:
        champ = max(g.players, key=lambda p: (p.bank, p.wins, p.total_coins, -p.idx))
        blit(c, font, tr("champ", pname(champ.idx)), W // 2, 18, PCOLORS[champ.idx][0], 1, center=True)
        champ.body.x = W // 2 - PW // 2
        champ.body.y = 30
        champ.face = 1
        champ.state = "run"
        champ.squash = 0
        draw_player(c, champ, 0, g.t)
    order = sorted(g.players, key=lambda p: (-p.bank, -p.wins))
    panel = pygame.Rect(16, 64, W - 32, 72)
    pygame.draw.rect(c, (255, 246, 232), panel)
    pygame.draw.rect(c, (140, 80, 60), panel, 2)
    for i, pl in enumerate(order):
        y = 70 + i * 16
        pygame.draw.rect(c, PCOLORS[pl.idx][0], (28, y, 8, 8))
        blit(c, font, pname(pl.idx), 42, y, (70, 36, 32), 1, shadow=False)
        blit(c, font, str(pl.bank), 168, y, (90, 50, 40), 1, shadow=False)
        for k in range(pl.wins):
            pygame.draw.rect(c, (220, 160, 40), (230 + k * 8, y, 6, 6))
    blit(c, font, tr("rematch") + "   " + tr("back_lobby"), W // 2, 166, (255, 248, 236), 1, center=True)


def draw_pause(g):
    c = g.canvas
    veil = pygame.Surface((W, H), pygame.SRCALPHA)
    veil.fill((20, 12, 18, 150))
    c.blit(veil, (0, 0))
    font = _font(c)
    blit(c, font, tr("paused"), W // 2, 48, (255, 220, 150), 2, center=True)
    opts = (tr("resume"), tr("to_lobby"), tr("quit"))
    for i, label in enumerate(opts):
        y = 84 + i * 20
        if i == g.menu_i:
            pygame.draw.rect(c, (255, 210, 140), (70, y - 3, 180, 16))
        blit(c, font, label, W // 2, y, (90, 40, 36), 1, center=True)


def draw_quit(g):
    if g.quit_hold < 6:
        return
    c = g.canvas
    bw = 120
    x = W // 2 - bw // 2
    pygame.draw.rect(c, (40, 20, 24), (x, 4, bw, 10))
    pygame.draw.rect(c, (255, 244, 230), (x, 4, int(bw * min(1, g.quit_hold / 60)), 10))
    blit(c, _font(c), tr("quitting"), W // 2, 5, (80, 30, 30), 1, center=True)


def draw_frame(g):
    if g.font is not None:
        bind_font(g.font)
    st = g.state
    if st == "lobby":
        draw_lobby(g)
    elif st == "legend":
        draw_legend(g)
    elif st == "results":
        draw_results(g)
    else:
        draw_world(g)
        if st == "ready":
            draw_count(g)
        elif st == "play" and g.go_flash:
            blit(g.canvas, _font(g.canvas), tr("go"), W // 2, 78, (255, 244, 160), 3, center=True)
        elif st == "roundend":
            draw_round_end(g)
        elif st == "paused":
            draw_pause(g)
    draw_quit(g)
