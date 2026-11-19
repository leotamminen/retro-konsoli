# 320x180 sauna. The background is painted once; the frame only adds fire, people and steam.
import math

import pygame

from .const import FPS, H, PCOLORS, PH, PLACES, PW, W
from .font import blit
from .text import label, pname, tr

WOOD_DK = (78, 42, 24)
WOOD = (132, 78, 42)
WOOD_LT = (176, 116, 64)
LOG = (112, 64, 34)
LOG_DK = (64, 36, 20)
STONE = (62, 60, 66)
STONE_LT = (108, 104, 110)
LAKE = (32, 86, 122)
LAKE_DK = (18, 52, 82)
ICE = (214, 232, 236)
SKY_TOP = (24, 36, 72)
SKY_BOT = (78, 118, 158)
PINE = (18, 46, 34)
SKIN = (255, 214, 186)
HOT = (214, 42, 36)


def _mix(a, b, t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_background():
    s = pygame.Surface((W, H))
    for y in range(H):
        k = y / float(H - 1)
        s.fill(_mix(SKY_TOP, SKY_BOT, k), (0, y, 112, 1))
    pygame.draw.circle(s, (232, 226, 196), (22, 28), 8)
    pygame.draw.circle(s, SKY_TOP, (26, 26), 7)
    _pine(s, 4, 78)
    _pine(s, 72, 86)
    pygame.draw.rect(s, LAKE_DK, (0, 160, 112, 20))
    pygame.draw.rect(s, LAKE, (0, 158, 112, 6))
    pygame.draw.ellipse(s, ICE, (12, 156, 44, 12))
    pygame.draw.ellipse(s, (16, 40, 64), (20, 159, 28, 8))
    for x in range(0, 100, 8):
        pygame.draw.rect(s, WOOD if (x // 8) % 2 == 0 else WOOD_LT, (x, 142, 8, 16))
        pygame.draw.rect(s, WOOD_DK, (x, 142, 8, 2))
    pygame.draw.rect(s, LOG_DK, (96, 108, 18, 50))
    pygame.draw.rect(s, (48, 28, 18), (102, 116, 8, 34))
    for y in range(16, 156, 8):
        pygame.draw.rect(s, LOG if (y // 8) % 2 == 0 else WOOD, (112, y, W - 112, 8))
        pygame.draw.rect(s, LOG_DK, (112, y + 6, W - 112, 2))
    pygame.draw.rect(s, (36, 48, 78), (188, 22, 28, 14))
    pygame.draw.rect(s, WOOD_LT, (186, 20, 32, 18), 2)
    _bench(s, 156, 242, 50)
    _bench(s, 142, 254, 84)
    _bench(s, 128, 264, 118)
    pygame.draw.rect(s, WOOD_DK, (112, 156, W - 112, 24))
    for x in range(112, W, 10):
        pygame.draw.rect(s, WOOD, (x, 156, 9, 6))
    rail = (214, 176, 112)
    for y in range(50, 156, 7):
        pygame.draw.rect(s, rail, (230, y, 3, 6))
        pygame.draw.rect(s, rail, (246, y, 3, 6))
        pygame.draw.rect(s, (70, 40, 22), (233, y + 2, 13, 2))
    pygame.draw.rect(s, STONE, (276, 112, 38, 44))
    pygame.draw.rect(s, STONE_LT, (280, 116, 30, 8))
    pygame.draw.rect(s, (24, 22, 26), (286, 128, 18, 20))
    pygame.draw.rect(s, WOOD, (260, 146, 14, 10))
    pygame.draw.rect(s, (36, 78, 110), (263, 142, 8, 5))
    pygame.draw.rect(s, LOG_DK, (112, 16, W - 112, 6))
    return s


def _pine(s, x, top):
    pygame.draw.rect(s, (72, 48, 28), (x + 6, top + 36, 3, 18))
    pygame.draw.polygon(s, PINE, ((x + 7, top), (x, top + 22), (x + 14, top + 22)))
    pygame.draw.polygon(s, PINE, ((x + 7, top + 10), (x - 2, top + 36), (x + 16, top + 36)))


def _bench(s, x0, x1, y):
    pygame.draw.rect(s, WOOD_DK, (x0, y, x1 - x0, 8))
    for x in range(x0, x1, 8):
        pygame.draw.rect(s, WOOD_LT, (x, y, 7, 3))
    pygame.draw.rect(s, LOG_DK, (x0 + 6, y + 8, 3, 10))
    pygame.draw.rect(s, LOG_DK, (x1 - 10, y + 8, 3, 10))


def _font(g):
    return g.font


def draw_frame(g):
    st = g.state
    if st == "lobby":
        draw_lobby(g)
    elif st == "settings":
        draw_settings(g)
    elif st == "legend":
        draw_legend(g)
    elif st == "results":
        draw_results(g)
    else:
        draw_world(g)
        if st == "ready":
            draw_count(g)
        elif st == "play" and g.go_flash:
            blit(g.canvas, _font(g), tr("go"), W // 2, 78, (255, 236, 170), 3, center=True)
        elif st == "roundend":
            draw_round_end(g)
        elif st == "paused":
            draw_pause(g)
    _notes(g)
    draw_quit(g)


def draw_world(g):
    c = g.canvas
    c.blit(g.bg, (0, 0))
    _fire(c, g)
    _gust(c, g)
    if g.room is not None and g.room.item is not None:
        _item(c, g.room.item, g.t)
    _bits(c, g.bits)
    order = sorted(g.players, key=lambda p: (p.y, p.idx))
    for player in order:
        draw_player(c, player, g.t)
    _soak(c, g.t)
    if any(p.place in ("porch", "avanto") and p.mode != "faint" for p in g.players):
        pygame.draw.rect(c, WOOD_LT, (100, 116, 4, 28))
    _hud(g)


def _soak(c, t):
    """Drawn after the bathers so an avanto dip actually goes under the water."""
    shift = (t // 8) % 2
    pygame.draw.rect(c, LAKE if shift == 0 else LAKE_DK, (0, 166, 104, 14))
    pygame.draw.rect(c, ICE, (14, 163, 40, 3))
    pygame.draw.rect(c, (186, 224, 232), (24 + shift, 164, 12, 1))


def _fire(c, g):
    heat = 22 if g.room is None else g.room.heat
    glow = heat / 100.0
    if g.room is not None and g.room.loyly_t:
        glow = min(1.0, glow + 0.35)
    h = 6 + int(glow * 14)
    col = _mix((180, 70, 24), (255, 220, 90), glow)
    pygame.draw.rect(c, col, (290, 146 - h, 10, h))
    pygame.draw.rect(c, (255, 244, 210), (293, 148 - h, 4, max(3, h // 2)))
    if g.room is not None and g.room.fx == "flare" and g.room.fx_t:
        pygame.draw.rect(c, (255, 180, 60), (276, 112, 38, 4))


def _gust(c, g):
    if g.room is None or g.room.fx != "gust" or not g.room.fx_t:
        return
    x = 108 + (g.t % 5) * 3
    for i in range(4):
        pygame.draw.rect(c, (200, 220, 230), (x + i * 14, 132 + (i % 2) * 6, 10, 2))


def _item(c, item, t):
    spec = PLACES[item.place]
    x = int(item.x) - 3
    y = int(spec["y"]) - 12
    bob = int(math.sin(t * 0.15) * 1)
    y += bob
    if item.kind == "olut":
        pygame.draw.rect(c, (92, 60, 28), (x + 1, y + 2, 4, 8))
        pygame.draw.rect(c, (220, 200, 140), (x + 1, y, 4, 3))
        pygame.draw.rect(c, (240, 230, 200), (x, y - 1, 6, 2))
    else:
        pygame.draw.rect(c, (70, 140, 180), (x, y + 2, 8, 6))
        pygame.draw.rect(c, (230, 240, 245), (x, y + 4, 8, 2))


def _bits(c, bits):
    for bit in bits:
        x, y, _vx, _vy, life, col = bit
        if life <= 0:
            continue
        size = 3 if life > 12 else 2
        pygame.draw.rect(c, col, (int(x), int(y), size, size))


def draw_player(c, player, t, at=None):
    if at is None:
        x = int(player.x - PW // 2)
        y = int(player.y - PH)
    else:
        x, y = at
    heat = max(0.0, min(1.0, player.heat / 100.0))
    skin = _mix(SKIN, HOT, heat * 0.92)
    col, edge = PCOLORS[player.idx]
    if player.mode == "faint":
        feet = int(player.y) if at is None else y + PH
        _fainted(c, x, feet, skin, col, edge, t, player.idx)
        _meter(c, x, feet - PH, 1.0)
        return
    bob = 0
    if abs(player.vx) > 0.2 and player.mode == "move":
        bob = 1 if (player.anim // 4) % 2 == 0 else 0
    if player.place == "avanto":
        _body(c, x, y + 2, skin, col, edge, heat, t, player, bob, water=True)
    else:
        _body(c, x, y - bob, skin, col, edge, heat, t, player, bob, water=False)
    _meter(c, x, y - bob, heat)


def _body(c, x, y, skin, col, edge, heat, t, player, bob, water):
    pygame.draw.rect(c, (30, 18, 12), (x + 2, y + PH - 2, 8, 2))
    if not water:
        step = bob
        pygame.draw.rect(c, skin, (x + 2, y + 11, 3, 5))
        pygame.draw.rect(c, skin, (x + 7, y + 11 - step, 3, 5))
    pygame.draw.rect(c, col, (x + 1, y + 7, 10, 5))
    pygame.draw.rect(c, edge, (x + 1, y + 7, 10, 5), 1)
    pygame.draw.rect(c, skin, (x + 2, y + 1, 8, 7))
    pygame.draw.rect(c, edge, (x + 2, y + 1, 8, 7), 1)
    pygame.draw.rect(c, (50, 32, 24), (x + 2, y, 8, 2))
    look = 1 if player.face > 0 else 0
    if heat > 0.82:
        pygame.draw.rect(c, (60, 20, 20), (x + 3 + look, y + 3, 2, 1))
        pygame.draw.rect(c, (60, 20, 20), (x + 7 + look, y + 4, 2, 1))
    else:
        pygame.draw.rect(c, (40, 24, 24), (x + 3 + look, y + 3, 2, 2))
        pygame.draw.rect(c, (40, 24, 24), (x + 6 + look, y + 3, 2, 2))
    if heat > 0.42:
        drop = (t // 3 + player.idx * 3) % 8
        pygame.draw.rect(c, (190, 230, 255), (x - 1, y + 2 + drop, 1, 2))
    if player.cool_t > 0 and (t // 6) % 2 == 0:
        pygame.draw.rect(c, (140, 210, 230), (x + 4, y + 8, 4, 2))


def _fainted(c, x, feet, skin, col, edge, t, idx):
    y = feet - 8
    pygame.draw.rect(c, skin, (x, y, 6, 7))
    pygame.draw.rect(c, edge, (x, y, 6, 7), 1)
    pygame.draw.rect(c, col, (x + 6, y + 1, 12, 6))
    pygame.draw.rect(c, edge, (x + 6, y + 1, 12, 6), 1)
    pygame.draw.rect(c, (40, 16, 16), (x + 1, y + 2, 2, 1))
    pygame.draw.rect(c, (40, 16, 16), (x + 1, y + 4, 2, 1))
    pygame.draw.rect(c, (40, 16, 16), (x + 3, y + 3, 1, 1))
    for i in range(3):
        sx = x + 4 + i * 5
        sy = y - 5 + int(math.sin(t * 0.25 + i + idx) * 2)
        pygame.draw.rect(c, (255, 220, 80), (sx, sy, 2, 2))


def _meter(c, x, y, heat):
    bar_y = y - 4
    if bar_y < 16:
        bar_y = y + PH + 1
    pygame.draw.rect(c, (20, 12, 10), (x, bar_y, PW, 4))
    w = int((PW - 2) * max(0.0, min(1.0, heat)))
    if heat < 0.45:
        col = (72, 210, 96)
    elif heat < 0.75:
        col = (244, 196, 48)
    else:
        col = (232, 64, 48)
    if w:
        pygame.draw.rect(c, col, (x + 1, bar_y + 1, w, 2))


def _hud(g):
    c = g.canvas
    font = _font(g)
    pygame.draw.rect(c, (32, 18, 14), (0, 0, W, 16))
    pygame.draw.rect(c, (90, 52, 30), (0, 15, W, 1))
    for i, player in enumerate(g.players):
        x = 2 + i * 32
        pygame.draw.rect(c, PCOLORS[player.idx][0], (x, 4, 6, 8))
        blit(c, font, str(int(player.score)), x + 8, 1, (255, 236, 214), 1, shadow=False)
    rounds = getattr(g, "match_rounds", 3)
    hud = tr("round", g.round_no, rounds)
    blit(c, font, hud, 132, 1, (255, 214, 160), 1, shadow=False)
    left = 0 if g.room is None else max(0, g.round_left)
    secs = (left + FPS - 1) // FPS if left else 0
    # imported locally to keep this file from needing a cycle on a renamed const
    clock = "%d:%02d" % (secs // 60, secs % 60)
    col = (255, 120, 90) if 0 < secs <= 10 else (255, 244, 220)
    blit(c, font, clock, 214, 1, col, 1, shadow=False)
    heat = 0 if g.room is None else g.room.heat / 100.0
    pygame.draw.rect(c, (255, 220, 170), (262, 4, 54, 8), 1)
    pygame.draw.rect(c, (48, 28, 22), (263, 5, 52, 6))
    pygame.draw.rect(c, _mix((90, 190, 90), (255, 70, 36), heat), (263, 5, max(1, int(52 * heat)), 6))


def _notes(g):
    font = _font(g)
    for text, x, y, life, col in g.notes:
        if life <= 0:
            continue
        blit(g.canvas, font, text, int(x), int(y), col, 1, center=True)


def draw_lobby(g):
    c = g.canvas
    c.blit(g.bg, (0, 0))
    c.blit(g.veil, (0, 0))
    font = _font(g)
    bob = int(math.sin(g.t * 0.08) * 2)
    blit(c, font, tr("title"), W // 2, 14 + bob, (255, 214, 140), 2, center=True)
    ver = "V" + g.version
    vw, _vh = font.size(ver, 1)
    blit(c, font, ver, W - vw - 4, 2, (220, 170, 120), 1, shadow=False)
    blit(c, font, tr("tag"), W // 2, 36, (255, 186, 130), 1, center=True)
    for i in range(4):
        x = 8 + i * 78
        box = pygame.Rect(x, 50, 74, 78)
        pygame.draw.rect(c, (255, 232, 204), box)
        pygame.draw.rect(c, PCOLORS[i][1], box, 2)
        if i < len(g.players):
            player = g.players[i]
            draw_player(c, player, g.t, at=(x + 28, 72))
            who = label(player)
            blit(c, font, who, x + 37, 112, PCOLORS[i][0], 1, center=True)
        else:
            if (g.t // 25) % 2 == 0:
                blit(c, font, tr("press"), x + 37, 78, (140, 90, 70), 1, center=True)
            blit(c, font, tr("join"), x + 37, 94, (110, 70, 50), 1, center=True)
    ready = len(g.players) >= 2 and any(not p.cpu for p in g.players)
    hint = tr("start_hint") if ready else tr("need")
    blit(c, font, hint, W // 2, 140, (255, 220, 180), 1, center=True)
    blit(c, font, tr("cpu_hint") + "   " + tr("legend_btn"), W // 2, 154, (255, 214, 170), 1, center=True)
    blit(c, font, tr("leave_hint"), W // 2, 168, (230, 180, 140), 1, center=True)


def draw_settings(g):
    c = g.canvas
    c.blit(g.bg, (0, 0))
    c.blit(g.veil, (0, 0))
    font = _font(g)
    panel = pygame.Rect(6, 2, W - 12, 156)
    pygame.draw.rect(c, (255, 236, 214), panel)
    pygame.draw.rect(c, (120, 64, 36), panel, 2)
    blit(c, font, tr("settings"), W // 2, 8, (120, 64, 36), 1, center=True, shadow=False)
    rows = g.setting_rows()
    for i, (_key, name, value) in enumerate(rows):
        y = 24 + i * 14
        if i == g.menu_i:
            pygame.draw.rect(c, (255, 196, 120), (12, y - 1, W - 24, 14))
        ink = (60, 28, 16)
        blit(c, font, name, 18, y, ink, 1, shadow=False)
        if value:
            vw, _vh = font.size(value, 1)
            blit(c, font, value, W - 18 - vw, y, ink, 1, shadow=False)
    blit(c, font, tr("back"), W // 2, 166, (255, 236, 214), 1, center=True)


def draw_legend(g):
    c = g.canvas
    c.blit(g.bg, (0, 0))
    c.blit(g.veil, (0, 0))
    font = _font(g)
    blit(c, font, tr("legend"), W // 2, 6, (255, 220, 150), 1, center=True)
    keys = ("c_move", "c_climb", "c_loyly", "c_door", "c_avanto", "c_item", "c_score", "c_faint", "c_win")
    for i, key in enumerate(keys):
        blit(c, font, tr(key), W // 2, 22 + i * 15, (255, 236, 214), 1, center=True)
    blit(c, font, tr("back"), W // 2, 164, (255, 210, 140), 1, center=True)


def draw_count(g):
    font = _font(g)
    if g.t < 60:
        label, col = "3", (255, 120, 80)
    elif g.t < 120:
        label, col = "2", (255, 170, 70)
    elif g.t < 180:
        label, col = "1", (255, 214, 100)
    else:
        label, col = tr("go"), (255, 244, 180)
    blit(g.canvas, font, label, W // 2, 70, col, 3, center=True)
    blit(g.canvas, font, tr("hint_play"), W // 2, 164, (255, 232, 200), 1, center=True)


def draw_round_end(g):
    c = g.canvas
    c.blit(g.veil, (0, 0))
    font = _font(g)
    panel = pygame.Rect(12, 20, W - 24, 132)
    pygame.draw.rect(c, (255, 236, 214), panel)
    pygame.draw.rect(c, (120, 64, 36), panel, 2)
    winners = g.round_winners or []
    if len(winners) == 1:
        title = tr("win", label(winners[0]))
        col = PCOLORS[winners[0].idx][0]
    else:
        title, col = tr("draw"), (120, 64, 36)
    blit(c, font, title, W // 2, 28, col, 1, center=True)
    blit(c, font, tr("board"), W // 2, 42, (120, 70, 40), 1, center=True)
    order = sorted(g.players, key=lambda p: (-p.round_points, p.idx))
    for i, player in enumerate(order):
        y = 58 + i * 18
        pygame.draw.rect(c, PCOLORS[player.idx][0], (20, y + 2, 8, 8))
        blit(c, font, label(player), 32, y, (70, 36, 24), 1, shadow=False)
        line = "%d" % player.round_points
        if player.mode == "faint":
            line += " " + tr("fainted")
        blit(c, font, line, 130, y, (90, 48, 28), 1, shadow=False)
        tot = "%s %d" % (tr("total"), player.bank)
        tw, _th = font.size(tot, 1)
        blit(c, font, tot, W - 28 - tw, y, (110, 64, 40), 1, shadow=False)
    if g.t > 24 and (g.t // 20) % 2 == 0:
        blit(c, font, tr("next"), W // 2, 162, (255, 220, 170), 1, center=True)


def draw_results(g):
    c = g.canvas
    c.blit(g.bg, (0, 0))
    pygame.draw.rect(c, (32, 18, 14), (0, 0, W, 13))
    font = _font(g)
    blit(c, font, tr("results"), W // 2, 2, (255, 220, 160), 1, center=True)
    if g.players:
        champ = max(g.players, key=lambda p: (p.bank, p.wins, -p.faints, -p.idx))
        blit(c, font, tr("champ", label(champ)), W // 2, 20, PCOLORS[champ.idx][0], 1, center=True)
        draw_player(c, champ, g.t, at=(W // 2 - 6, 32))
    order = sorted(g.players, key=lambda p: (-p.bank, -p.wins, p.idx))
    panel = pygame.Rect(16, 64, W - 32, 78)
    pygame.draw.rect(c, (255, 236, 214), panel)
    pygame.draw.rect(c, (140, 80, 48), panel, 2)
    for i, player in enumerate(order):
        y = 72 + i * 16
        pygame.draw.rect(c, PCOLORS[player.idx][0], (26, y, 8, 8))
        blit(c, font, label(player), 40, y, (70, 36, 24), 1, shadow=False)
        blit(c, font, str(player.bank), 168, y, (90, 48, 28), 1, shadow=False)
        for k in range(min(3, player.wins)):
            pygame.draw.rect(c, (220, 160, 40), (230 + k * 8, y, 6, 6))
    blit(c, font, tr("rematch") + "   " + tr("back_lobby"), W // 2, 164, (255, 236, 210), 1, center=True)


def draw_pause(g):
    c = g.canvas
    c.blit(g.veil, (0, 0))
    font = _font(g)
    blit(c, font, tr("paused"), W // 2, 48, (255, 220, 150), 2, center=True)
    opts = (tr("resume"), tr("to_lobby"), tr("quit"))
    for i, label in enumerate(opts):
        y = 84 + i * 20
        if i == g.menu_i:
            pygame.draw.rect(c, (255, 210, 140), (70, y - 3, 180, 16))
        blit(c, font, label, W // 2, y, (90, 40, 28), 1, center=True)


def draw_quit(g):
    if g.quit_hold < 6:
        return
    c = g.canvas
    bw = 120
    x = W // 2 - bw // 2
    pygame.draw.rect(c, (40, 20, 24), (x, 4, bw, 10))
    pygame.draw.rect(c, (255, 236, 214), (x, 4, int(bw * min(1, g.quit_hold / 60.0)), 10))
    blit(c, _font(g), tr("quitting"), W // 2, 5, (80, 30, 24), 1, center=True)
