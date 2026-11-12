"""Finnish pygame view of the map documents."""
import os
from pathlib import Path

import pygame

import json

from editor import EDITOR_VERSION
from editor.model import (
    AIR, SOLID, PLAT, LADDER, THORN, WATER, TILE_NAMES, MapDoc,
)
from editor.preview import build_preview

TILE_COLOR = {
    SOLID: (78, 108, 72),
    PLAT: (164, 116, 64),
    LADDER: (150, 108, 68),
    THORN: (176, 64, 72),
    WATER: (48, 96, 168),
}
ENEMY_COLOR = {
    "peikko": (120, 150, 80), "susi": (150, 150, 150), "korppi": (70, 70, 80),
    "jousi": (150, 120, 70), "hukkunut": (70, 110, 90), "virvatuli": (80, 160, 220),
    "nakki": (60, 140, 120), "haamu": (140, 140, 180), "henki": (100, 180, 160),
    "joutsen": (200, 200, 210), "lampi": (140, 210, 190), "rapu": (170, 90, 60),
    "poltto": (40, 120, 130), "merikala": (40, 140, 160), "kutri": (150, 170, 210),
}


def load_font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        if os.path.isfile(path):
            return pygame.font.Font(path, size)
    return pygame.font.SysFont("segoeui,arial,freesans,dejavusans", size)


