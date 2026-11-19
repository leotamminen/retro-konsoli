# Kultakiri text uses the shared Tuonelan Polku bitmap font.
import os
import sys

import pygame

_common = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "common"))
if _common not in sys.path:
    sys.path.insert(0, _common)
from pixelfont import PixelFont

_CACHE = {}


def get_font(scale=1, tall=None, bold=None):
    if tall is None:
        tall = True
    if bold is None:
        bold = scale >= 2
    key = (int(scale), bool(tall), bool(bold))
    font = _CACHE.get(key)
    if font is None:
        font = PixelFont(tall=tall, scale=int(scale), bold=bold, space=3)
        _CACHE[key] = font
    return font


def has_glyph(ch):
    if ch == " ":
        return True
    font = get_font(1)
    return ch in font.glyphs or ch.upper() in font.glyphs


class Font:
    """Kept so older call sites can still pass a font object into blit()."""

    def __init__(self, scale=1):
        self.scale = scale

    def size(self, text, scale=None):
        sc = self.scale if scale is None else scale
        return get_font(sc).size(text)


def blit(surf, font, text, x, y, color, scale=1, center=False, shadow=True):
    if not text:
        return
    sc = scale
    face = get_font(sc)
    img = face.render(text, False, color)
    if center:
        x -= img.get_width() // 2
        y -= img.get_height() // 2
    if shadow:
        sh = face.render(text, False, (32, 18, 28))
        surf.blit(sh, (x + max(1, sc // 2), y + max(1, sc // 2)))
    surf.blit(img, (x, y))
