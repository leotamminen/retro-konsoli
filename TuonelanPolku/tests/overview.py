from lib import *
import pygame
Gd = G
S = 8
cols = len(Gd["GRID"][0]); rows = len(Gd["GRID"])
print(cols, rows)
def render(path, x0, x1):
    surf = pygame.Surface(((x1 - x0) * S, rows * S)); surf.fill((20, 22, 30))
    colr = {1: (110, 90, 70), 2: (180, 150, 90), 3: (160, 110, 60), 4: (200, 60, 60), 5: (40, 80, 160)}
    wd = Gd["World"]()
    for y in range(rows):
        for x in range(x0, x1):
            t = wd.tile(x, y)
            if t: pygame.draw.rect(surf, colr.get(t, (255, 0, 255)), ((x - x0) * S, y * S, S, S))
    f = pygame.font.Font(None, 14)
    for k, d in Gd["DYN"].items():
        for (x, y) in d["tiles"]:
            if x0 <= x < x1: pygame.draw.rect(surf, (230, 230, 80) if not d["active"] else (80, 230, 230), ((x - x0) * S, y * S, S, S), 1)
    for b, tx in Gd["BONFIRES"].items():
        if x0 <= tx < x1:
            x, y = Gd["bonfire_pos"](b); pygame.draw.circle(surf, (255, 140, 20), (int((x / 16 - x0) * S), int(y / 16 * S) - 4), 5); surf.blit(f.render(b, False, (255, 255, 255)), ((tx - x0) * S, int(y / 16 * S) - 22))
    for i, (k, tx, fr) in enumerate(Gd["SPAWNS"]):
        if x0 <= tx < x1:
            y = Gd["floor_row"](tx, fr) if k not in ("nakki",) else Gd["floor_row"](tx, fr)
            pygame.draw.rect(surf, (255, 60, 255), ((tx - x0) * S, y * S - 6, 5, 6)); surf.blit(f.render(k[:3], False, (255, 180, 255)), ((tx - x0) * S, y * S - 16))
    for k, it in Gd["ITEMS"].items() if isinstance(Gd["ITEMS"], dict) else [(i[2], i) for i in Gd["ITEMS"]]:
        pass
    for lid, lv in Gd["LEVERS"].items():
        if x0 <= lv["tx"] < x1: pygame.draw.rect(surf, (80, 255, 80), ((lv["tx"] - x0) * S, lv["ty"] * S, S, S)); surf.blit(f.render(lid, False, (80, 255, 80)), ((lv["tx"] - x0) * S, lv["ty"] * S - 10))
    pygame.image.save(surf, path)
for i, (a, b) in enumerate([(0, 150), (146, 296), (292, 446)]):
    render("/tmp/ov%d.png" % i, a, b)
