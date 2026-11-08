"""Load, edit and save the canonical world.json and vellamo.json documents.

The game paints world rows first and then extras.blocks. Vellamo fills air
above the floor row and solid from the floor down, then paints blocks.
This module keeps those two layers. It does not invent dialogue or enemy AI.
"""
import copy
import json
from datetime import datetime
from pathlib import Path

ROWS = 44
WORLD_WIDTH = 486
VELLAMO_ORIGIN = 486
AIR, SOLID, PLAT, LADDER, THORN, WATER = 0, 1, 2, 3, 4, 5
TILE_CODES = (AIR, SOLID, PLAT, LADDER, THORN, WATER)
TILE_NAMES = {
    AIR: "ilma", SOLID: "maa", PLAT: "taso", LADDER: "tikkaat", THORN: "piikit", WATER: "vesi",
}
LAND_ENEMIES = ("peikko", "susi", "korppi", "jousi", "hukkunut", "virvatuli", "nakki", "haamu", "henki", "joutsen")
WATER_ENEMIES = ("lampi", "rapu", "poltto", "merikala", "kutri")
BOSS_KINDS = ("hiisi", "turso", "tytti", "louhi", "joukahainen", "ahti", "aino", "vellamo")
WORLD_BOSSES = ("hiisi", "turso", "tytti", "louhi")
VELLAMO_BOSSES = ("joukahainen", "ahti", "aino", "vellamo")
WORLD_BONFIRES = tuple("b%d" % i for i in range(10))
VELLAMO_BONFIRES = tuple("b%d" % i for i in range(10, 14))
ITEM_TYPES = {"souls": "int", "flask": "int", "flaskpow": "int", "charm": "str"}
ADDABLE_ITEMS = ("souls", "flask", "flaskpow")


def decode_row(spec):
    row = []
    for part in str(spec).split(","):
        if not part:
            continue
        count, code = part.split(":")
        row.extend([int(code)] * int(count))
    return row


def encode_row(cells):
    parts = []
    index = 0
    while index < len(cells):
        end = index + 1
        while end < len(cells) and cells[end] == cells[index]:
            end += 1
        parts.append("%d:%d" % (end - index, cells[index]))
        index = end
    return ",".join(parts)


def _subtract(block, x, y):
    bx, by, bw, bh, code = block
    if not (bx <= x < bx + bw and by <= y < by + bh):
        return [list(block)]
    parts = []
    if y > by:
        parts.append([bx, by, bw, y - by, code])
    if y + 1 < by + bh:
        parts.append([bx, y + 1, bw, by + bh - (y + 1), code])
    if x > bx:
        parts.append([bx, y, x - bx, 1, code])
    if x + 1 < bx + bw:
        parts.append([x + 1, y, bx + bw - (x + 1), 1, code])
    return parts


