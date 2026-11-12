#!/usr/bin/env python3
"""Build one pygame file from the source modules.

version.json is the only version. It names TuonelanPolku<version>.pygame and
is embedded once, before the modules. maps/world.json and maps/vellamo.json
are embedded before the modules that read them. The game does not open those
JSON files at runtime.

ORDER is the dependency order. The build fails if a source file is missing,
if an extra module is not listed, if a required module is out of order, if a
module rebinds a class method, or if the entrypoint is not last.
"""
import ast, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")

# Load order. A name may use names defined by every module above it.
ORDER = [
    "font.py",
    "core.py",
    "audio.py",
    "world.py",
    "physics.py",
    "art.py",
    "scenery.py",
    "boss_art.py",
    "entities.py",
    "enemies.py",
    "bosses.py",
    "player.py",
    "session.py",
    "ui.py",
    "text.py",
    "app.py",
    "vellamo_world.py",
    "vellamo_art.py",
    "vellamo_music.py",
    "vellamo_bosses.py",
    "vellamo_mobs.py",
    "vellamo_text.py",
    "map_chart.py",
    "map_draw.py",
    "vellamo_scenery.py",
    "vellamo_strings.py",
    "release_text.py",
    "entry.py",
]

# module -> modules that must already have been loaded
REQUIRES = {
    "core.py": ["font.py"],
    "audio.py": ["core.py"],
    "world.py": ["core.py"],
    "physics.py": ["core.py", "world.py"],
    "art.py": ["core.py"],
    "scenery.py": ["art.py"],
    "boss_art.py": ["art.py"],
    "entities.py": ["physics.py", "art.py"],
    "enemies.py": ["entities.py"],
    "bosses.py": ["enemies.py", "boss_art.py"],
    "player.py": ["entities.py", "physics.py"],
    "session.py": ["player.py", "bosses.py", "world.py"],
    "ui.py": ["session.py"],
    "text.py": ["core.py"],
    "app.py": ["ui.py", "session.py"],
    "vellamo_world.py": ["world.py"],
    "vellamo_art.py": ["boss_art.py"],
    "vellamo_music.py": ["audio.py"],
    "vellamo_bosses.py": ["bosses.py", "entities.py"],
    "vellamo_mobs.py": ["enemies.py"],
    "vellamo_text.py": ["text.py"],
    "map_chart.py": ["ui.py", "world.py"],
    "map_draw.py": ["ui.py", "map_chart.py"],
    "vellamo_scenery.py": ["scenery.py"],
    "vellamo_strings.py": ["text.py"],
    "release_text.py": ["text.py"],
    "entry.py": ["app.py"],
}

EMBED_BEFORE = {
    "world.py": ("WORLD_LAYOUT", "world.json"),
    "vellamo_world.py": ("VELLAMO_LAYOUT", "vellamo.json"),
}

CLASS_NAMES = {
    "GameCore", "GameUI", "Player", "Enemy", "Mob", "Proj", "Zone",
    "Boss", "WaterBoss", "Body", "World",
}


def fail(msg):
    sys.exit("build failed: " + msg)


def check_order():
    present = sorted(f for f in os.listdir(SRC) if f.endswith(".py"))
    if present != sorted(ORDER):
        missing = sorted(set(ORDER) - set(present))
        extra = sorted(set(present) - set(ORDER))
        fail("source list does not match ORDER (missing %s, extra %s)" % (missing, extra))
    if ORDER[-1] != "entry.py":
        fail("entry.py must be the last module")
    index = {name: i for i, name in enumerate(ORDER)}
    for name, deps in REQUIRES.items():
        if name not in index:
            fail("required module is not in ORDER: " + name)
        for dep in deps:
            if dep not in index:
                fail("%s requires missing module %s" % (name, dep))
            if index[dep] >= index[name]:
                fail("%s requires %s earlier in ORDER" % (name, dep))


def check_module(name, body):
    if re.search(r"^VERSION\s*=", body, re.M):
        fail("%s assigns VERSION; version.json is the only source" % name)
    try:
        tree = ast.parse(body, filename=name)
    except SyntaxError as exc:
        fail("%s: %s" % (name, exc))
    defined = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.append(node.name)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                    if target.value.id in CLASS_NAMES or target.value.id[:1].isupper():
                        fail("%s rebinds %s.%s after the class" % (name, target.value.id, target.attr))
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            func = call.func
            if isinstance(func, ast.Name) and func.id == "setattr" and call.args:
                arg = call.args[0]
                if isinstance(arg, ast.Name) and arg.id[:1].isupper():
                    fail("%s uses setattr to rebind %s" % (name, arg.id))
    dupes = sorted({n for n in defined if defined.count(n) > 1})
    if dupes:
        fail("%s defines %s more than once" % (name, ", ".join(dupes)))


