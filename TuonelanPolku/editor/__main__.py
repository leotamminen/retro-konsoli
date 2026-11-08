"""Launch the editor. A missing pygame install stops here with a plain message."""
import sys


def main():
    try:
        import pygame  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "pygame puuttuu.\n"
            "Asenna Python 3 ja sitten itse komennolla: py -3 -m pip install pygame\n"
            "Tämä ohjelma ei asenna mitään puolestasi.\n"
        )
        return 1
    from editor.ui import run
    return run()


if __name__ == "__main__":
    sys.exit(main())
