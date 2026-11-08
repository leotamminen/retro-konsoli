# Tuonelan polku, lähdekoodi

Julkaisu on yksi pygame-tiedosto. Lähde on tässä kansiossa. `master` pitää vanhat julkaisut koskemattomina. Uusi työ tehdään kehityshaarassa.

## Kokoaminen

```bash
python3 build.py
```

Komento lukee `src/pNN_*.py` numerojärjestyksessä ja upottaa `maps/vellamo.json` ennen Vellamo-moduulia. Tuloksena on `TuonelanPolku1.3.4.pygame`. Pelissä ei ole uutta ajonaikaista kirjastoa: vain Python 3 ja pygame 2.6.1. Kartta ja äänet syntyvät pelin sisällä.

Ainoa käynnistys on `src/p99_entry.py` tiedoston lopussa. Sitä ennen kaikki määritelmät on suoritettu.

## Testaus

```bash
python3 tests/test_release.py
```

Testi käynnistää kootun tiedoston `__main__`-tilassa ja ajaa oikeaa `update`- ja `draw`-silmukkaa. Ohjaimet ovat SDL:n virtuaalilaitteita, eivät fyysistä DualShockia tai Batoceraa. Kuvat kirjoitetaan `/tmp/tp134`.

## Kartta

`maps/vellamo.json` on Vellamon lohkolista. Kenttä `blocks` on listoja `[x, y, w, h, t]`. `t` on 0 ilma, 1 kiinteä, 2 taso, 5 vesi. `x` ja `y` ovat tiiliruutuja. Pohja on ilmaa rivin 20 yläpuolella ja kiinteää siitä alaspäin. Kokoamisen jälkeen peli ei lue tiedostoa uudestaan.

Vanha metsä, suo ja joki ovat yhä koodissa `src/p3_world.py`. Niiden pomotaistelut on jätetty ennalleen.

## Ehdotus editoriksi

Erillistä editoria ei ole, eikä uusi työkalu ole pakollinen. Käytännöllinen seuraava askel on pieni pygame-ikkuna, joka piirtää `vellamo.json`-lohkot, liikuttaa osoitinta nuolilla ja tallentaa saman jsonin. Leo voi jo nyt siirtää, lisätä ja poistaa lohkoja tekstinä ja koota pelin uudestaan. Koko peruskartan vienti samaan muotoon on eri työ, eikä sitä ole tehty tässä versiossa.
