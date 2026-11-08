"""Bonfire names and the Vellamo entrance copy. Gate behavior lives on GameCore."""
for b, nm, en in [
    ("b9", "Pohjolan nuotio", "Pohjola Bonfire"),
    ("b10", "Aallon ranta", "Shimmering Shore"),
    ("b11", "Syvänteen nuotio", "Depths Bonfire"),
    ("b12", "Temppelin nuotio", "Cathedral Bonfire"),
    ("b13", "Vapauden ranta", "Shore of Freedom"),
    ("vel_entrance", "VELLAMON VALTAKUNTA  >", "VELLAMO'S REALM  >"),
    ("p_vellamo", "Jatka Vellamon valtakuntaan", "Enter Vellamo's realm"),
    ("vel_sign", "Vellamon portti on heti nuotion oikealla puolella. Mene portille ja paina ylös.", "Vellamo's gate is right by the bonfire. Go to it and press up."),
]:
    _t(b, nm, en)
BF_KEYS.update({("b%d" % i): "bf_b%d" % i for i in range(9, 14)})
