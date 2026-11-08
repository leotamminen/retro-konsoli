"""Synthetic pygame events against the editor view. Headless, not a Windows session."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from editor.model import PLAT, WATER
from editor.ui import EditorApp

ROOT = Path(__file__).resolve().parents[1]
FAIL = []


def req(ok, name):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        FAIL.append(name)


def event(kind, **fields):
    return pygame.event.Event(kind, fields)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="editor_ui_"))
    pygame.init()
    try:
        body(tmp)
    finally:
        pygame.quit()
        shutil.rmtree(tmp, ignore_errors=True)
    if FAIL:
        print("EDITOR UI FAIL", len(FAIL))
        sys.exit(1)
    print("OK editor ui")


def copy_maps(dest):
    (dest / "maps").mkdir(parents=True)
    for name in ("world.json", "vellamo.json"):
        shutil.copy(ROOT / "maps" / name, dest / "maps" / name)


def body(tmp):
    shot_root = tmp / "shot"
    copy_maps(shot_root)
    screen = pygame.display.set_mode((960, 540))
    app = EditorApp(screen, shot_root)
    app.draw()
    world_png = Path("/tmp/editori_maailma.png")
    app.save_png(world_png)
    ground = screen.get_at((int(app.cell_to_screen(10, 30)[0]) + 2, int(app.cell_to_screen(10, 30)[1]) + 2))
    sky = screen.get_at((int(app.cell_to_screen(10, 18)[0]) + 2, int(app.cell_to_screen(10, 18)[1]) + 2))
    palette = screen.get_at((app.viewport().right + 20, 40))
    req(ground[1] > sky[1] + 20, "screenshot shows forest ground, not an empty sky")
    req(palette != ground, "palette is drawn beside the map")
    req(world_png.stat().st_size > 8000, "world screenshot file")
    app._switch_map("vellamo")
    app.cam_x = 500
    app.cam_y = 8
    app.zoom = 8
    app.draw()
    vellamo_png = Path("/tmp/editori_vellamo.png")
    app.save_png(vellamo_png)
    water = app.cell_to_screen(528, 19)
    sample = screen.get_at((int(water[0]) + 2, int(water[1]) + 2))
    req(sample[2] > 80, "Vellamo screenshot shows the pool")
    req(vellamo_png.stat().st_size > 8000, "vellamo screenshot file")

    edit_root = tmp / "edit"
    copy_maps(edit_root)
    app = EditorApp(screen, edit_root)
    app.draw()
    before = app.screen_to_cell(*app.cell_to_screen(5, 6))
    req(before == (5, 6), "cell converts back from its own screen point")
    app.zoom = 16
    again = app.screen_to_cell(*[int(v) + 1 for v in app.cell_to_screen(5, 6)])
    req(again == (5, 6), "zoom keeps the same cell under its screen point")
    app.cam_x = 4
    app.cam_y = 2
    shifted = app.screen_to_cell(*[int(v) + 1 for v in app.cell_to_screen(12, 20)])
    req(shifted == (12, 20), "pan keeps the same cell under its screen point")

    app = EditorApp(screen, edit_root)
    app.zoom = 8
    app.cam_x = 0
    app.cam_y = 16
    app.draw()
    water_button = next(rect for rect, action, label, _color in app.widgets if action == ("tile", WATER))
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=water_button.center, button=1))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=water_button.center, button=1))
    req(app.tile == WATER and app.tool == "paint", "palette click selects water")
    point = tuple(int(v) + app.zoom // 2 for v in app.cell_to_screen(8, 28))
    app.tile = PLAT
    app.tool = "paint"
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=point, button=1))
    app.handle(event(pygame.MOUSEMOTION, pos=(point[0] + app.zoom, point[1]), buttons=(1, 0, 0), rel=(app.zoom, 0)))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=(point[0] + app.zoom, point[1]), button=1))
    req(app.doc.cell(8, 28) == PLAT and app.doc.cell(9, 28) == PLAT, "drag paints two cells")
    req(app.doc.data["rows"] == json_rows(edit_root), "UI paint does not rewrite run-length rows")
    app.handle(event(pygame.KEYDOWN, key=pygame.K_z, mod=pygame.KMOD_CTRL, unicode="z"))
    req(app.doc.cell(8, 28) != PLAT, "ctrl+z undoes the stroke")
    app.handle(event(pygame.KEYDOWN, key=pygame.K_y, mod=pygame.KMOD_CTRL, unicode="y"))
    req(app.doc.cell(8, 28) == PLAT, "ctrl+y redoes the stroke")

    cam = app.cam_x
    app.handle(event(pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0, unicode=""))
    req(app.cam_x > cam, "right arrow pans")
    panned = app.cam_x
    zoom = app.zoom
    app.handle(event(pygame.MOUSEWHEEL, x=0, y=1, precise_x=0.0, precise_y=1.0, flipped=False))
    req(app.zoom > zoom, "wheel zooms in")
    origin = (120, 160)
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=origin, button=2))
    app.handle(event(pygame.MOUSEMOTION, pos=(origin[0] - 24, origin[1]), buttons=(0, 1, 0), rel=(-24, 0)))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=(origin[0] - 24, origin[1]), button=2))
    req(app.cam_x != panned, "middle mouse pans")

    enemy_button = next(rect for rect, action, _label, _color in app.widgets if action == ("enemy", "susi"))
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=enemy_button.center, button=1))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=enemy_button.center, button=1))
    spawn_at = tuple(int(v) + 1 for v in app.cell_to_screen(22, 27))
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=spawn_at, button=1))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=spawn_at, button=1))
    req(any(rec[0] == "susi" and rec[1] == 22 for _w, _i, rec in app.doc.spawn_refs()), "click places the selected enemy")
    app.tool = "select"
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=spawn_at, button=1))
    app.handle(event(pygame.MOUSEMOTION, pos=(spawn_at[0] + app.zoom, spawn_at[1]), buttons=(1, 0, 0), rel=(app.zoom, 0)))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=(spawn_at[0] + app.zoom, spawn_at[1]), button=1))
    req(any(rec[0] == "susi" and rec[1] == 23 for _w, _i, rec in app.doc.spawn_refs()), "drag moves the enemy")
    before = sum(1 for _w, _i, rec in app.doc.spawn_refs() if rec[0] == "susi")
    app.handle(event(pygame.KEYDOWN, key=pygame.K_DELETE, mod=0, unicode=""))
    after = sum(1 for _w, _i, rec in app.doc.spawn_refs() if rec[0] == "susi")
    req(after == before - 1 and not any(rec[0] == "susi" and rec[1] == 23 for _w, _i, rec in app.doc.spawn_refs()), "delete removes the enemy")

    app.tool = "select"
    app.zoom = 8
    app.cam_x = 0
    app.cam_y = 16
    app.draw()
    floor_at = tuple(int(v) + 1 for v in app.cell_to_screen(10, 32))
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=floor_at, button=1))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=floor_at, button=1))
    req(app.selection and app.selection[0] == "tile" and "Valittu ruutu" in app._describe(app.selection), "left click in select mode selects the tile")
    app.handle(event(pygame.KEYDOWN, key=pygame.K_DELETE, mod=0, unicode=""))
    req(app.doc.cell(10, 32) == 0 and app.selection is None, "delete key erases the selected floor tile")
    solid_at = tuple(int(v) + 1 for v in app.cell_to_screen(11, 32))
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=solid_at, button=1))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=solid_at, button=1))
    remove = next(rect for rect, action, _label, _color in app.widgets if action == ("delete",))
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=remove.center, button=1))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=remove.center, button=1))
    req(app.doc.cell(11, 32) == 0, "Poista valittu erases the selected tile")
    app.handle(event(pygame.KEYDOWN, key=pygame.K_z, mod=pygame.KMOD_CTRL, unicode="z"))
    req(app.doc.cell(11, 32) != 0, "undo restores the deleted tile")
    fire = tuple(int(v) + 1 for v in app.cell_to_screen(5, app._ground(5) - 1))
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=fire, button=1))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=fire, button=1))
    req(app.selection and app.selection[0] == "bonfire", "bonfire can be selected")
    app._delete_selection()
    req("ei voi poistaa" in app.message and "b0" in app.doc.data["bonfires"], "bonfire deletion explains why and keeps the id")

    app._switch_map("vellamo")
    app.tool = "select"
    app.zoom = 4
    app.cam_x = 540
    app.cam_y = 0
    app.draw()
    arena_before = next(item for item in app.doc.arena_boxes() if item[0] == "joukahainen")
    spawns_before = [tuple(rec) for _w, _i, rec in app.doc.spawn_refs()]
    center = tuple(int(v) + 1 for v in app.cell_to_screen((arena_before[1] + arena_before[2]) // 2, 8))
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=center, button=1))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=center, button=1))
    req(app.selection == ("arena", "joukahainen", "body"), "empty arena interior selects the whole room")
    app.handle(event(pygame.MOUSEMOTION, pos=(center[0] + app.zoom * 4, center[1]), buttons=(1, 0, 0), rel=(app.zoom * 4, 0)))
    # motion without a fresh press does nothing; press, drag, release
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=center, button=1))
    app.handle(event(pygame.MOUSEMOTION, pos=(center[0] + app.zoom * 4, center[1]), buttons=(1, 0, 0), rel=(app.zoom * 4, 0)))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=(center[0] + app.zoom * 4, center[1]), button=1))
    arena_after = next(item for item in app.doc.arena_boxes() if item[0] == "joukahainen")
    req(arena_after[1] == arena_before[1] + 4, "dragging the room moves it by four columns")
    req([tuple(rec) for _w, _i, rec in app.doc.spawn_refs()] == spawns_before, "room drag does not move spawns")
    edge = tuple(int(v) + 1 for v in app.cell_to_screen(arena_after[2] - 1, 10))
    app.handle(event(pygame.MOUSEBUTTONDOWN, pos=edge, button=1))
    app.handle(event(pygame.MOUSEMOTION, pos=(edge[0] + app.zoom * 2, edge[1]), buttons=(1, 0, 0), rel=(app.zoom * 2, 0)))
    app.handle(event(pygame.MOUSEBUTTONUP, pos=(edge[0] + app.zoom * 2, edge[1]), button=1))
    req(next(item for item in app.doc.arena_boxes() if item[0] == "joukahainen")[2] == arena_after[2] + 2, "right handle resizes the room")
    app._switch_map("world")
    app.cam_x = 0
    app.cam_y = 16
    app.zoom = 8
    app.tool = "select"
    app.draw()

    target = edit_root / "maps" / "world.json"
    raw = target.read_bytes()
    app.handle(event(pygame.QUIT))
    req(not app.running and target.read_bytes() == raw, "closing does not save")
    app.running = True
    app.doc.data["spawns"][0][0] = "ei_ole"
    app._save()
    req(target.read_bytes() == raw, "invalid document is not written")


def json_rows(root):
    import json
    return json.loads((root / "maps" / "world.json").read_text(encoding="utf-8"))["rows"]


if __name__ == "__main__":
    main()