class MapDoc:
    def __init__(self, kind, data, path, original):
        self.kind = kind
        self.data = data
        self.path = Path(path)
        self.original = original
        self.undo_stack = []
        self.redo_stack = []
        self._stroke = False
        self._stroke_saved = False
        self._decode_base()

    @classmethod
    def load(cls, path):
        path = Path(path)
        original = path.read_bytes()
        data = json.loads(original.decode("utf-8"))
        kind = "vellamo" if "floor" in data and "rows" not in data else "world"
        if kind == "world" and "rows" not in data:
            raise ValueError("tuntematon kartta: %s" % path.name)
        return cls(kind, data, path, original)

    def _decode_base(self):
        if self.kind == "world":
            self.base = [decode_row(spec) for spec in self.data["rows"]]
        else:
            self.base = None

    @property
    def dirty(self):
        return json.loads(json.dumps(self.data)) != json.loads(self.original.decode("utf-8"))

    def width(self):
        if self.kind == "world":
            return len(self.base[0])
        return int(self.data["cols"])

    def height(self):
        return len(self.base) if self.kind == "world" else ROWS

    def origin_x(self):
        return 0 if self.kind == "world" else VELLAMO_ORIGIN

    def enemies(self):
        return LAND_ENEMIES if self.kind == "world" else WATER_ENEMIES

    def in_bounds(self, x, y):
        return self.origin_x() <= x < self.width() and 0 <= y < self.height()

    def area_at(self, x):
        for name, start, end in self.data.get("areas") or []:
            if start <= x < end:
                return name
        areas = self.data.get("areas") or []
        return areas[-1][0] if areas else ""

    def base_cell(self, x, y):
        if not self.in_bounds(x, y):
            return None
        if self.kind == "world":
            return self.base[y][x]
        return SOLID if y >= int(self.data["floor"]) else AIR

    def blocks(self):
        if self.kind == "world":
            return self.data.setdefault("extras", {}).setdefault("blocks", [])
        return self.data.setdefault("blocks", [])

    def cell(self, x, y):
        value = self.base_cell(x, y)
        if value is None:
            return None
        for block in self.blocks():
            bx, by, bw, bh, code = block[:5]
            if bx <= x < bx + bw and by <= y < by + bh:
                value = code
        return value

    def begin_stroke(self):
        self._stroke = True
        self._stroke_saved = False

    def end_stroke(self):
        self._stroke = False
        self._stroke_saved = False

    def _touch(self):
        if self._stroke:
            if self._stroke_saved:
                return
            self._stroke_saved = True
        self.undo_stack.append(copy.deepcopy(self.data))
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _restore(self, data):
        self.data = data
        self._decode_base()
        self.end_stroke()

    def undo(self):
        self.end_stroke()
        if not self.undo_stack:
            return False
        self.redo_stack.append(copy.deepcopy(self.data))
        self._restore(self.undo_stack.pop())
        return True

    def redo(self):
        self.end_stroke()
        if not self.redo_stack:
            return False
        self.undo_stack.append(copy.deepcopy(self.data))
        self._restore(self.redo_stack.pop())
        return True

    def paint(self, x, y, code, base=False):
        if code not in TILE_CODES:
            return False, "tuntematon maasto"
        if not self.in_bounds(x, y):
            return False, "ruutu on kartan ulkopuolella"
        if self.kind == "vellamo" and y >= int(self.data["floor"]) and code == AIR:
            return False, "Vellamon lattiaa ei puhkota ilmaksi"
        if base and self.kind == "world":
            return self._paint_base(x, y, code)
        if self.cell(x, y) == code and code == self.base_cell(x, y):
            covered = any(bx <= x < bx + bw and by <= y < by + bh for bx, by, bw, bh, _c in (b[:5] for b in self.blocks()))
            if not covered:
                return True, ""
        if self.cell(x, y) == code:
            return True, ""
        self._touch()
        kept = []
        for block in self.blocks():
            kept.extend(_subtract(block, x, y))
        if code != self.base_cell(x, y):
            kept.append([x, y, 1, 1, code])
        self.blocks()[:] = kept
        return True, ""

    def _paint_base(self, x, y, code):
        if self.base[y][x] == code and self.cell(x, y) == code:
            return True, ""
        self._touch()
        kept = []
        for block in self.blocks():
            kept.extend(_subtract(block, x, y))
        self.blocks()[:] = kept
        self.base[y][x] = code
        self.data["rows"][y] = encode_row(self.base[y])
        return True, ""

    def erase(self, x, y, base=False):
        if base and self.kind == "world":
            return self.paint(x, y, AIR, base=True)
        if not self.in_bounds(x, y):
            return False, "ruutu on kartan ulkopuolella"
        if self.cell(x, y) == self.base_cell(x, y):
            return True, ""
        return self.paint(x, y, self.base_cell(x, y), base=False)

    def move_block(self, index, dx, dy):
        blocks = self.blocks()
        if not (0 <= index < len(blocks)):
            return False
        block = blocks[index]
        nx, ny = block[0] + dx, block[1] + dy
        if not self.in_bounds(nx, ny) or not self.in_bounds(nx + block[2] - 1, ny + block[3] - 1):
            return False
        if dx == 0 and dy == 0:
            return True
        self._touch()
        block[0], block[1] = nx, ny
        return True

    def delete_block(self, index):
        blocks = self.blocks()
        if not (0 <= index < len(blocks)):
            return False
        self._touch()
        del blocks[index]
        return True

    def suggest_platform(self, x, y):
        """Propose a short platform in open air. The caller can move or delete it."""
        if not self.in_bounds(x, y):
            x = self.origin_x() + 8
            y = 20
        floor = None
        for row in range(max(0, y), self.height()):
            if self.cell(x, row) in (SOLID, PLAT):
                floor = row
                break
        if floor is None or floor < 2:
            return False, "tästä ei löydy lattiaa ehdotukselle"
        top = floor - 2
        if self.kind == "vellamo" and top >= int(self.data["floor"]):
            return False, "ehdotus osuisi Vellamon lattiaan"
        width = 4
        if x + width > self.width():
            x = self.width() - width
        for col in range(x, x + width):
            if self.cell(col, top) != AIR:
                return False, "ehdotuksen kohdalla on jo maastoa"
        self._touch()
        self.blocks().append([x, top, width, 1, PLAT])
        return True, len(self.blocks()) - 1

    def _spawn_list(self, where):
        if self.kind == "vellamo":
            return self.data.setdefault("spawns", [])
        if where == "extra":
            return self.data.setdefault("extras", {}).setdefault("spawns", [])
        return self.data.setdefault("spawns", [])

    def spawn_refs(self):
        if self.kind == "vellamo":
            return [("base", i, rec) for i, rec in enumerate(self.data.get("spawns") or [])]
        refs = [("base", i, rec) for i, rec in enumerate(self.data.get("spawns") or [])]
        refs += [("extra", i, rec) for i, rec in enumerate((self.data.get("extras") or {}).get("spawns") or [])]
        return refs

    def add_spawn(self, kind, x, y):
        if kind not in self.enemies():
            return False, "tätä vihollista ei voi lisätä tähän karttaan"
        if not self.in_bounds(x, y):
            return False, "ruutu on kartan ulkopuolella"
        if self.kind == "world" and x >= 446:
            return False, "perusmaailman vihollinen kolumnissa 446 tai sen jälkeen katoaa, kun Vellamo ladataan"
        self._touch()
        where = "base" if self.kind == "vellamo" else "extra"
        self._spawn_list(where).append([kind, x, y])
        return True, (where, len(self._spawn_list(where)) - 1)

    def move_spawn(self, where, index, dx, dy):
        items = self._spawn_list(where)
        if not (0 <= index < len(items)):
            return False
        rec = list(items[index])
        nx, ny = rec[1] + dx, rec[2] + dy
        if not self.in_bounds(nx, ny):
            return False
        if self.kind == "world" and nx >= 446:
            return False
        if dx == 0 and dy == 0:
            return True
        self._touch()
        rec[1], rec[2] = nx, ny
        items[index] = rec
        return True

    def delete_spawn(self, where, index):
        items = self._spawn_list(where)
        if not (0 <= index < len(items)):
            return False
        self._touch()
        del items[index]
        return True

    def item_refs(self):
        refs = []
        if self.kind == "world":
            for key, rec in (self.data.get("items") or {}).items():
                refs.append(("base", key, rec))
            for index, rec in enumerate((self.data.get("extras") or {}).get("items") or []):
                refs.append(("extra", index, rec))
        else:
            for index, rec in enumerate(self.data.get("items") or []):
                refs.append(("base", index, rec))
        return refs

    def _item_ids(self):
        found = set()
        for where, key, rec in self.item_refs():
            found.add(rec[0] if where == "extra" or self.kind == "vellamo" else key)
        return found

    def add_item(self, kind, x, y, amount=100):
        if kind not in ADDABLE_ITEMS:
            return False, "uusia taikoja ei luoda, koska pelissä ei ole niille tekstiä"
        if not self.in_bounds(x, y):
            return False, "ruutu on kartan ulkopuolella"
        number = 1
        while ("pouch_uusi_%d" % number) in self._item_ids() or ("pullo_uusi_%d" % number) in self._item_ids():
            number += 1
        if kind == "souls":
            ident, payload = "pouch_uusi_%d" % number, int(amount)
        else:
            ident, payload = "pullo_uusi_%d" % number, 1
        self._touch()
        if self.kind == "world":
            bucket = self.data.setdefault("extras", {}).setdefault("items", [])
            bucket.append([ident, x, y, kind, payload])
            return True, ("extra", len(bucket) - 1)
        bucket = self.data.setdefault("items", [])
        bucket.append([ident, x, y, kind, payload])
        return True, ("base", len(bucket) - 1)

    def move_item(self, where, key, dx, dy):
        rec, owner = self._item_record(where, key)
        if rec is None:
            return False
        tx, ty = (rec[1], rec[2]) if where == "extra" or self.kind == "vellamo" else (rec[0], rec[1])
        nx, ny = tx + dx, ty + dy
        if not self.in_bounds(nx, ny):
            return False
        if dx == 0 and dy == 0:
            return True
        self._touch()
        if where == "extra" or self.kind == "vellamo":
            rec[1], rec[2] = nx, ny
        else:
            rec[0], rec[1] = nx, ny
        return True

    def delete_item(self, where, key):
        if self.kind == "world" and where == "base":
            items = self.data.get("items") or {}
            if key not in items:
                return False
            self._touch()
            del items[key]
            return True
        bucket = self._item_bucket(where)
        if not (0 <= key < len(bucket)):
            return False
        self._touch()
        del bucket[key]
        return True

    def _item_bucket(self, where):
        if self.kind == "vellamo":
            return self.data.setdefault("items", [])
        if where == "extra":
            return self.data.setdefault("extras", {}).setdefault("items", [])
        return None

    def _item_record(self, where, key):
        if self.kind == "world" and where == "base":
            rec = (self.data.get("items") or {}).get(key)
            return rec, None
        bucket = self._item_bucket(where)
        if bucket is None or not (0 <= key < len(bucket)):
            return None, None
        return bucket[key], bucket

    def move_bonfire(self, ident, dx):
        fires = self.data.get("bonfires") or {}
        if ident not in fires:
            return False
        column = int(fires[ident]) + dx
        if not (self.origin_x() <= column < self.width()):
            return False
        if dx == 0:
            return True
        self._touch()
        fires[ident] = column
        areas = self.data.get("bonfire_area")
        if isinstance(areas, dict) and ident in areas:
            areas[ident] = self.area_at(column)
        return True

    def arenas(self):
        raw = self.data.get("arenas")
        if self.kind == "vellamo":
            return [(rec[0], rec[1], rec[2]) for rec in raw or []]
        return [(key, rec.get("x0"), rec.get("x1")) for key, rec in (raw or {}).items()]

    def move_arena_edge(self, name, edge, dx):
        if dx == 0:
            return True
        if self.kind == "vellamo":
            rec = next((item for item in self.data.get("arenas") or [] if item[0] == name), None)
            if rec is None:
                return False
            x0, x1 = rec[1] + (dx if edge == "left" else 0), rec[2] + (dx if edge == "right" else 0)
            if not self._arena_span_ok(name, x0, x1):
                return False
            self._touch()
            rec[1], rec[2] = x0, x1
            return True
        rec = (self.data.get("arenas") or {}).get(name)
        if not isinstance(rec, dict):
            return False
        x0 = rec["x0"] + (dx if edge == "left" else 0)
        x1 = rec["x1"] + (dx if edge == "right" else 0)
        if not self._arena_span_ok(name, x0, x1):
            return False
        self._touch()
        old0, old1 = rec["x0"], rec["x1"]
        rec["x0"], rec["x1"] = x0, x1
        self._shift_door(rec, "door_in", old0, x0, "d_%s_in" % name)
        self._shift_door(rec, "door_out", old1, x1, "d_%s_out" % name)
        return True

    def _arena_span_ok(self, name, x0, x1):
        if x1 - x0 < 8:
            return False
        if x0 < self.origin_x() or x1 > self.width():
            return False
        for other, left, right in self.arenas():
            if other == name:
                continue
            if not (x1 <= left or right <= x0):
                return False
        return True

    def _shift_door(self, arena, field, old, new, dyn_key):
        door = arena.get(field)
        if not isinstance(door, list) or not door or door[0] != old:
            return
        door[0] = new
        dyn = (self.data.get("dyn") or {}).get(dyn_key)
        if not isinstance(dyn, dict):
            return
        for tile in dyn.get("tiles") or []:
            if isinstance(tile, list) and tile and tile[0] == old:
                tile[0] = new

    def validate(self):
        errors = []
        if self.kind == "world":
            self._validate_world(errors)
        else:
            self._validate_vellamo(errors)
        self._validate_common(errors)
        return errors

    def _validate_world(self, errors):
        rows = self.data.get("rows")
        if not isinstance(rows, list) or len(rows) != ROWS:
            errors.append("perusmaailmassa pitää olla %d korkeusjuovaa" % ROWS)
            return
        widths = []
        for index, spec in enumerate(rows):
            try:
                decoded = decode_row(spec)
            except (TypeError, ValueError):
                errors.append("juova %d ei ole tiivistetty rivi" % index)
                return
            if any(code not in TILE_CODES for code in decoded):
                errors.append("juovassa %d on tuntematon maasto" % index)
            widths.append(len(decoded))
        if len(set(widths)) != 1 or widths[0] != WORLD_WIDTH:
            errors.append("perusmaailman leveys ei ole %d" % WORLD_WIDTH)
        self._validate_areas(errors, 0, WORLD_WIDTH)
        self._require_names(errors, self.data.get("bonfires"), WORLD_BONFIRES, "nuotio")
        self._require_names(errors, self.data.get("arenas"), WORLD_BOSSES, "areena")
        for ident, column in (self.data.get("bonfires") or {}).items():
            if not isinstance(column, int) or not (0 <= column < WORLD_WIDTH):
                errors.append("nuotio %s on kartan ulkopuolella" % ident)
        for name, rec in (self.data.get("arenas") or {}).items():
            if not isinstance(rec, dict):
                errors.append("areena %s on rikki" % name)
                continue
            if rec.get("door_in") and rec["door_in"][0] != rec.get("x0"):
                errors.append("areenan %s vasen ovi irtosi rajasta" % name)
            if rec.get("door_out") and rec["door_out"][0] != rec.get("x1"):
                errors.append("areenan %s oikea ovi irtosi rajasta" % name)

    def _validate_vellamo(self, errors):
        cols = self.data.get("cols")
        floor = self.data.get("floor")
        if not isinstance(cols, int) or cols <= VELLAMO_ORIGIN:
            errors.append("Vellamon leveys on rikki")
            return
        if not isinstance(floor, int) or not (1 <= floor < ROWS):
            errors.append("Vellamon lattiarivi on rikki")
        self._validate_areas(errors, VELLAMO_ORIGIN, cols)
        self._require_names(errors, self.data.get("bonfires"), VELLAMO_BONFIRES, "nuotio")
        names = [rec[0] for rec in self.data.get("arenas") or [] if isinstance(rec, list) and rec]
        for boss in VELLAMO_BOSSES:
            if boss not in names:
                errors.append("areena puuttuu: %s" % boss)
        for rec in self.data.get("arenas") or []:
            if not (isinstance(rec, list) and len(rec) >= 3):
                errors.append("Vellamon areenarivi on rikki")
                continue
            if rec[2] - rec[1] < 8 or rec[1] < VELLAMO_ORIGIN or rec[2] > cols:
                errors.append("areena %s on rajojen ulkopuolella" % rec[0])
        for block in self.data.get("blocks") or []:
            if len(block) < 5:
                continue
            if block[1] + block[3] > floor and block[4] == AIR:
                errors.append("ilmalohko puhkoisi Vellamon lattian")

    def _validate_areas(self, errors, start, end):
        areas = self.data.get("areas")
        if not isinstance(areas, list) or not areas:
            errors.append("alueet puuttuvat")
            return
        cursor = start
        for rec in areas:
            if not (isinstance(rec, (list, tuple)) and len(rec) >= 3):
                errors.append("aluerivi on rikki")
                return
            if rec[1] != cursor or rec[2] <= rec[1]:
                errors.append("alueet eivät ole yhtenäiset")
                return
            cursor = rec[2]
        if cursor != end:
            errors.append("alueet eivät kata karttaa")

    def _require_names(self, errors, container, names, label):
        keys = set(container or [])
        for name in names:
            if name not in keys:
                errors.append("%s puuttuu: %s" % (label, name))

    def _validate_common(self, errors):
        for block in self.blocks():
            if len(block) < 5:
                errors.append("lohko on rikki")
                continue
            x, y, w, h, code = block[:5]
            if code not in TILE_CODES or w < 1 or h < 1:
                errors.append("lohkossa on virheellinen maasto")
            if not self.in_bounds(x, y) or not self.in_bounds(x + w - 1, y + h - 1):
                errors.append("lohko on kartan ulkopuolella")
        seen = set()
        for _where, _key, rec in self.spawn_refs():
            if len(rec) < 3 or rec[0] in BOSS_KINDS or rec[0] not in self.enemies():
                errors.append("vihollinen ei kuulu tähän karttaan: %s" % (rec[0] if rec else "?"))
            elif not self.in_bounds(rec[1], rec[2]):
                errors.append("vihollinen on kartan ulkopuolella")
            elif self.kind == "world" and rec[1] >= 446:
                errors.append("perusmaailman vihollinen ei saa olla kolumnissa 446 tai sen jälkeen")
        idents = []
        for where, key, rec in self.item_refs():
            if where == "extra" or self.kind == "vellamo":
                if len(rec) < 5:
                    errors.append("esine on rikki")
                    continue
                ident, tx, ty, kind, payload = rec[0], rec[1], rec[2], rec[3], rec[4]
            else:
                if len(rec) < 4:
                    errors.append("esine on rikki")
                    continue
                ident, tx, ty, kind, payload = key, rec[0], rec[1], rec[2], rec[3]
            idents.append(ident)
            if kind not in ITEM_TYPES:
                errors.append("esineen %s lajia ei tueta" % ident)
            elif ITEM_TYPES[kind] == "int" and not isinstance(payload, int):
                errors.append("esineen %s määrä ei ole luku" % ident)
            elif ITEM_TYPES[kind] == "str" and not isinstance(payload, str):
                errors.append("taian %s tunniste on rikki" % ident)
            elif not self.in_bounds(tx, ty):
                errors.append("esine %s on kartan ulkopuolella" % ident)
        if len(idents) != len(set(idents)):
            errors.append("esineillä on sama tunniste")
        columns = list((self.data.get("bonfires") or {}).values())
        if len(columns) != len(set(columns)):
            errors.append("kaksi nuotiota on samassa kolumnissa")
        previous = self.origin_x()
        for name, left, right in self.arenas():
            if left is None or right is None or right <= left:
                errors.append("areena %s on rikki" % name)
            elif left < previous:
                errors.append("areenat menevät päällekkäin")
            previous = right

    def dumps(self):
        return json.dumps(self.data, ensure_ascii=False, indent=2) + "\n"

    def save(self, path=None, backup=True):
        path = Path(path or self.path)
        errors = self.validate()
        if errors:
            return False, errors
        payload = self.original if not self.dirty else self.dumps().encode("utf-8")
        if path.exists() and path.read_bytes() == payload:
            return True, []
        if backup and path.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            folder = path.parent / "backups"
            folder.mkdir(parents=True, exist_ok=True)
            dest = folder / ("%s-%s%s" % (path.stem, stamp, path.suffix))
            suffix = 1
            while dest.exists():
                dest = folder / ("%s-%s-%d%s" % (path.stem, stamp, suffix, path.suffix))
                suffix += 1
            dest.write_bytes(path.read_bytes())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        if path.resolve() == self.path.resolve():
            self.original = payload
        return True, []
