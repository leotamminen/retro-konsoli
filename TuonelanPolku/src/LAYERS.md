# Source modules

`build.py` loads these files in the order below. The order is the list `ORDER` in `build.py`, not a filename number. A module may use names defined by modules above it. The build fails if a file is missing, extra, out of order, or if it rebinds a class method from outside the class.

| File | Owns |
|---|---|
| font.py | Bitmap font |
| core.py | Constants, settings, saves |
| audio.py | Sound effects and music, one `render_track` |
| world.py | Base world from the embedded `maps/world.json` |
| physics.py | Movement and hazards |
| art.py | Character and prop drawing |
| scenery.py | Sky, parallax, fog, including the water realms |
| boss_art.py | Hiisi, Turso, Tytti, Louhi sprites |
| entities.py | Projectiles, zones, enemies |
| enemies.py | Enemy brains, including the water mobs |
| bosses.py | Hiisi, Turso, Tytti, Louhi |
| player.py | Pads and the player |
| session.py | Session, camera, combat, gates, New Game+ |
| ui.py | Menus, cutscenes, HUD, map screen |
| text.py | Base Finnish and English strings |
| app.py | The `Game` object and `main()`, not the call |
| vellamo_world.py | Vellamo columns from `maps/vellamo.json` |
| vellamo_art.py | Water-boss sprites |
| vellamo_music.py | Water-realm tracks |
| vellamo_bosses.py | Joukahainen, Ahti, Aino, Vellamo |
| vellamo_mobs.py | Lampi, rapu, poltto, merikala, kutri brains |
| vellamo_text.py | Realm strings and the ending drawings |
| map_chart.py | Explored-region map image |
| map_draw.py | Map screen drawing |
| vellamo_scenery.py | Water sky, reeds, mist |
| vellamo_strings.py | Bonfire names and the gate sign |
| release_text.py | Credits and test-weapon strings |
| entry.py | The only `if __name__ == "__main__"` call |

`version.json` is the only version. Source modules do not assign `VERSION`. Do not edit a generated `TuonelanPolku*.pygame` by hand.
