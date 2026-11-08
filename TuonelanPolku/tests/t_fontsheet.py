"""Renders a font sample sheet (all glyphs, all sizes) to screenshots/20_font_sheet.png."""
from lib import *
g = new_game(); c = g.canvas; c.fill((14, 12, 20))
chars = "".join(sorted(G["_GL"].keys(), key=lambda ch: (not ch.isupper(), not ch.islower(), not ch.isdigit(), ch)))
lines = ["ABCDEFGHIJKLMNOPQRSTUVWXYZ ÄÖÅ", "abcdefghijklmnopqrstuvwxyz äöå", "0123456789 .,:;!?'\"-+=/()[]<>%*#&_"]
y = 4
for name, f in (("tiny", g.tiny), ("font", g.font), ("mid", g.mid)):
    for ln in lines:
        g.text(TStr(ln), 4, y + f.get_height() // 2, (235, 230, 210), f, "l"); y += f.get_height() + 1
    y += 2
g.text(TStr("s a e o 8 B S 5 | i l 1 I | ä ö å Ä Ö"), 4, y + 5, (255, 220, 140), g.tiny, "l"); y += 12
g.text(TStr("Tuonelan polku"), 4, y + g.big.get_height() // 2, (255, 225, 150), g.big, "l"); y += g.big.get_height()
g.text(TStr("Äänitehosteet, sielut 1234"), 160, y - g.big.get_height() // 2 + 8, (200, 220, 255), g.font, "l")
shot(g, "20_font_sheet", 4)
print("sheet ok", y)
