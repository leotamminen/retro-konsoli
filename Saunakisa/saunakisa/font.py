# Tuonelan polku's hand-drawn bitmap font, from this same repo (p0_font.py).
# No third-party license: the glyphs were drawn for these games.
# Spec per glyph: "accent | body | descender", rows separated by spaces.
# Tall caps (9px) stay readable on a TV once the 320x180 picture is scaled up.
import pygame

_GL = {
 "A": "|.###. #...# #...# ##### #...# #...# #...#|", "B": "|####. #...# #...# ####. #...# #...# ####.|",
 "C": "|.###. #...# #.... #.... #.... #...# .###.|", "D": "|####. #...# #...# #...# #...# #...# ####.|",
 "E": "|##### #.... #.... ####. #.... #.... #####|", "F": "|##### #.... #.... ####. #.... #.... #....|",
 "G": "|.###. #...# #.... #.### #...# #...# .####|", "H": "|#...# #...# #...# ##### #...# #...# #...#|",
 "I": "|### .#. .#. .#. .#. .#. ###|", "J": "|..### ...#. ...#. ...#. ...#. #..#. .##..|",
 "K": "|#...# #..#. #.#.. ##... #.#.. #..#. #...#|", "L": "|#.... #.... #.... #.... #.... #.... #####|",
 "M": "|#...# ##.## #.#.# #.#.# #...# #...# #...#|", "N": "|#...# ##..# ##..# #.#.# #..## #..## #...#|",
 "O": "|.###. #...# #...# #...# #...# #...# .###.|", "P": "|####. #...# #...# ####. #.... #.... #....|",
 "Q": "|.###. #...# #...# #...# #.#.# #..#. .##.#|", "R": "|####. #...# #...# ####. #.#.. #..#. #...#|",
 "S": "|.#### #.... #.... .###. ....# ....# ####.|", "T": "|##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..|",
 "U": "|#...# #...# #...# #...# #...# #...# .###.|", "V": "|#...# #...# #...# #...# .#.#. .#.#. ..#..|",
 "W": "|#...# #...# #...# #.#.# #.#.# ##.## #...#|", "X": "|#...# #...# .#.#. ..#.. .#.#. #...# #...#|",
 "Y": "|#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..|", "Z": "|##### ....# ...#. ..#.. .#... #.... #####|",
 "Ä": ".#.#. .....|.###. #...# #...# ##### #...# #...# #...#|", "Ö": ".#.#. .....|.###. #...# #...# #...# #...# #...# .###.|",
 "Å": "..#.. .#.#.|..#.. .#.#. #...# ##### #...# #...# #...#|", "Ü": ".#.#. .....|#...# #...# #...# #...# #...# #...# .###.|",
 "É": "...#. ..#..|##### #.... #.... ####. #.... #.... #####|",
 "a": "|.##. ...# .### #..# .###|", "b": "|#... #... ###. #..# #..# #..# ###.|", "c": "|.### #... #... #... .###|",
 "d": "|...# ...# .### #..# #..# #..# .###|", "e": "|.##. #..# #### #... .###|", "f": "|.## #.. ### #.. #.. #.. #..|",
 "g": "|.### #..# #..# #..# .###|...# ###.", "h": "|#... #... ###. #..# #..# #..# #..#|", "i": "|# . # # # # #|",
 "j": "|.# .. .# .# .# .# .#|.# #.", "k": "|#... #... #..# #.#. ##.. #.#. #..#|", "l": "|#. #. #. #. #. #. .#|",
 "m": "|####. #.#.# #.#.# #.#.# #.#.#|", "n": "|###. #..# #..# #..# #..#|", "o": "|.##. #..# #..# #..# .##.|",
 "p": "|###. #..# #..# #..# ###.|#... #...", "q": "|.### #..# #..# #..# .###|...# ...#", "r": "|#.## ##.. #... #... #...|",
 "s": "|.### #... .##. ...# ###.|", "t": "|.#. .#. ### .#. .#. .#. ..#|", "u": "|#..# #..# #..# #..# .###|",
 "v": "|#...# #...# #...# .#.#. ..#..|", "w": "|#...# #...# #.#.# #.#.# .#.#.|", "x": "|#...# .#.#. ..#.. .#.#. #...#|",
 "y": "|#..# #..# #..# #..# .###|...# .##.", "z": "|#### ...# .##. #... ####|",
 "ä": "|#..# .... .##. ...# .### #..# .###|", "ö": "|#..# .... .##. #..# #..# #..# .##.|",
 "å": ".##. #..#|.##. .... .##. ...# .### #..# .###|", "ü": "|#..# .... #..# #..# #..# #..# .###|",
 "é": "|..#. .#.. .##. #..# #### #... .###|",
 "0": "|.###. #...# #..## #.#.# ##..# #...# .###.|", "1": "|.#. ##. .#. .#. .#. .#. ###|",
 "2": "|.###. #...# ....# ...#. ..#.. .#... #####|", "3": "|####. ....# ....# .###. ....# ....# ####.|",
 "4": "|...#. ..##. .#.#. #..#. ##### ...#. ...#.|", "5": "|##### #.... ####. ....# ....# #...# .###.|",
 "6": "|..##. .#... #.... ####. #...# #...# .###.|", "7": "|##### ....# ...#. ..#.. .#... .#... .#...|",
 "8": "|.###. #...# #...# .###. #...# #...# .###.|", "9": "|.###. #...# #...# .#### ....# ...#. .##..|",
 ".": "|. . . . . . #|", ",": "|.. .. .. .. .. .. .#|#.", ":": "|. . . # . . #|", ";": "|.. .. .. .# .. .. .#|#.",
 "!": "|# # # # # . #|", "?": "|.##. #..# ...# ..#. .#.. .... .#..|", "'": "|# # . . . . .|", '"': "|#.# #.# ... ... ... ... ...|",
 "-": "|... ... ... ### ... ... ...|", "+": "|... ... .#. ### .#. ... ...|", "=": "|... ... ### ... ### ... ...|",
 "/": "|..# ..# .#. .#. .#. #.. #..|", "(": "|.# #. #. #. #. #. .#|", ")": "|#. .# .# .# .# .# #.|",
 "[": "|## #. #. #. #. #. ##|", "]": "|## .# .# .# .# .# ##|", "<": "|... ..# .#. #.. .#. ..# ...|", ">": "|... #.. .#. ..# .#. #.. ...|",
 "%": "|##..# ##.#. ...#. ..#.. .#... .#.## #..##|", "*": "|... #.# .#. #.# ... ... ...|", "_": "|.... .... .... .... .... .... ####|",
 "#": "|.#.#. ##### .#.#. .#.#. .#.#. ##### .#.#.|", "&": "|.##.. #..#. .##.. .#... #.#.# #..#. .##.#|",
 "x": "|#...# .#.#. ..#.. .#.#. #...#|", "\u2013": "|.... .... .... #### .... .... ....|", "\u00b7": "|. . . # . . .|",
 "|": "|# # # # # # #|#", "\u2026": "|..... ..... ..... ..... ..... ..... #.#.#|",
}

