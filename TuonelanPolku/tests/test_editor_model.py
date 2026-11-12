"""Map document roundtrip, validation, undo and backups. Does not touch shipped maps."""
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from editor.model import AIR, PLAT, SOLID, MapDoc

ROOT = Path(__file__).resolve().parents[1]
FAIL = []


def req(ok, name):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        FAIL.append(name)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="editor_model_"))
    try:
        body(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if FAIL:
        print("EDITOR MODEL FAIL", len(FAIL))
        sys.exit(1)
    print("OK editor model")


def body(tmp):
    for name in ("world.json", "vellamo.json"):
        raw = (ROOT / "maps" / name).read_bytes()
        copy = tmp / name
        copy.write_bytes(raw)
        doc = MapDoc.load(copy)
        req(doc.validate() == [], name + " validates")
        req(not doc.dirty, name + " loads clean")
        other = tmp / ("copy-" + name)
        ok, errors = doc.save(other, backup=False)
        req(ok and errors == [] and other.read_bytes() == raw, name + " clean save is byte-identical")

    world_raw = (ROOT / "maps" / "world.json").read_bytes()
    world_path = tmp / "edit-world.json"
    world_path.write_bytes(world_raw)
    doc = MapDoc.load(world_path)
    original_rows = list(doc.data["rows"])
    req(doc.cell(8, 28) == AIR, "sample cell starts as air")
    doc.begin_stroke()
    ok, _note = doc.paint(8, 28, PLAT)
    doc.paint(9, 28, PLAT)
    doc.end_stroke()
    req(ok and doc.cell(8, 28) == PLAT and doc.cell(9, 28) == PLAT, "overlay paint")
    req(doc.data["rows"] == original_rows, "overlay paint keeps every run-length row")
    doc.data["zz_keep"] = {"ä": 1, "n": 2}
    doc.data["arenas"]["hiisi"]["huomio"] = "säilyy"
    ok, errors = doc.save(world_path)
    req(ok and errors == [], "dirty save " + " ".join(errors))
    saved = json.loads(world_path.read_text(encoding="utf-8"))
    req(saved["zz_keep"] == {"ä": 1, "n": 2}, "unknown top-level field kept")
    req(saved["arenas"]["hiisi"]["huomio"] == "säilyy", "unknown arena field kept")
    req(saved["rows"] == original_rows, "saved rows still the original run-length")
    backups = list((world_path.parent / "backups").glob("edit-world-*.json"))
    req(len(backups) == 1 and backups[0].read_bytes() == world_raw, "backup is the previous file")

    broken = MapDoc.load(world_path)
    before = world_path.read_bytes()
    broken.data["spawns"][0][0] = "lohikäärme"
    ok, errors = broken.save(world_path)
    req((not ok) and errors and world_path.read_bytes() == before, "invalid enemy does not overwrite")

    fresh = MapDoc.load(tmp / "copy-world.json")
    fresh.paint(10, 10, SOLID, base=True)
    req(fresh.data["rows"][10] != original_rows[10], "base brush rewrites one row")
    req(fresh.data["rows"][:10] == original_rows[:10] and fresh.data["rows"][11:] == original_rows[11:], "other rows stay exact")
    fresh.undo()
    req(fresh.data["rows"][10] == original_rows[10], "undo restores the row")
    fresh.redo()
    req(fresh.base_cell(10, 10) == SOLID, "redo paints the base again")
    fresh.undo()

    mover = MapDoc.load(tmp / "copy-world.json")
    block = list(mover.blocks()[0])
    req(mover.move_block(0, 2, 0), "block moves")
    req(mover.blocks()[0][0] == block[0] + 2 and mover.blocks()[0][1] == block[1], "block origin updated")
    req(mover.delete_block(0), "block deletes")
    mover.undo()
    req(mover.blocks()[0][0] == block[0] + 2, "undo delete keeps the move")
    old = mover.data["arenas"]["hiisi"]["x0"]
    tiles = [list(tile) for tile in mover.data["dyn"]["d_hiisi_in"]["tiles"]]
    out_tiles = [list(tile) for tile in mover.data["dyn"]["d_hiisi_out"]["tiles"]]
    req(mover.move_arena_edge("hiisi", "left", 2), "arena edge moves")
    req(mover.data["arenas"]["hiisi"]["x0"] == old + 2, "arena x0 follows")
    req(mover.data["arenas"]["hiisi"]["door_in"][0] == old + 2, "door column follows the edge")
    req(mover.data["dyn"]["d_hiisi_in"]["tiles"][0][0] == tiles[0][0] + 2, "gate tiles follow the edge")
    req(mover.data["dyn"]["d_hiisi_out"]["tiles"] == out_tiles, "far door stays put")
    req(not mover.move_arena_edge("hiisi", "right", -30), "arena refuses to collapse")
    ok, info = mover.add_spawn("lampi", 20, 10)
    req(not ok, "water enemy refused on the base map")
    ok, info = mover.add_spawn("peikko", 20, 10)
    req(ok and mover.data["extras"]["spawns"][-1][:3] == ["peikko", 20, 10], "new enemy keeps its type")
    req(mover.move_spawn("extra", len(mover.data["extras"]["spawns"]) - 1, 1, 0), "enemy moves")
    req(mover.delete_spawn("extra", len(mover.data["extras"]["spawns"]) - 1), "enemy deletes")
    ok, info = mover.add_item("souls", 21, 28, 140)
    ident = mover.data["extras"]["items"][-1][0]
    req(ok and ident.startswith("pouch_uusi_") and ident not in json.loads(world_raw)["items"], "new item gets a fresh id")
    req(not mover.add_item("charm", 22, 28)[0], "new charm is refused")
    req(mover.move_item("base", "c_moss", 1, 0), "existing charm moves and keeps its id")
    req("c_moss" in mover.data["items"], "charm id remains")
    req(not mover.add_spawn("peikko", 450, 10)[0], "spawn past column 446 is refused")

    vraw = (ROOT / "maps" / "vellamo.json").read_bytes()
    vpath = tmp / "vellamo.json"
    vpath.write_bytes(vraw)
    vdoc = MapDoc.load(vpath)
    comment = vdoc.data["comment"]
    floor = vdoc.data["floor"]
    req(vdoc.cell(500, floor) == SOLID, "vellamo floor starts solid")
    ok, note = vdoc.paint(500, floor, AIR)
    req(ok and vdoc.cell(500, floor) == AIR, "air removes the visible Vellamo floor")
    vdoc.undo()
    req(vdoc.cell(500, floor) == SOLID, "undo restores the floor")
    ok, _note = vdoc.paint(490, 5, PLAT)
    vdoc.data["tekijä"] = "testi"
    req(ok and vdoc.cell(490, 5) == PLAT, "Vellamo platform block")
    req(vdoc.data["comment"] == comment, "comment kept in memory")
    ok, errors = vdoc.save(vpath)
    loaded = json.loads(vpath.read_text(encoding="utf-8"))
    req(ok and loaded["comment"] == comment and loaded["tekijä"] == "testi", "Vellamo unknown field and comment saved")
    req(loaded["floor"] == 43 and loaded["cols"] == 1326, "floor and width stay")
    vdoc.undo()
    req(vdoc.cell(490, 5) == vdoc.base_cell(490, 5), "undo removes the Vellamo paint")
    spawn_before = [list(rec) for _w, _i, rec in vdoc.spawn_refs()]
    box = next(item for item in vdoc.arena_boxes() if item[0] == "joukahainen")
    req(vdoc.move_arena("joukahainen", 4, 1), "whole arena moves")
    moved = next(item for item in vdoc.arena_boxes() if item[0] == "joukahainen")
    req(moved[1] == box[1] + 4 and moved[4] == box[4] + 1, "arena x and ground both move")
    req([list(rec) for _w, _i, rec in vdoc.spawn_refs()] == spawn_before, "arena move leaves spawns")
    req(vdoc.resize_arena("joukahainen", "right", 3), "arena resize handle")
    req(next(item for item in vdoc.arena_boxes() if item[0] == "joukahainen")[2] == moved[2] + 3, "right edge follows the handle")
    req(vdoc.delete_blocked("bonfire", "b10"), "bonfire deletion explains itself")
    req(vdoc.delete_blocked("arena", "joukahainen"), "arena deletion explains itself")
    vdoc.erase(500, vdoc.data["floor"])
    notes = vdoc.warnings()
    ok, errors = vdoc.save(tmp / "warn-vellamo.json")
    req(ok and errors == [] and notes, "creative warning does not block save")
    world = MapDoc.load(tmp / "copy-world.json")
    hid = world.data["arenas"]["hiisi"]["ground"]
    req(world.move_arena("hiisi", 0, 2), "world arena moves vertically")
    req(world.data["arenas"]["hiisi"]["ground"] == hid + 2, "boss ground follows")
    req(world.data["arenas"]["hiisi"]["door_in"][2] == hid + 2, "door bottom follows")
    req(world.data["dyn"]["d_hiisi_in"]["tiles"][-1][1] == hid + 1, "door tiles follow the new ground")
    missing = subprocess.run([sys.executable, "-c", textwrap.dedent("""
        import sys
        sys.modules["pygame"] = None
        sys.path.insert(0, %r)
        from editor.__main__ import main
        raise SystemExit(main())
    """ % str(ROOT))], capture_output=True, text=True)
    req(missing.returncode == 1 and "pygame puuttuu" in missing.stderr and "ei asenna" in missing.stderr, "missing pygame explains itself")


if __name__ == "__main__":
    main()
