
# ---------------- translations: Finnish / English ----------------
def _t(key, fi, en): TR["fi"][key] = fi; TR["en"][key] = en

_t("title", "TUONELAN POLKU", "PATH OF TUONELA")
_t("subtitle", "Matka Tuonelan virralle", "A journey to the river of Tuonela")
_t("m_continue", "Jatka", "Continue"); _t("m_new", "Uusi peli", "New game"); _t("m_settings", "Asetukset", "Settings"); _t("m_quit", "Lopeta", "Quit")
_t("m_resume", "Jatka peliä", "Resume"); _t("m_map", "Kartta", "Map"); _t("m_controls", "Ohjaus", "Controls")
_t("m_p2_leave", "Pelaaja 2 poistuu", "Player 2 leaves"); _t("m_to_title", "Päävalikkoon", "Main menu")
_t("paused", "Tauko", "Paused"); _t("p2_hint", "Toinen pelaaja: paina Start toisella ohjaimella", "Second player: press Start on another controller")
_t("m_leave_fire", "Jatka matkaa", "Leave the fire"); _t("m_levelup1", "Vahvistu", "Level up"); _t("m_levelup", "Vahvistu: %s", "Level up: %s")
_t("m_save_exit", "Tallenna ja päävalikkoon", "Save and exit to menu")
_t("fire_sub", "Lepäät nuotion ääressä. Viholliset heräävät.", "You rest by the fire. The enemies return.")
_t("save_info", "%s, taso %d - %s", "%s, level %d - %s"); _t("time_fmt", "%d h %02d min", "%d h %02d min")
_t("save_corrupt", "Tallennus oli vioittunut. Aloita uusi peli.", "The save was corrupt. Start a new game.")
_t("save_backup", "Tallennus palautettiin varmuuskopiosta.", "Save restored from backup.")
_t("confirm_new", "Uusi peli korvaa nykyisen tallennuksen. Jatketaanko?", "A new game replaces the current save. Continue?")
_t("yes", "Kyllä", "Yes"); _t("no", "Ei", "No"); _t("on", "Päällä", "On"); _t("off", "Pois", "Off")
_t("choose_class", "Valitse sankarisi", "Choose your hero"); _t("choose_class_p2", "Pelaaja 2: valitse sankarisi", "Player 2: choose your hero")
_t("hint_choose", "{jump} Valitse   {dodge} Takaisin", "{jump} Select   {dodge} Back")
_t("cls_warrior", "Soturi", "Warrior"); _t("cls_sage", "Tietäjä", "Sage"); _t("cls_hunter", "Metsästäjä", "Hunter")
_t("cd_warrior", "Miekka ja kilpi. Torju iskut oikealla hetkellä. Kestävä, mutta hidas.", "Sword and shield. Parry with good timing. Sturdy, but slow.")
_t("cd_sage", "Loitsut ja kantele, joka parantaa ja vahvistaa. Hauras, mutta vaarallinen kaukaa.", "Spells and a kantele that heals and empowers. Fragile, but deadly from afar.")
_t("cd_hunter", "Jousi ja tikari. Nopea ja pitkä väistö. Pysy liikkeessä.", "Bow and dagger. Quick, with a long dodge. Keep moving.")
_t("pl_1", "Pelaaja 1", "Player 1"); _t("pl_2", "Pelaaja 2", "Player 2")
_t("p2_joined", "Pelaaja 2 liittyi: %s", "Player 2 joined: %s"); _t("p2_left", "Pelaaja 2 poistui", "Player 2 left")
_t("p_down", "%s kaatui! Auta ylös", "%s is down! Help them up"); _t("p_revive", "Pidä {interact} nostaaksesi", "Hold {interact} to revive")
_t("p_revived", "%s nousi jaloilleen", "%s is back on their feet"); _t("p_keep_close", "Pysykää lähekkäin", "Stay close together")
_t("pad_lost", "%s: ohjain irtosi", "%s: controller disconnected"); _t("pad_lost_d", "Paina {pause} uudella ohjaimella", "Press {pause} on a controller")
_t("p_rest", "Lepää", "Rest"); _t("p_lever", "Vedä vipua", "Pull lever")
_t("lever_lv_gate", "Portti rämähti auki", "The gate crashed open"); _t("lever_lv_ladder", "Tikkaat laskeutuivat alas", "A ladder dropped down")
_t("lever_lv_bridge", "Silta laskeutui joen yli", "The bridge lowered across the river")
_t("bonfire_lit", "Nuotio sytytetty", "Bonfire lit"); _t("got_souls", "+%d sielua", "+%d souls"); _t("found_item", "Löysit: %s", "Found: %s")
_t("secret_found", "Salainen kulku aukesi", "A secret passage opened"); _t("stain_back", "Sait sielusi takaisin: %d", "Souls recovered: %d")
_t("stain_hint", "Hae sielusi kuolinpaikalta", "Retrieve your souls where you fell")
_t("you_died", "KUOLIT", "YOU DIED"); _t("quitting", "Poistutaan...", "Quitting..."); _t("loading", "Ladataan...", "Loading...")
_t("felled", "%s kaatui", "%s defeated"); _t("parry", "Torjuttu!", "Parry!")
_t("area_forest", "Metsä", "The Forest"); _t("area_swamp", "Suo", "The Mire"); _t("area_river", "Tuonelan joki", "River of Tuonela")
_t("boss_hiisi", "Hiisi", "Hiisi"); _t("boss_turso", "Iku-Turso", "Iku-Turso"); _t("boss_tytti", "Tuonen Tytti", "Tuonen Tytti")
for k, fi, en in (("b0", "Metsän laita", "Edge of the Forest"), ("b1", "Kuusikon kätkö", "Spruce Hollow"), ("b2", "Hiiden portti", "Hiisi's Gate"),
                  ("b3", "Suon reuna", "Edge of the Mire"), ("b4", "Rauniotornin juuri", "Ruined Tower Base"), ("b5", "Turson kynnys", "Turso's Threshold"),
                  ("b6", "Joen ranta", "The Riverbank"), ("b7", "Luusilta", "Bone Bridge"), ("b8", "Tytin kynnys", "The Maiden's Threshold")):
    _t("bf_" + k, fi, en)