_LOWER = set("abcdefghijklmnopqrstuvwxyzäöåüé")
_CAPMAP = [0, 1, 1, 2, 3, 4, 5, 5, 6]
_LOWMAP = [0, 1, 2, 3, 3, 4, 5, 5, 6]


def _parse(spec):
    acc, body, desc = (spec.split("|") + ["", ""])[:3]
    acc = [row for row in acc.split() if row]
    body = [row for row in body.split() if row]
    desc = [row for row in desc.split() if row]
    if len(body) == 5:
        body = ["." * len(body[0])] * 2 + body
    return acc, body, desc


class PixelFont:
    def __init__(self, tall=False, scale=1, bold=False, space=3):
        self.tall = tall
        self.sc = scale
        self.bold = bold
        self.space = space
        self.cap = 9 if tall else 7
        self.rows = 2 + self.cap + 2
        self.glyphs = {}
        for ch, spec in _GL.items():
            self.glyphs[ch] = self._build(ch, spec)
        self.cache = {}

    def _build(self, ch, spec):
        acc, body, desc = _parse(spec)
        w = max(len(r) for r in acc + body + desc)
        if self.tall:
            mp = _LOWMAP if ch in _LOWER else _CAPMAP
            body = [body[i] for i in mp]
        rows = ["." * w] * (2 - len(acc)) + acc + body + desc
        px = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "#"]
        if self.bold:
            st = set(px)
            px = sorted(st | {(x + 1, y) for x, y in st if (x + 2, y) not in st})
            w += 1
        return w, px

    def _g(self, ch):
        g = self.glyphs.get(ch)
        if g is None:
            g = self.glyphs.get(ch.upper()) or self.glyphs["?"]
        return g

    def size(self, text):
        text = "" if text is None else str(text)
        w = 0
        for ch in text:
            w += self.space if ch == " " else self._g(ch)[0] + 1
        if text and text[-1] != " ":
            w -= 1
        return max(0, w) * self.sc, self.rows * self.sc

    def render(self, text, aa=False, color=(255, 255, 255), bg=None):
        text = "" if text is None else str(text)
        key = (text, tuple(color[:3]), self.sc, self.bold, self.tall)
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        w, h = self.size(text)
        surf = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
        col = tuple(color[:3])
        sc = self.sc
        x = 0
        for ch in text:
            if ch == " ":
                x += self.space
                continue
            gw, px = self._g(ch)
            for gx, gy in px:
                surf.fill(col, ((x + gx) * sc, gy * sc, sc, sc))
            x += gw + 1
        self.cache[key] = surf
        return surf


def has_glyph(ch):
    return ch == " " or ch in _GL or (ch.upper() in _GL)


class Font:
    """scale 1 is the tall UI face. scale 2 and up is the bold title face."""

    def __init__(self):
        self.ui = PixelFont(tall=True, scale=1)
        self.big = PixelFont(tall=True, scale=2, bold=True)

    def _pick(self, scale):
        return self.big if scale >= 2 else self.ui

    def size(self, text, scale=1):
        return self._pick(scale).size(text)

    def render(self, text, color, scale=1):
        return self._pick(scale).render(text, False, color)


def blit(surf, font, text, x, y, color, scale=1, center=False, shadow=True):
    if not text:
        return
    img = font.render(text, color, scale)
    if center:
        x -= img.get_width() // 2
        y -= img.get_height() // 2
    if shadow:
        sh = font.render(text, (24, 12, 10), scale)
        surf.blit(sh, (x + scale, y + scale))
    surf.blit(img, (x, y))
