# Finnish UI. Every glyph used here exists in font.py.
from .const import PNAMES

FI = {
    "title": "KULTAKIRI",
    "tag": "VIIMEINEN JUOKSIJA VOITTAA",
    "press": "PAINA X",
    "join": "LIITY",
    "need": "TARVITAAN 2 PELAAJAA",
    "start_hint": "OPTIONS: ALOITA",
    "legend_btn": "KOLMIO: TEHOSTEET",
    "leave_hint": "SHARE: POISTU",
    "quit_hint": "SHARE+OPTIONS: LOPETA",
    "round": "ERÄ %d/%d",
    "go": "NYT!",
    "ghost": "HAAMU",
    "out": "ULOS",
    "pad": "OHJAIN IRTOSI",
    "win": "%s VEI ERÄN",
    "draw": "TASAPELI",
    "board": "PISTETAULU",
    "coins": "KOL",
    "meters": "M",
    "total": "YHT",
    "next": "X: SEURAAVA ERÄ",
    "results": "TULOKSET",
    "champ": "%s ON KULTAKUNINGAS",
    "rematch": "X: UUSINTA",
    "back_lobby": "SHARE: AULAAN",
    "paused": "TAUKO",
    "resume": "JATKA",
    "to_lobby": "AULAAN",
    "quit": "LOPETA",
    "quitting": "LOPETETAAN",
    "legend": "TEHOSTEET",
    "back": "X: TAKAISIN",
    "controls": "X HYPÄÄ  SAUVA LIIKUTTAA",
    "p_double": "KAKSOISHYPPY",
    "p_speed": "VAUHTI",
    "p_shield": "KILPI",
    "p_magnet": "MAGNEETTI",
    "p_slow": "HIDASTUS",
    "p_glide": "LIITO",
    "d_double": "TOINEN HYPPY ILMASSA",
    "d_speed": "JUOKSET NOPEAMMIN",
    "d_shield": "ESTÄÄ YHTEEN PIIKKIIN",
    "d_magnet": "KOLIKOT TULEVAT LUOKSE",
    "d_slow": "MUUT HIDASTUVAT",
    "d_glide": "PIDÄ X NIIN LIIDÄT",
    "finish": "MAALI",
}


def tr(key, *args):
    text = FI[key]
    if args:
        text = text % args
    return text


def pname(idx):
    return PNAMES[idx]