def load_version():
    path = os.path.join(HERE, "version.json")
    try:
        version = json.load(open(path, encoding="utf-8"))["version"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        fail("version.json: %s" % exc)
    if not re.match(r"\d+\.\d+\.\d+$", version):
        fail("version.json must be a plain x.y.z string")
    return version


def pieces(maps_dir=None):
    """Return (version, stamp, chunks) in ORDER, with maps embedded."""
    check_order()
    version = load_version()
    stamp = 'VERSION = "%s"\n' % version
    maps_dir = maps_dir or os.path.join(HERE, "maps")
    chunks = []
    for name in ORDER:
        path = os.path.join(SRC, name)
        if name in EMBED_BEFORE:
            const, filename = EMBED_BEFORE[name]
            map_path = os.path.join(maps_dir, filename)
            if not os.path.isfile(map_path):
                fail("missing map " + map_path)
            data = json.load(open(map_path, encoding="utf-8"))
            chunks.append((filename, "%s = %s\n" % (const, repr(data))))
        body = open(path, encoding="utf-8").read()
        check_module(name, body)
        if not body.endswith("\n"):
            body += "\n"
        chunks.append((name, body))
    return version, stamp, chunks


def assemble(version, stamp, chunks):
    parts = ["# Built by TuonelanPolku/build.py from version.json %s. Do not edit this file by hand.\n" % version, stamp]
    for name, body in chunks:
        parts.append("\n# ======== %s ========\n" % name)
        parts.append(body)
    text = "".join(parts)
    if text.count('if __name__ == "__main__":') != 1:
        fail("release must contain exactly one entrypoint")
    if text.count(stamp.strip()) != 1:
        fail("VERSION must be embedded exactly once")
    if text.rfind('if __name__ == "__main__":') < text.rfind("\nclass "):
        fail("entrypoint is not after the class definitions")
    return text


def shipped_path(version):
    return os.path.join(HERE, "TuonelanPolku%s.pygame" % version)


def is_shipped_release(path):
    """A pygame file that already lives next to the source is a release. Do not replace it."""
    folder = os.path.abspath(HERE)
    target = os.path.abspath(path)
    name = os.path.basename(target)
    return os.path.dirname(target) == folder and name.startswith("TuonelanPolku") and name.endswith(".pygame") and os.path.isfile(target)


def parse_args(argv):
    replace = False
    check = False
    maps_dir = None
    positional = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--replace":
            replace = True
        elif arg == "--check":
            check = True
        elif arg == "--maps":
            i += 1
            if i >= len(argv):
                fail("usage: build.py [--check|--replace] [--maps DIR] [output.pygame]")
            maps_dir = argv[i]
        elif arg.startswith("-"):
            fail("unknown option " + arg)
        else:
            positional.append(arg)
        i += 1
    if len(positional) > 1:
        fail("usage: build.py [--check|--replace] [--maps DIR] [output.pygame]")
    return replace, check, maps_dir, (positional[0] if positional else None)


def main(argv=None):
    replace, check, maps_dir, requested = parse_args(list(sys.argv[1:] if argv is None else argv))
    version, stamp, chunks = pieces(maps_dir)
    text = assemble(version, stamp, chunks)
    default_out = shipped_path(version)
    if check:
        if maps_dir:
            fail("--check compares the canonical maps with the shipped file")
        if not os.path.isfile(default_out):
            fail("missing shipped file " + default_out)
        existing = open(default_out, encoding="utf-8").read()
        if existing != text:
            fail("source would change %s. Bump version.json and build a new filename, or pass an explicit output path." % default_out)
        print("unchanged", default_out, os.path.getsize(default_out), "bytes")
        return
    out = requested or default_out
    if maps_dir and os.path.abspath(out) == os.path.abspath(default_out):
        fail("refusing to write the versioned release from --maps. Choose another filename.")
    if os.path.isfile(out):
        existing = open(out, encoding="utf-8").read()
        if existing == text:
            print("unchanged", out, os.path.getsize(out), "bytes")
            return
        if is_shipped_release(out) and not replace:
            fail("refusing to overwrite shipped release %s. Write a new filename, or bump version.json." % out)
        if not replace and os.path.basename(out).startswith("TuonelanPolku") and out.endswith(".pygame"):
            fail("refusing to change %s under an existing release name. Pass a new filename." % out)
    parent = os.path.dirname(os.path.abspath(out))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(text)
    print("built", out, len(ORDER), "modules", os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