class EditorApp:
    def __init__(self, screen, root):
        self.screen = screen
        self.root = Path(root)
        self.docs = {
            "world": MapDoc.load(self.root / "maps" / "world.json"),
            "vellamo": MapDoc.load(self.root / "maps" / "vellamo.json"),
        }
        self.map_id = "world"
        self.zoom = 8
        self.cam_x = 0.0
        self.cam_y = 16.0
        self.tool = "select"
        self.tile = PLAT
        self.enemy = "peikko"
        self.item_kind = "souls"
        self.selection = None
        self.drag = None
        self.message = "Valitse-tila: vasen napsautus. Delete tai Poista valittu poistaa. Maalaa muotoilee maata."
        self.help = False
        self.running = True
        self.font = load_font(13)
        self.widgets = []

    @property
    def doc(self):
        return self.docs[self.map_id]

    def viewport(self):
        width, height = self.screen.get_size()
        return pygame.Rect(0, 28, width - 188, height - 64)

    def cell_to_screen(self, tx, ty):
        view = self.viewport()
        return (
            view.x + (tx - self.cam_x) * self.zoom,
            view.y + (ty - self.cam_y) * self.zoom,
        )

    def screen_to_cell(self, sx, sy):
        view = self.viewport()
        return (
            int((self.cam_x + (sx - view.x) / self.zoom) // 1),
            int((self.cam_y + (sy - view.y) / self.zoom) // 1),
        )

    def _switch_map(self, ident):
        self.map_id = ident
        self.selection = None
        self.enemy = self.doc.enemies()[0]
        self.cam_x = float(self.doc.origin_x())
        self.cam_y = 12.0

    def _layout(self):
        view = self.viewport()
        x = view.right + 8
        y = 32
        widgets = []

        def add(label, action, color=(36, 44, 52), width=172, height=14):
            nonlocal y
            rect = pygame.Rect(x, y, width, height)
            widgets.append((rect, action, label, color))
            y += height + 1

        add("Maailma", ("map", "world"), (70, 90, 60) if self.map_id == "world" else (36, 44, 52))
        add("Vellamo", ("map", "vellamo"), (40, 90, 110) if self.map_id == "vellamo" else (36, 44, 52))
        y += 4
        add("Valitse", ("tool", "select"), (210, 170, 40) if self.tool == "select" else (36, 44, 52))
        add("Maalaa", ("tool", "paint"), (90, 70, 40) if self.tool == "paint" else (36, 44, 52))
        add("Pyyhi", ("tool", "erase"), (90, 70, 40) if self.tool == "erase" else (36, 44, 52))
        add("Poista valittu", ("delete",), (150, 48, 42) if self._selection_alive() else (70, 40, 40))
        if self.map_id == "world":
            add("Pohjajuova", ("tool", "base"), (90, 70, 40) if self.tool == "base" else (36, 44, 52))
        add("Ehdota tasannetta", ("tool", "suggest"), (36, 44, 52))
        y += 4
        for code, label in ((SOLID, "Maa"), (PLAT, "Taso"), (WATER, "Vesi"), (LADDER, "Tikkaat"), (THORN, "Piikit"), (AIR, "Ilma")):
            add(label, ("tile", code), TILE_COLOR.get(code, (28, 32, 38)) if self.tile == code else (36, 44, 52))
        y += 4
        for kind in self.doc.enemies():
            add(kind, ("enemy", kind), ENEMY_COLOR.get(kind, (80, 80, 80)) if self.enemy == kind else (36, 44, 52))
        y += 4
        add("Uusi sielupussi", ("item", "souls"), (120, 100, 40) if self.item_kind == "souls" else (36, 44, 52))
        add("Uusi pullo", ("item", "flask"), (80, 140, 160) if self.item_kind == "flask" else (36, 44, 52))
        y += 4
        add("Tallenna", ("save",), (50, 80, 50))
        add("Kumoa", ("undo",), (50, 50, 70))
        add("Tee uudelleen", ("redo",), (50, 50, 70))
        add("Esikatsele peli", ("preview",), (70, 60, 40))
        self.widgets = widgets

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN:
            self._key(event)
            return
        if event.type == pygame.MOUSEWHEEL:
            self._zoom(1 if event.y > 0 else -1, pygame.mouse.get_pos())
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._down(event)
            return
        if event.type == pygame.MOUSEMOTION:
            self._motion(event)
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
            self.doc.end_stroke()
            self.drag = None

    def _key(self, event):
        ctrl = bool(event.mod & pygame.KMOD_CTRL)
        shift = bool(event.mod & pygame.KMOD_SHIFT)
        if ctrl and event.key == pygame.K_z:
            self.doc.undo()
            self.selection = None
            self.message = "Kumottu."
            return
        if ctrl and event.key in (pygame.K_y, pygame.K_x):
            self.doc.redo()
            self.selection = None
            self.message = "Tehty uudelleen."
            return
        if ctrl and event.key == pygame.K_s:
            self._save()
            return
        if ctrl and event.key == pygame.K_q:
            self.running = False
            self.message = "Suljettu tallentamatta."
            return
        if event.key == pygame.K_F1:
            self.help = not self.help
            return
        if event.key == pygame.K_TAB:
            self._switch_map("vellamo" if self.map_id == "world" else "world")
            return
        if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self._zoom(1, (self.viewport().centerx, self.viewport().centery))
            return
        if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self._zoom(-1, (self.viewport().centerx, self.viewport().centery))
            return
        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
            self.tile = (SOLID, PLAT, WATER, LADDER, THORN, AIR)[event.key - pygame.K_1]
            return
        step = 4
        if shift and self.selection:
            delta = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1)}.get(event.key)
            if delta:
                self.doc.begin_stroke()
                self._move_selection(delta[0], delta[1])
                self.doc.end_stroke()
                return
        if event.key == pygame.K_LEFT:
            self.cam_x -= step
        elif event.key == pygame.K_RIGHT:
            self.cam_x += step
        elif event.key == pygame.K_UP:
            self.cam_y -= step
        elif event.key == pygame.K_DOWN:
            self.cam_y += step
        elif event.key == pygame.K_DELETE:
            self._delete_selection()
        elif event.key == pygame.K_ESCAPE:
            if self.selection or self.help:
                self.selection = None
                self.help = False
            else:
                self.message = "Esc ei tallenna. Ctrl+S tallentaa. Ctrl+Q lopettaa tallentamatta."
        self.cam_x = max(self.doc.origin_x() - 2, min(self.cam_x, self.doc.width() - 4))
        self.cam_y = max(-2, min(self.cam_y, self.doc.height() - 4))

    def _zoom(self, direction, pos):
        before = self.screen_to_cell(*pos) if self.viewport().collidepoint(pos) else None
        self.zoom = min(18, max(4, self.zoom + direction * 2))
        if before:
            sx, sy = pos
            view = self.viewport()
            self.cam_x = before[0] - (sx - view.x) / self.zoom
            self.cam_y = before[1] - (sy - view.y) / self.zoom

    def _down(self, event):
        if event.button == 2 or (event.button == 1 and pygame.key.get_mods() & pygame.KMOD_ALT):
            self.drag = ("pan", event.pos, self.cam_x, self.cam_y)
            return
        for rect, action, _label, _color in self.widgets:
            if rect.collidepoint(event.pos):
                self._widget(action)
                return
        if not self.viewport().collidepoint(event.pos):
            return
        cell = self.screen_to_cell(*event.pos)
        if event.button == 3 or self.tool == "select":
            self.selection = self._pick(cell)
            if self.selection:
                self.drag = ("move", cell)
                self.doc.begin_stroke()
                self.message = "Valittu. Delete tai Poista valittu poistaa. Shift+nuoli tai raahaus siirtää."
            else:
                self.message = "Ei valittavaa ruudussa %d,%d." % cell
            return
        if self.tool == "suggest":
            ok, info = self.doc.suggest_platform(*cell)
            self.message = "Ehdotus on valittuna. Siirrä tai poista se." if ok else info
            if ok:
                self.selection = ("block", info)
                self.tool = "select"
            return
        if self.tool == "item":
            ok, info = self.doc.add_item(self.item_kind, *cell)
            self.message = "Esine lisätty." if ok else info
            if ok:
                self.selection = ("item", info[0], info[1])
            return
        if self.tool == "enemy":
            ok, info = self.doc.add_spawn(self.enemy, *cell)
            self.message = "Vihollinen lisätty. Tämä ei luo uutta tekoälyä." if ok else info
            if ok:
                self.selection = ("spawn", info[0], info[1])
            return
        self.doc.begin_stroke()
        self.drag = ("paint",)
        self._apply_brush(cell)

    def _motion(self, event):
        if not self.drag:
            return
        if self.drag[0] == "pan":
            _kind, origin, cam_x, cam_y = self.drag
            self.cam_x = cam_x - (event.pos[0] - origin[0]) / self.zoom
            self.cam_y = cam_y - (event.pos[1] - origin[1]) / self.zoom
            return
        if not self.viewport().collidepoint(event.pos):
            return
        cell = self.screen_to_cell(*event.pos)
        if self.drag[0] == "paint":
            self._apply_brush(cell)
            return
        if self.drag[0] == "move" and self.selection:
            previous = self.drag[1]
            dx, dy = cell[0] - previous[0], cell[1] - previous[1]
            if dx or dy:
                if self._move_selection(dx, dy):
                    self.drag = ("move", cell)

    def _widget(self, action):
        kind = action[0]
        if kind == "map":
            self._switch_map(action[1])
        elif kind == "tool":
            if action[1] == "suggest":
                center = (int(self.cam_x + 8), int(self.cam_y + 8))
                ok, info = self.doc.suggest_platform(*center)
                self.message = "Ehdotus on valittuna. Siirrä tai poista se." if ok else info
                if ok:
                    self.selection = ("block", info)
                    self.tool = "select"
            else:
                self.tool = action[1]
                self.message = {
                    "select": "Valitse-tila päällä. Vasen napsautus valitsee. Delete tai Poista valittu poistaa.",
                    "paint": "Maalaa muuttaa näkyvän ruudun. Vellamon lattian voi pyyhkiä ilmaksi.",
                    "erase": "Pyyhi poistaa näkyvän ruudun, myös perustan.",
                    "base": "Pohjajuova kirjoittaa tiivistetyn perusrivin. Tavallinen pyyhkiminen ei koske siihen.",
                }.get(self.tool, self.message)
        elif kind == "delete":
            self._delete_selection()
        elif kind == "tile":
            self.tile = action[1]
            self.tool = "paint"
        elif kind == "enemy":
            self.enemy = action[1]
            self.tool = "enemy"
            self.message = "Vihollinen käyttää pelin valmista käytöstä. Uutta dialogia tai tekoälyä ei voi kirjoittaa."
        elif kind == "item":
            self.item_kind = action[1]
            self.tool = "item"
            self.message = "Uusi esine saa oman tunnisteen. Taikoja ei luoda, olemassa olevia voi siirtää."
        elif kind == "save":
            self._save()
        elif kind == "undo":
            self.doc.undo()
            self.selection = None
        elif kind == "redo":
            self.doc.redo()
            self.selection = None
        elif kind == "preview":
            self._preview()

    def _apply_brush(self, cell):
        base = self.tool == "base"
        if self.tool == "erase":
            ok, note = self.doc.erase(*cell, base=False)
        else:
            ok, note = self.doc.paint(*cell, self.tile, base=base)
        if not ok:
            self.message = note

    def _move_selection(self, dx, dy):
        kind = self.selection[0]
        moved = False
        if kind == "block":
            moved = self.doc.move_block(self.selection[1], dx, dy)
        elif kind == "spawn":
            moved = self.doc.move_spawn(self.selection[1], self.selection[2], dx, dy)
        elif kind == "item":
            moved = self.doc.move_item(self.selection[1], self.selection[2], dx, dy)
        elif kind == "bonfire":
            moved = self.doc.move_bonfire(self.selection[1], dx) if dy == 0 else False
        elif kind == "arena":
            edge = self.selection[2]
            if edge == "body":
                moved = self.doc.move_arena(self.selection[1], dx, dy)
            elif edge in ("left", "right") and dx:
                moved = self.doc.resize_arena(self.selection[1], edge, dx)
            elif edge in ("top", "bottom") and dy:
                moved = self.doc.resize_arena(self.selection[1], edge, dy)
            else:
                moved = True
        elif kind == "tile":
            self.message = "Ruutua ei siirretä. Pyyhi tai maalaa sitä."
            return False
        if not moved:
            self.message = "Siirto ei onnistu rajojen tai areenan takia."
        return moved

    def _delete_selection(self):
        if not self._selection_alive():
            self.selection = None
            self.message = "Ei valintaa. Vaihda Valitse-tilaan ja napsauta kohdetta."
            return
        kind = self.selection[0]
        blocked = self.doc.delete_blocked(kind, self.selection[1] if len(self.selection) > 1 else "")
        if blocked:
            self.message = blocked
            return
        self.doc.begin_stroke()
        if kind == "block":
            self.doc.delete_block(self.selection[1])
        elif kind == "spawn":
            self.doc.delete_spawn(self.selection[1], self.selection[2])
        elif kind == "item":
            self.doc.delete_item(self.selection[1], self.selection[2])
        elif kind == "tile":
            self.doc.erase(self.selection[1], self.selection[2])
        self.doc.end_stroke()
        self.selection = None
        self.message = "Poistettu. Ctrl+Z peruu."

    def _pick(self, cell):
        x, y = cell
        for where, index, rec in reversed(self.doc.spawn_refs()):
            if rec[1] == x and rec[2] == y:
                return ("spawn", where, index)
        for where, key, rec in reversed(self.doc.item_refs()):
            tx, ty = (rec[1], rec[2]) if where == "extra" or self.doc.kind == "vellamo" else (rec[0], rec[1])
            if tx == x and ty == y:
                return ("item", where, key)
        for ident, column in (self.doc.data.get("bonfires") or {}).items():
            if column == x and abs(self._ground(column) - y) <= 1:
                return ("bonfire", ident)
        box = None
        for name, left, right, top, ground in self.doc.arena_boxes():
            if left <= x < right and top <= y <= ground:
                box = (name, left, right, top, ground)
                break
        if box:
            name, left, right, top, ground = box
            if x == left:
                return ("arena", name, "left")
            if x == right - 1:
                return ("arena", name, "right")
            if y == top:
                return ("arena", name, "top")
            if y == ground:
                return ("arena", name, "bottom")
        blocks = self.doc.blocks()
        for index in range(len(blocks) - 1, -1, -1):
            bx, by, bw, bh = blocks[index][:4]
            if bx <= x < bx + bw and by <= y < by + bh:
                return ("block", index)
        if box and self.doc.cell(x, y) == AIR:
            return ("arena", box[0], "body")
        if self.doc.in_bounds(x, y):
            return ("tile", x, y)
        return None

    def _ground(self, column):
        for row in range(self.doc.height()):
            if self.doc.cell(column, row) in (SOLID, PLAT):
                return row
        return self.doc.height() - 1

    def _selection_alive(self):
        sel = self.selection
        if not sel:
            return False
        kind = sel[0]
        try:
            if kind == "block":
                return 0 <= sel[1] < len(self.doc.blocks())
            if kind == "spawn":
                return 0 <= sel[2] < len(self.doc._spawn_list(sel[1]))
            if kind == "item":
                return self.doc._item_record(sel[1], sel[2])[0] is not None
            if kind == "bonfire":
                return sel[1] in (self.doc.data.get("bonfires") or {})
            if kind == "arena":
                return any(box[0] == sel[1] for box in self.doc.arena_boxes())
            if kind == "tile":
                return self.doc.in_bounds(sel[1], sel[2])
        except (IndexError, KeyError, TypeError):
            return False
        return False

    def _describe(self, selection):
        if not selection:
            return "Ei valintaa."
        kind = selection[0]
        if kind == "spawn":
            rec = self.doc._spawn_list(selection[1])[selection[2]]
            return "Valittu vihollinen %s, ruutu %d,%d. Delete poistaa spawnin. Uutta tekoälyä ei kirjoiteta." % (rec[0], rec[1], rec[2])
        if kind == "item":
            return "Valittu esine. Delete poistaa sen. Tunniste säilyy siirrossa."
        if kind == "bonfire":
            return "Valittu nuotio %s. Sitä ei voi poistaa, koska peli vaatii tunnisteen. Shift+nuoli siirtää." % selection[1]
        if kind == "arena":
            box = next(item for item in self.doc.arena_boxes() if item[0] == selection[1])
            edge = {"body": "koko huone", "left": "vasen reuna", "right": "oikea reuna", "top": "yläreuna", "bottom": "alareuna"}.get(selection[2], selection[2])
            return "Valittu pomohuone %s (%s), x %d–%d, maa %d. Keskusta siirtää, reunat muuttavat kokoa. Muut esineet eivät liiku." % (box[0], edge, box[1], box[2], box[4])
        if kind == "block":
            block = self.doc.blocks()[selection[1]]
            return "Valittu maalohko %d,%d koko %dx%d. Delete poistaa lohkon." % (block[0], block[1], block[2], block[3])
        if kind == "tile":
            code = self.doc.cell(selection[1], selection[2])
            source = "lohko" if code != self.doc.base_cell(selection[1], selection[2]) else "perusta"
            return "Valittu ruutu %d,%d: %s (%s). Delete pyyhkii näkyvän maan." % (selection[1], selection[2], TILE_NAMES.get(code, "?"), source)
        return "Valinta."

    def _save(self):
        ok, errors = self.doc.save()
        if ok:
            self.message = "Tallennettu. Varmuuskopio on maps/backups-kansiossa, jos tiedosto muuttui."
        else:
            self.message = errors[0]

    def _preview(self):
        if any(doc.dirty for doc in self.docs.values()):
            self.message = "Esikatselu käyttää tallennettua karttaa. Tallenna ensin Ctrl+S."
            return
        ok, note, dest = build_preview(self.root)
        if ok:
            self.message = "Esikatselu %s on peliversio %s ja sisältää maaston tuen. Julkaistua tiedostoa ei korvattu." % (dest.name, self._game_version())
        else:
            self.message = note.splitlines()[-1] if note else "Esikatselu epäonnistui."

    def draw(self):
        self._layout()
        screen = self.screen
        screen.fill((16, 20, 26))
        view = self.viewport()
        clip = screen.get_clip()
        screen.set_clip(view)
        x0 = max(self.doc.origin_x(), int(self.cam_x) - 1)
        y0 = max(0, int(self.cam_y) - 1)
        x1 = min(self.doc.width(), int(self.cam_x + view.w / self.zoom) + 2)
        y1 = min(self.doc.height(), int(self.cam_y + view.h / self.zoom) + 2)
        for ty in range(y0, y1):
            for tx in range(x0, x1):
                code = self.doc.cell(tx, ty)
                sx, sy = self.cell_to_screen(tx, ty)
                rect = pygame.Rect(int(sx), int(sy), self.zoom, self.zoom)
                if code in TILE_COLOR:
                    pygame.draw.rect(screen, TILE_COLOR[code], rect)
                    if code != self.doc.base_cell(tx, ty):
                        pygame.draw.rect(screen, (230, 210, 140), rect, 1)
                elif self.zoom >= 8:
                    pygame.draw.rect(screen, (28, 34, 42), rect, 1)
        for name, left, right in self.doc.arenas():
            top = self.cell_to_screen(left, 2)
            bottom = self.cell_to_screen(right, self.doc.height())
            pygame.draw.rect(screen, (220, 80, 70), pygame.Rect(int(top[0]), int(top[1]), max(2, int(bottom[0] - top[0])), max(2, int(bottom[1] - top[1]))), 1)
        for where, index, rec in self.doc.spawn_refs():
            sx, sy = self.cell_to_screen(rec[1], rec[2])
            pygame.draw.circle(screen, ENEMY_COLOR.get(rec[0], (200, 200, 200)), (int(sx + self.zoom / 2), int(sy + self.zoom / 2)), max(2, self.zoom // 3))
        for where, key, rec in self.doc.item_refs():
            tx, ty = (rec[1], rec[2]) if where == "extra" or self.doc.kind == "vellamo" else (rec[0], rec[1])
            sx, sy = self.cell_to_screen(tx, ty)
            pygame.draw.rect(screen, (230, 190, 70), (int(sx + 1), int(sy + 1), max(2, self.zoom - 2), max(2, self.zoom - 2)))
        for ident, column in (self.doc.data.get("bonfires") or {}).items():
            row = max(0, self._ground(column) - 1)
            sx, sy = self.cell_to_screen(column, row)
            pygame.draw.polygon(screen, (255, 140, 50), [(sx + self.zoom / 2, sy), (sx + self.zoom, sy + self.zoom), (sx, sy + self.zoom)])
        levers = (self.doc.data.get("levers") or {}) if self.doc.kind == "world" else {}
        for rec in levers.values():
            sx, sy = self.cell_to_screen(rec["tx"], rec["ty"])
            pygame.draw.line(screen, (180, 180, 190), (sx, sy + self.zoom), (sx + self.zoom / 2, sy), 2)
        if not self._selection_alive():
            self.selection = None
        else:
            self._draw_selection(screen)
        screen.set_clip(clip)
        pygame.draw.rect(screen, (12, 14, 18), (view.right, 0, 188, screen.get_height()))
        for rect, _action, label, color in self.widgets:
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (180, 180, 170), rect, 1)
            screen.blit(self.font.render(label, True, (245, 245, 235)), (rect.x + 4, rect.y + 1))
        title = "Maailma" if self.map_id == "world" else "Vellamo"
        dirty = "muokattu" if self.doc.dirty else "tallessa"
        screen.blit(self.font.render("Editori %s  %s  %s  zoom %d  peli %s" % (EDITOR_VERSION, title, dirty, self.zoom, self._game_version()), True, (240, 230, 200)), (8, 6))
        screen.blit(self.font.render(self.message[:120], True, (220, 220, 210)), (8, screen.get_height() - 44))
        status = self._describe(self.selection) if self.selection else "Ei valintaa. Valitse-tila ja vasen napsautus. Delete tai Poista valittu poistaa."
        screen.blit(self.font.render(status[:120], True, (255, 220, 80)), (8, screen.get_height() - 24))
        if self.help:
            self._help()

    def _help(self):
        panel = pygame.Surface((520, 250), pygame.SRCALPHA)
        panel.fill((8, 10, 14, 230))
        lines = [
            "Valitse-tila: vasen napsautus. Keltainen kehys näyttää valinnan.",
            "Delete ja Poista valittu poistavat. Nuotiota ja pomohuonetta ei poisteta, syy näkyy.",
            "Pomohuoneen tyhjä keskusta siirtää huoneen. Reunat muuttavat kokoa. Ovet seuraavat.",
            "Viholliset, esineet ja maasto eivät liiku huoneen mukana.",
            "Pyyhi ja Delete ruudulla poistavat näkyvän maan, myös Vellamon lattian.",
            "Pohjajuova kirjoittaa tiivistetyn rivin. Tavallinen pyyhintä lisää ilmalohkon.",
            "Ctrl+S tallentaa ja tekee varmuuskopion. Sulkeminen ei tallenna.",
            "Esikatselu on uusi pelitiedosto, jossa on tämä editorin vaatima tuki. Vanhaa julkaisua ei korvata.",
        ]
        for index, line in enumerate(lines):
            panel.blit(self.font.render(line, True, (235, 235, 225)), (12, 12 + index * 28))
        self.screen.blit(panel, (16, 40))

    def _game_version(self):
        try:
            return json.loads((self.root / "version.json").read_text(encoding="utf-8"))["version"]
        except (OSError, json.JSONDecodeError, KeyError):
            return "?"

    def _draw_selection(self, screen):
        sel = self.selection
        color = (255, 220, 40)
        if sel[0] == "tile":
            sx, sy = self.cell_to_screen(sel[1], sel[2])
            pygame.draw.rect(screen, color, pygame.Rect(int(sx), int(sy), self.zoom, self.zoom), 3)
            return
        if sel[0] == "block":
            block = self.doc.blocks()[sel[1]]
            sx, sy = self.cell_to_screen(block[0], block[1])
            pygame.draw.rect(screen, color, pygame.Rect(int(sx), int(sy), block[2] * self.zoom, block[3] * self.zoom), 3)
            return
        if sel[0] == "arena":
            box = next(item for item in self.doc.arena_boxes() if item[0] == sel[1])
            _name, x0, x1, y0, ground = box
            sx, sy = self.cell_to_screen(x0, y0)
            pygame.draw.rect(screen, color, pygame.Rect(int(sx), int(sy), (x1 - x0) * self.zoom, (ground - y0 + 1) * self.zoom), 3)
            for hx, hy in ((x0, y0), (x1 - 1, y0), (x0, ground), (x1 - 1, ground)):
                px, py = self.cell_to_screen(hx, hy)
                pygame.draw.rect(screen, (255, 80, 40), pygame.Rect(int(px), int(py), self.zoom, self.zoom))
            return
        if sel[0] == "spawn":
            rec = self.doc._spawn_list(sel[1])[sel[2]]
            sx, sy = self.cell_to_screen(rec[1], rec[2])
        elif sel[0] == "bonfire":
            column = int(self.doc.data["bonfires"][sel[1]])
            sx, sy = self.cell_to_screen(column, max(0, self._ground(column) - 1))
        elif sel[0] == "item":
            rec = self.doc._item_record(sel[1], sel[2])[0]
            tx, ty = (rec[1], rec[2]) if sel[1] == "extra" or self.doc.kind == "vellamo" else (rec[0], rec[1])
            sx, sy = self.cell_to_screen(tx, ty)
        else:
            return
        pygame.draw.rect(screen, color, pygame.Rect(int(sx) - 2, int(sy) - 2, self.zoom + 4, self.zoom + 4), 3)

    def save_png(self, path):
        self.draw()
        pygame.image.save(self.screen, str(path))


def run(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    pygame.init()
    pygame.display.set_caption("Tuonelan polku — kenttäeditori")
    screen = pygame.display.set_mode((960, 540))
    app = EditorApp(screen, root)
    clock = pygame.time.Clock()
    while app.running:
        for event in pygame.event.get():
            app.handle(event)
        app.draw()
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    return 0
