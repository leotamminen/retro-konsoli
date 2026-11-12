#!/usr/bin/env python3
"""Run the game from source on a desktop.

This loads the same modules, in the same order, with the same embedded maps,
as build.py. It does not read a generated .pygame file. Edit src/ and maps/,
then use this for a local window or build.py for the one-file release.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build


def namespace():
    version, stamp, chunks = build.pieces()
    ns = {"__name__": "tuonela_source"}
    exec(compile(stamp, "version.json", "exec"), ns)
    for name, body in chunks:
        exec(compile(body, os.path.join("src", name), "exec"), ns)
    ns["VERSION"] = version
    return ns


def main():
    ns = namespace()
    ns["main"]()


if __name__ == "__main__":
    main()