_t("hint_levelup", "{jump} Vahvista   {dodge} Takaisin", "{jump} Level up   {dodge} Back")
_t("lv_title", "Vahvistu", "Level up"); _t("lv_who", "%s: %s", "%s: %s"); _t("lv_level", "Taso %d", "Level %d")
_t("lv_souls", "Sielut: %d", "Souls: %d"); _t("lv_cost", "Hinta: %d", "Cost: %d"); _t("lv_max", "Huipputaso", "Max level")
_t("st_vit", "Elinvoima", "Vitality"); _t("st_end", "Kestävyys", "Endurance"); _t("st_str", "Voima", "Strength")
_t("st_foc_warrior", "Tahto", "Resolve"); _t("st_foc_sage", "Mieli", "Mind"); _t("st_foc_hunter", "Tarkkuus", "Precision")
_t("st_vit_d", "+10 elämää", "+10 health"); _t("st_end_d", "+6 kestävyyttä", "+6 stamina"); _t("st_str_d", "+8 % vahinkoa", "+8 % damage")
_t("st_foc_warrior_d", "Vakaampi asento, kilpi kestää", "Steadier stance, stronger guard")
_t("st_foc_sage_d", "+10 keskittymistä, vahvemmat loitsut", "+10 focus, stronger spells")
_t("st_foc_hunter_d", "Vahvempi jousi, halvempi väistö", "Stronger bow, cheaper dodge")
_t("it_c_moss", "Sammalamuletti", "Moss Amulet"); _t("it_c_moss_d", "+20 elämää", "+20 health")
_t("it_c_bear", "Karhun kynsi", "Bear Claw"); _t("it_c_bear_d", "+15 % vahinkoa", "+15 % damage")
_t("it_c_wolf", "Suden korva", "Wolf's Ear"); _t("it_c_wolf_d", "Kestävyys palautuu nopeammin", "Stamina recovers faster")
_t("it_c_ember", "Hiilenpala", "Ember Charm"); _t("it_c_ember_d", "Väistö kuluttaa 30 % vähemmän", "Dodging costs 30 % less")
_t("it_flask", "Parannuspullo", "Healing Flask"); _t("it_flask_d", "Yksi pullo lisää", "One more flask")
_t("it_flaskpow", "Kirkas yrtti", "Bright Herb"); _t("it_flaskpow_d", "Pullot parantavat enemmän", "Flasks heal more")
_t("it_feather", "Haukan sulka", "Hawk Feather"); _t("it_feather_d", "Kaksoishyppy: hyppää uudestaan ilmassa", "Double jump: jump again in mid-air")
_t("map_legend", "Oranssi: nuotio   Punainen: pomo   Vilkkuva: sinä", "Orange: bonfire   Red: boss   Blinking: you")
_t("map_unknown", "Tuntematon", "Unknown")
_t("gt", ">", ">"); _t("lt", "<", "<")
# settings
for k, fi, en, sfi, sen in (
    ("lang", "Kieli / Language", "Kieli / Language", "Pelin kieli.", "Game language."),
    ("difficulty", "Vaikeustaso", "Difficulty", "Voit vaihtaa vaikeustasoa milloin vain.", "You can change the difficulty at any time."),
    ("penalty", "Kuoleman rangaistus", "Death penalty", "Mitä sieluillesi käy, kun kuolet.", "What happens to your souls when you die."),
    ("music", "Musiikki", "Music", "Musiikki päälle tai pois.", "Music on or off."),
    ("music_vol", "Musiikin voimakkuus", "Music volume", "Säädä musiikin voimakkuutta.", "Adjust the music volume."),
    ("sfx", "Äänitehosteet", "Sound effects", "Äänitehosteet päälle tai pois.", "Sound effects on or off."),
    ("sfx_vol", "Tehosteiden voimakkuus", "Effects volume", "Säädä äänitehosteiden voimakkuutta.", "Adjust the sound effects volume."),
    ("shake", "Ruudun tärinä", "Screen shake", "Kameran tärinä iskuista ja räjähdyksistä.", "Camera shake from hits and explosions."),
    ("dmgnum", "Vahinkoluvut", "Damage numbers", "Näytä vahinkoluvut osumien kohdalla.", "Show damage numbers on hits."),
    ("flash", "Välkkyvät tehosteet", "Flashing effects", "Vähennetty: ei valkoisia osumavälähdyksiä (valoherkille).", "Reduced: no white hit flashes (for light sensitivity)."),
    ("prompts", "Painikekuvakkeet", "Button prompts", "Ohjeiden kuvakkeet: PlayStation, Xbox tai näppäimistö.", "Prompt icons: PlayStation, Xbox or keyboard."),
    ("runmode", "Juoksutapa", "Run style", "Automaattinen: tikun suunta riittää. Analoginen: tikun kallistus säätää vauhtia.", "Automatic: any push runs. Analog: stick tilt sets your speed."),
    ("hints", "Vihjeet", "Hints", "Näytä ohjevihjeet pelin alussa.", "Show tutorial hints early in the game."),
    ("controls", "Ohjaus", "Controls", "Näytä ohjainten ohje.", "Show the controls help page."),
    ("back", "Takaisin", "Back", "Palaa edelliseen valikkoon.", "Return to the previous menu.")):
    _t("set_" + k, fi, en); _t("sd_" + k, sfi, sen)
