"""Release strings. New Game Plus and the credits screen live on GameCore and GameUI."""

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
