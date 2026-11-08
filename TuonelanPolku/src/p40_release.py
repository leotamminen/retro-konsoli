"""1.3.4 release rules: credits, new game plus, menu strings, bonfire names."""

def begin_ng(s, save):
    if not save or not save.get("ng_ready"):
        return
    sv = new_save(save["cls"])
    sv["stats"] = {k: int(save["stats"].get(k, 0)) for k in STAT_KEYS}
    sv["souls"] = int(save.get("souls", 0))
    sv["taken"] = list(save.get("taken") or [])
    sv["p2"] = save.get("p2")
    sv["level"] = 1 + sum(sv["stats"].values())
    sv["deaths"] = int(save.get("deaths", 0))
    sv["time"] = int(save.get("time", 0))
    sv["ng"] = int(save.get("ng") or 0) + 1
    sv["ng_ready"] = True
    sv["bosses"] = []
    sv["opened"] = []
    sv["seen"] = ["b0"]
    sv["bonfire"] = "b0"
    sv["mapseen"] = []
    sv["louhi_unlocked"] = False
    sv["vellamo_unlocked"] = False
    sv["vellamo_visited"] = False
    sv["vellamo_done"] = False
    sv["aino_freed"] = False
    sv["done"] = False
    s.begin_session(sv)

def up_info(s):
    r = s.menu_in()
    s.info_t = getattr(s, "info_t", 0) + 1
    if (r["ok"] or r["back"]) and s.info_t > 8:
        s.state_name = "title"

def dr_info(s):
    c = s.canvas
    s.draw_title_bg(c, s.t_ui)
    s.panel(16, 18, 288, 146)
    s.text(tr("m_info"), W // 2, 30, (255, 225, 150), s.mid)
    lines = (
        tr("info_game"),
        tr("info_version", VERSION),
        tr("info_author"),
        tr("info_note"),
    )
    for i, line in enumerate(lines):
        s.text(line, W // 2, 52 + i * 16, (220, 220, 210), s.font)
    s.text(tr("info_back"), W // 2, 148, (170, 170, 180), s.tiny)

GameCore.begin_ng = begin_ng
GameUI.up_info = up_info
GameUI.dr_info = dr_info

for _key, _fi, _en in (
    ("m_info", "Tietoa", "Credits"),
    ("m_ng", "Uusi kierros+", "New Game +"),
    ("info_game", "TUONELAN POLKU", "PATH OF TUONELA"),
    ("info_version", "Versio %s", "Version %s"),
    ("info_author", "Leo Tamminen", "Leo Tamminen"),
    ("info_note", "Yksi tiedosto. Kartta ja aanet syntyvat pelissa.", "One file. Maps and audio are made in game."),
    ("info_back", "Hyppy tai väistö palaa", "Jump or dodge returns"),
    ("set_test_weapon", "Testiase", "Test weapon"),
    ("test_weapon_hud", "TESTIASE", "TEST WEAPON"),
    ("sd_test_weapon", "Testiase: valtava vahinko. Ei tallennu varusteeksi. Oletus pois.", "Test weapon: very high damage. Not saved as gear. Default off."),
    ("bf_b9", "Pohjolan nuotio", "Pohjola Bonfire"),
    ("bf_b10", "Aallon ranta", "Shimmering Shore"),
    ("bf_b11", "Syvänteen nuotio", "Depths Bonfire"),
    ("bf_b12", "Temppelin nuotio", "Cathedral Bonfire"),
    ("bf_b13", "Vapauden ranta", "Shore of Freedom"),
    ("it_c_pearl", "Helmi", "Pearl"),
    ("it_c_pearl_d", "Kestavyys palautuu hieman nopeammin.", "Stamina returns a little faster."),
):
    _t(_key, _fi, _en)
