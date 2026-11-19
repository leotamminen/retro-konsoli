# The only version number lives in ../version.json. The release build
# rewrites load_version() so the single-file game does not need the json.
import json
import os


def load_version():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(os.path.dirname(here), "version.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    version = str(data["version"]).strip()
    if not version:
        raise RuntimeError("version.json has an empty version")
    return version
