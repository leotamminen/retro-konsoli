# Module map

`build.py` concatenates `pNN_*.py` in numeric order. The number is the load order. The name after it is the responsibility.

| File | Responsibility |
|---|---|
| p0_font | Bitmap font |
| p1_core | Constants, settings, saves |
| p2_audio | SFX and lazy music |
| p3_world | Reads the embedded base map |
| p4_phys | Movement and collisions |
| p5_art, p6_env, p7_bossart | Drawing |
| p8_ent, p9_ai | Entities and enemy brains |
| p10_boss | Hiisi, Turso, Tytti, Louhi |
| p11_player | Input pads and the player |
| p12_game | Session, camera, combat |
| p13_ui | Menus, cutscenes, HUD |
| p14_text | Base translations |
| p15_main | Game object and `main()`, not the call |
| p16_vellamo_core | Applies the Vellamo map |
| p18, p20, p21, p22 | Vellamo art, music, bosses, enemies |
| p40_release | Credits, New Game+, test-weapon text |
| p99_entry | The only `main()` call |

These still patch earlier classes instead of living inside them: `p23_v13_game.py`, `p25_v13_ui.py`, `p26_v13_core_hooks.py`, `p29_v13_transitions.py`, `p30` through `p35`. They run before `main()`, so the patches are active on the first frame. Moving them into the original classes would reorder a lot of working behavior, so they stay as a named layer for now.

`version.json` is the only version string. The build embeds it once. Source modules do not assign `VERSION`.
