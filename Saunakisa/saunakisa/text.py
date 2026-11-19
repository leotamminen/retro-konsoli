# Finnish UI. Every glyph used here exists in font.py.
from .const import PNAMES

FI = {
    "title": "SAUNAKISA",
    "tag": "KUKA KESTÄÄ LÖYLYN",
    "press": "PAINA X",
    "join": "LIITY",
    "need": "TARVITAAN 2 PELAAJAA",
    "start_hint": "OPTIONS: ALOITA",
    "legend_btn": "KOLMIO: ASETUKSET",
    "cpu_hint": "NELIÖ: CPU",
    "cpu_tag": "CPU",
    "settings": "ASETUKSET",
    "set_cpu": "CPU",
    "set_diff": "VAIKEUS",
    "set_rounds": "ERÄT",
    "set_length": "ERÄN PITUUS",
    "set_heat": "KUUMUUS",
    "set_pick": "POIMINNAT",
    "set_sfx": "ÄÄNET",
    "set_music": "MUSIIKKI",
    "set_help": "OHJE",
    "d_helppo": "HELPPO",
    "d_normaali": "NORMAALI",
    "d_vaikea": "VAIKEA",
    "h_hidas": "HIDAS",
    "h_normaali": "NORMAALI",
    "h_nopea": "NOPEA",
    "p_harvoin": "HARVOIN",
    "p_normaali": "NORMAALI",
    "p_usein": "USEIN",
    "secs": "%dS",
    "leave_hint": "SHARE: POISTU",
    "quit_hint": "SHARE+OPTIONS: LOPETA",
    "round": "ERÄ %d/%d",
    "go": "NYT!",
    "fainted": "PYÖRRYI",
    "loyly": "LÖYLY!",
    "avanto": "AVANTO",
    "olut": "OLUT!",
    "pyyhe": "PYYHE!",
    "last": "VIIMEINEN",
    "board": "PISTETAULU",
    "win": "%s VEI ERÄN",
    "draw": "TASAPELI",
    "points": "PST",
    "total": "YHT",
    "next": "X: SEURAAVA ERÄ",
    "results": "TULOKSET",
    "champ": "%s ON SAUNAKUNINGAS",
    "rematch": "X: UUSINTA",
    "back_lobby": "SHARE: AULAAN",
    "paused": "TAUKO",
    "resume": "JATKA",
    "to_lobby": "AULAAN",
    "quit": "LOPETA",
    "quitting": "LOPETETAAN",
    "legend": "OHJE",
    "back": "X: TAKAISIN",
    "c_move": "SAUVA LIIKUTTAA",
    "c_climb": "YLÖS JA ALAS LAUTEILLA",
    "c_loyly": "X HEITTÄÄ LÖYLYN KIUKAALLA",
    "c_door": "VASEN OVI VIE VIILENEMÄÄN",
    "c_avanto": "AVANTO JÄÄHDYTTÄÄ NOPEASTI",
    "c_item": "OLUT JA PYYHE VIILENTÄVÄT",
    "c_score": "YLÄLAUDE ANTAA ENITEN",
    "c_faint": "LIIAN KUUMA NIIN PYÖRRYT",
    "c_win": "ENITEN PISTEITÄ VOITTAA",
    "hint_play": "YLÖS LAUTEILLE  X LÖYLY  VASEN ULOS",
    "room": "LÖYLY",
}


def tr(key, *args):
    text = FI[key]
    if args:
        text = text % args
    return text


def pname(idx):
    return PNAMES[idx]


def label(player):
    if getattr(player, "cpu", False):
        return tr("cpu_tag")
    return pname(player.idx)