_t("lang_fi", "Suomi", "Suomi"); _t("lang_en", "English", "English")
_t("dn_easy", "Helppo", "Easy"); _t("dn_normal", "Normaali", "Normal"); _t("dn_hard", "Vaikea", "Hard"); _t("dn_brutal", "Julma", "Brutal"); _t("dn_tuonela", "Tuonela", "Tuonela")
_t("sd_difficulty_easy", "Helppo: heikommat iskut, hitaammat viholliset ja pitkät varoitusajat.", "Easy: weaker hits, slower enemies and long warning times.")
_t("sd_difficulty_normal", "Normaali: tarkoitettu kokemus. Opettele iskut ja väistä.", "Normal: the intended experience. Learn the attacks and dodge.")
_t("sd_difficulty_hard", "Vaikea: kovemmat iskut, lyhyemmät varoitukset, vähemmän parannusta.", "Hard: harder hits, shorter warnings, weaker healing.")
_t("sd_difficulty_brutal", "Julma: jokainen virhe maksaa. Viholliset ovat nopeita ja sitkeitä.", "Brutal: every mistake costs. Enemies are quick and tough.")
_t("sd_difficulty_tuonela", "Tuonela: armoton. Muutama osuma tappaa, eikä mikään anna anteeksi.", "Tuonela: merciless. A few hits kill and nothing forgives.")
_t("pen_classic", "Klassinen", "Classic"); _t("pen_mild", "Lievä", "Mild")
_t("sd_penalty_classic", "Klassinen: sielut jäävät läikäksi kuolinpaikalle. Hae ne, tai menetät ne.", "Classic: souls stay as a stain where you died. Retrieve them or lose them.")
_t("sd_penalty_mild", "Lievä: et menetä sieluja kuollessasi.", "Mild: you lose no souls when you die.")
_t("fl_full", "Täysi", "Full"); _t("fl_reduced", "Vähennetty", "Reduced")
_t("pr_ps", "PlayStation", "PlayStation"); _t("pr_xbox", "Xbox", "Xbox"); _t("pr_kb", "Näppäimistö", "Keyboard")
_t("run_auto", "Automaattinen", "Automatic"); _t("run_analog", "Analoginen", "Analog")
# controls help
_t("c_move", "Liiku. Ylös/alas tikkailla", "Move. Up/down on ladders"); _t("c_jump", "Hyppää (sulalla kaksoishyppy)", "Jump (double jump with the feather)")
_t("c_light_warrior", "Kevyt miekanisku", "Light sword attack"); _t("c_heavy_warrior", "Raskas isku, hidas mutta voimakas", "Heavy attack, slow but strong")
_t("c_light_sage", "Loitsu: salama (kuluttaa keskittymistä)", "Spell: bolt (uses focus)"); _t("c_heavy_sage", "Voimakas loitsu: lumottu pallo", "Strong spell: enchanted orb")
_t("c_light_hunter", "Tikarin iskusarja", "Dagger combo"); _t("c_heavy_hunter", "Raskas tikari-isku", "Heavy dagger strike")
_t("c_dodge", "Väistö: vierähdys, hetken haavoittumaton", "Dodge roll, briefly invulnerable")
_t("c_guard_warrior", "Pidä: kilpi. Hyvä ajoitus torjuu", "Hold: shield. Good timing parries")
_t("c_guard_sage", "Kantele: parantaa ja vahvistaa lähellä olevat", "Kantele: heals and empowers nearby allies")
_t("c_guard_hunter", "Taaksepäin loikka ja ammus", "Backflip and shot")
_t("c_skill_warrior", "Kilpisysäys: horjuttaa vihollisen", "Shield bash: staggers the enemy")
_t("c_skill_sage", "Shokkiaalto: tuhoaa ammukset", "Shockwave: destroys projectiles")
_t("c_skill_hunter", "Pidä: jännitä jousi. Vapauta: ammu", "Hold: draw the bow. Release: shoot")
_t("c_flask", "Parannuspullo (ristiohjain alas)", "Healing flask (D-pad down)")
_t("c_interact", "Nuotio, vipu, kaatuneen nosto", "Bonfire, lever, revive an ally"); _t("c_map", "Kartta", "Map"); _t("c_pause", "Tauko. Toinen pelaaja liittyy tästä", "Pause. A second player joins with this")
_t("c_drop", "Alas + hyppy: pudottaudu tasolta", "Down + jump: drop through platforms")
_t("c_quit", "Poistu: pidä Select + Start sekunti", "Quit: hold Select + Start for one second")
_t("c_join", "Toinen pelaaja: paina Start toisella ohjaimella", "Second player: press Start on another controller")
# hints
_t("h_move", "Liiku {move}", "Move {move}"); _t("h_jump", "Hyppää {jump}. Pidempi painallus hyppää korkeammalle", "Jump {jump}. Hold longer to jump higher")
_t("h_attack", "Kevyt isku {light}, raskas isku {heavy}. Iskut kuluttavat kestävyyttä", "Light attack {light}, heavy attack {heavy}. Attacks use stamina")
_t("h_roll", "Väistä iskun alta {dodge}. Vierähdyksessä et ole haavoittuva", "Dodge out of attacks with {dodge}. You are not hurt while rolling")
_t("h_special_warrior", "Pidä {guard} torjuaksesi. Torju juuri iskun osuessa, niin vihollinen horjahtaa", "Hold {guard} to guard. Guard just as a hit lands to stagger the enemy")
_t("h_special_sage", "{skill} lähettää shokkiaallon, {guard} soittaa kanteletta ja parantaa", "{skill} sends a shockwave, {guard} plays the kantele and heals")
_t("h_special_hunter", "Pidä {skill} jännittääksesi jousen ja vapauta ampuaksesi. {guard} loikkaa taakse", "Hold {skill} to draw the bow, release to shoot. {guard} backflips")
# ending
_t("end_0", "Tuonen Tytti vaipui virran syvyyteen, ja vesi tyyntyi.", "Tuonen Tytti sank into the depths of the river, and the water grew still.")
_t("end_1", "Tuonelan väki palasi lepoonsa, ja metsä hengitti taas.", "The folk of Tuonela returned to their rest, and the forest breathed again.")
_t("end_2", "Polku johtaa nyt valoon. Olet nähnyt sen pimeimmän pään.", "The path now leads to the light. You have seen its darkest end.")
_t("end_title", "Matka päättyy", "The path ends"); _t("end_stats", "Aika %s, kuolemia %d, taso %d", "Time %s, deaths %d, level %d")
_t("end_thanks", "Kiitos pelaamisesta!", "Thank you for playing!"); _t("hint_next", "{jump} Jatka", "{jump} Continue")
_t("set_perf", "Suorituskyky", "Performance")
_t("sd_perf", "FPS- ja ruutuajan mittari (vianetsintä).", "FPS and frame-time meter (debug).")
_t("area_pohjola","Pohjanmaa", "Northland")
_t("mpond","Pohjola", "Pohjola")
_t("louhi_name","Pohjolan Louhi, Valon Ryöstäjä", "Louhi of Northland, Thief of Light")
_t("louhi_intro","POHJOLAN LOUHI", "LOUHI OF NORTHLAND")
_t("louhi_minions","Pohjan lapset, nouse!", "Children of the North, rise!")
_t("louhi_wait","Valkealla on turva… toistaiseksi.", "Safe at the fire… for now.")
_t("louhi_warn","Pohjan emäntä odottaa oikealla.", "The mistress of the North awaits to the right.")
_t("real_0","Louhi lyyhistyi. Riistetty valo vapautui vastentahtoisista kynsistä.", "Louhi fell. The stolen light broke free of her reluctant claws.")
_t("real_1","Sampo ei ollut osumasi palkinto. Palkintosi on valo, jonka annoit kansalle.", "The Sampo was not your prize. Your prize is the light you returned to the people.")
_t("real_2","Pohjolan pimeys taipui. Tuonelan polku päättyy siihen, missä aamunkoi alkaa.", "The dark of the North yielded. The Path of Tuonela ends where dawn begins.")
_t("real_title","Todellinen loppu", "The true ending")
_t("bf_b9","Viimeinen nuotio", "The last fire")
_t("boss_louhi", "Pohjolan Louhi, Valon Ryöstäjä", "Louhi of Northland, Thief of Light")
