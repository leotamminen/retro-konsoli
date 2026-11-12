"""Static ownership checks and the hashes of every older release.

The behavioral comparison with 1.3.4 is the rest of the suite. This file
checks that the source still owns its methods and that no older file moved.
"""
import ast, hashlib, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
import build

FAIL = []

def req(ok, name):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        FAIL.append(name)

build.check_order()
req(True, "ORDER matches src and dependencies")

CLASS_NAMES = build.CLASS_NAMES
for name in build.ORDER:
    body = (ROOT / "src" / name).read_text(encoding="utf-8")
    tree = ast.parse(body, filename=name)
    rebound = []
    defined = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defined.append(node.name)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                    if target.value.id in CLASS_NAMES or target.value.id[:1].isupper():
                        rebound.append("%s.%s" % (target.value.id, target.attr))
    req(not rebound, name + " does not rebind a class")
    req(len(defined) == len(set(defined)), name + " has one definition per name")

req((ROOT / "src" / "entry.py").read_text(encoding="utf-8").count('if __name__ == "__main__":') == 1, "one source entrypoint")
req("VERSION" not in (ROOT / "src" / "core.py").read_text(encoding="utf-8").split("version.json")[0], "core does not own the version string")

OLD = {
    ROOT / "TuonelanPolku1.0.pygame": "950843c4499053f96cc9f1cb9f7363987176a4162d3f4d8436dc1f6af86c8917",
    ROOT / "TuonelanPolku1.1.pygame": "b2a1de60f64fd85bff2ccf624b52bf297fc68d778ff080f3cf7d568e2152acf5",
    ROOT / "TuonelanPolku1.2.pygame": "9fb3ee86127ece8d26e66e3c0817bf4476f5e537b222a22a251a4887f1169622",
    ROOT / "TuonelanPolku1.3.pygame": "e2dfc11f0ef80874cb5311a31617de6e567f79c1a60435e8081c662680c16956",
    ROOT / "TuonelanPolku1.3.1.pygame": "0af9d21b03899c5c01de5fc22192ea045c1aa71bf2a43b3a162443c86e9cce55",
    ROOT / "TuonelanPolku1.3.2.pygame": "0c11d1f41f1336ced887763bcf3d3e8d4648955929813c48be4ddb9dbbf7c09a",
    ROOT / "TuonelanPolku1.3.3.pygame": "a45e64ef4f6719488ff7296edceaec3ff37a341986fe57d3d75666fd00e192cc",
    ROOT / "TuonelanPolku1.3.4.pygame": "0b78cd857a40d11d78c1ec11fe751d655aa9f0a96b6d29371acbd551568f698b",
    REPO / "HyppyUkot" / "Hyppyukot1.0.pygame": "433007ec222d8cb648c83852a2470ac3d8ead41bae2f3c0e40c7664e8ff9af73",
    REPO / "HyppyUkot" / "Hyppyukot1.1.pygame": "2c0fb3944f3160dd3d21bad21947f4a818671d2020d0444ca9829853338ed98b",
    REPO / "HyppyUkot" / "Hyppyukot1.2.pygame": "da75c6c9b1ea063edb8b3bb15cf98d45cffdc8b6cf790ffd090f85cf3be67af9",
    REPO / "HyppyUkot" / "Hyppyukot1.2.1.pygame": "2bed6c916ac93c815b221d71c10e9265141a915a6393518463aa3c7a3cc87757",
}
for path, expect in OLD.items():
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    req(digest == expect, "unchanged " + path.name)

version = build.load_version()
built = ROOT / ("TuonelanPolku%s.pygame" % version)
req(built.is_file(), "built " + built.name)
text = built.read_text(encoding="utf-8")
req(text.count('if __name__ == "__main__":') == 1, "built file has one entrypoint")
req(text.count('VERSION = "%s"' % version) == 1, "built file has one version")
req("WORLD_LAYOUT = " in text and "VELLAMO_LAYOUT = " in text, "both maps are embedded")
req("GameCore.on_boss_dead =" not in text and "Player.phys =" not in text, "built file has no method rebinding")

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ns = {}
exec(compile(text, str(built), "exec"), ns)
OWNED = (
    ("GameCore", "start_session"), ("GameCore", "start_boss"), ("GameCore", "on_boss_dead"),
    ("GameCore", "draw_world"), ("GameCore", "draw_light"), ("GameCore", "hazard"),
    ("GameCore", "enter_vellamo"), ("GameCore", "begin_ng"), ("GameCore", "update_area"),
    ("GameUI", "title_items"), ("GameUI", "up_title"), ("GameUI", "build_map"),
    ("GameUI", "dr_map"), ("GameUI", "up_info"), ("GameUI", "dr_aino_reveal"),
    ("Player", "phys"), ("Player", "fire_arrow"), ("Player", "fire_spell"),
    ("Enemy", "draw"), ("Mob", "brain"), ("Mob", "draw"),
    ("Proj", "update"), ("Zone", "update"),
)
for cls, meth in OWNED:
    fn = getattr(ns[cls], meth)
    req(getattr(fn, "__qualname__", "") == "%s.%s" % (cls, meth), "%s.%s is the class method" % (cls, meth))
req(ns["render_track"].__name__ == "render_track", "one render_track")
req(ns["VERSION"] == version, "loaded version matches version.json")

if FAIL:
    print("AUDIT FAIL", len(FAIL))
    sys.exit(1)
print("AUDIT OK")
