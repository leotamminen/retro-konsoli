
# ---------------- game core: session, world state, combat resolution, camera, world drawing ----------------
_VELLAMO_GATE=(454*16+8, 320)
def _gate_unlocked(s):
    sv=s.save or {}
    return "louhi" in sv.get("bosses", []) and not sv.get("vellamo_visited")
MAP_CW, MAP_CH = 20, 11          # fog-of-war cell size in tiles
def map_cell(tx, ty): return "%d,%d" % (int(tx) // MAP_CW, max(0, int(ty)) // MAP_CH)
BF_START = {"b0": 0, "b1": 0, "b2": 0, "b3": 0, "b4": 0, "b5": 0, "b6": 10, "b7": 37, "b8": 2, "b9": 0}
def bonfire_pos(bid):
    if bid in BONFIRE_POS:return BONFIRE_POS[bid]
    tx = BONFIRES[bid]
    return tx * TILE + 8, floor_row(tx, BF_START[bid]) * TILE
BONFIRE_POS={k:(v*TILE+8,floor_row(v,BF_START[k])*TILE) for k,v in BONFIRES.items()}
BF_NAME = {"b0": "forest", "b1": "forest", "b2": "forest", "b3": "swamp", "b4": "swamp", "b5": "swamp", "b6": "river", "b7": "river", "b8": "river", "b9": "pohjola"}
BOSS_NAMES = ("hiisi", "turso", "tytti", "louhi")
CHARMS = ("c_moss", "c_bear", "c_wolf", "c_ember")

class GameCore:
    # ---------- session ----------
    def init_core(s):
        s.save = None; s.wd = None; s.players = []; s.enemies = []; s.projs = []; s.zones = []; s.parts = Parts()
        s.dns = []; s.hitstop = 0; s.state_name = "title"; s.boss = None; s.arena = None; s.stains = []
        s.cam = [0.0, 0.0]; s.shk_t = 0; s.shk_amp = 0; s.frames = 0; s.t0 = 0; s.dying = 0; s.msgs = []
        s.area = "forest"; s.area_popup = None; s.dark = 0.0; s.ffs = []; s.chunks = {}; s.banner = None; s.sep_t = 0
        s.hints_seen = set(); s.kills = 0; s.pads = {}; s.p_pad = [None, None]; s.felled = None; s.ending_t = 0
        s.dark_target = 0.0; s.gain = [];s.black=pygame.Surface((W,H))
    CHUNK_CACHE={};CHUNK_REV=[0]
    def chunk(s,c):
        key=(c,s.CHUNK_REV[0]);surf=GameCore.CHUNK_CACHE.get(key)
        if surf is None:
            surf=render_chunk(c,s.wd)
            if pygame.display.get_surface():surf=surf.convert()
            GameCore.CHUNK_CACHE[key]=surf
            if len(GameCore.CHUNK_CACHE)>28:GameCore.CHUNK_CACHE.pop(next(iter(GameCore.CHUNK_CACHE)))
        return surf
    def warm_all(s):
        center=int(s.cam[0])//320
        for c in range(max(0,center-1),min((COLS-1)//20,center+1)+1):s.chunk(c)
    def warm_chunks(s):
        if s.frames%4:return
        if getattr(s,"chunk_frame",-1)==s.frames:return
        center=int(s.cam[0])//320
        for c in sorted(range(max(0,center-3),min((COLS-1)//20,center+4)+1),key=lambda c:abs(c-center)):
            if (c,s.CHUNK_REV[0]) not in GameCore.CHUNK_CACHE:
                s.chunk_frame=s.frames; s.chunk(c); return
    def enter_pohjola(s,save):
        MUSIC.request("pohjola")
        for ar in ("pohjola",):sky_surface(ar);layers_for(ar);fog_surface(ar)
        for key in [(105,(130,153,254)),(70,(130,35,52))]:glow(*key)
        for phase in (1,2,3):louhi_frame("idle",0,phase=phase);louhi_frame("windup",0,phase=phase)
        save["bonfire"]="b9";save["louhi_unlocked"]=True
        write_save(save);s.start_session(save,s.p_pad[0] if s.p_pad and s.p_pad[0] is not None else s.kb);s.poht_t=0
        p=s.players[0];before=p.pad;p.pad=IdlePad();s.interact(p,("bonfire","b9"));s.state_name="poht";p.pad=before;s.coop_restore=True
        
    def start_session(s, save, p1pad):
        # v1.1 fix: everything transient from a previous session (e.g. a finished game's ending timer,
        # chunk images rendered with that world's opened shortcuts) is reset here
        s.ending_t = 0; s.hitstop = 0; s.shk_t = 0; s.shk_amp = 0; s.sep_t = 0; s.gain = []; s.dark = 0.0; s.dark_target = 0.0
        s.chunks = {}; s.hint = None; s.hint_t = 0; s.need_pad = None; s.end_page = 0; s.end_t = 0; s.kills = 0; s.ffs = []
        s.save = save; s.wd = World(); s.p_pad = [p1pad, None]
        for k in save["opened"]:
            if k in DYN: s.wd.state[k] = not DYN[k]["active"]
        for b in save["bosses"]:
            if b in ARENAS and ARENAS[b]["door_out"] and ("d_%s_out" % b) in DYN: s.wd.state["d_%s_out" % b] = False
        s.wd._rebuild()
        s.enemies = []; s.projs = []; s.zones = []; s.parts = Parts(); s.dns = []; s.boss = None; s.arena = None
        s.stains = save["stain"]; s.msgs = []; s.banner = None; s.dying = 0; s.hitstop = 0; s.felled = None
        s.t0 = save["time"] * 60; s.frames = 0; s.kills = 0; s.hints_seen = set();s.true_end_delay=0
        p = Player(s, 0, p1pad, save); s.players = [p]
        if save["bonfire"] not in save["seen"]: save["seen"].append(save["bonfire"])
        if save.get("mapseen") is None:       # 1.0 save: reveal what the player has provably explored
            ms = set()
            for bid in save["seen"]:
                if bid in BONFIRES: ms.add(map_cell(BONFIRES[bid], floor_row(BONFIRES[bid], BF_START[bid])))
            for k in save["bosses"]: ms.add("arena:" + k)
            save["mapseen"] = sorted(ms)
        s.mapseen = set(save["mapseen"])
        bx, by = bonfire_pos(save["bonfire"])
        p.refill(); p.spawn(bx - 26, by); p.face = 1
        s.spawn_enemies(); s.snap_cam(); s.area = area_at(int(p.x // TILE)); s.area_popup = (s.area, 0)
        s.state_name = "play"; s.init_fireflies()
        s.warm_all();s.enter_t=0
        s.aino_glimpse=None; s.tide=0; s.vel_end_t=0; s.current=0
        if save and "louhi" in save.get("bosses", []): s.wd.set_open("d_vellamo", True)
        if save and save.get("p2") and len(s.players)==1:
            other=physical_pad(s, p1pad)
            if other is not None: s.add_p2(save["p2"]["cls"], other)
    @property
    def coop(s): return len(s.players) > 1
    def save_game(s):
        if s.save is None: return False
        sv = s.save
        sv["time"] = int((s.t0 + s.frames) // 60); sv["level"] = 1 + sum(sv["stats"].values())
        sv["p2"] = s.players[1].ch if len(s.players) > 1 else sv.get("p2")
        if sv["p2"]: sv["p2"]["level"] = 1 + sum(sv["p2"]["stats"].values())
        sv["stain"] = s.stains; sv["mapseen"] = sorted(s.mapseen)
        return write_save(sv)
    def p2_char(s, cls):
        sv = s.save; p1lvl = 1 + sum(sv["stats"].values())
        ch = sv.get("p2")
        if not ch or ch["cls"] != cls: ch = {"cls": cls, "level": 1, "stats": {k: 0 for k in STAT_KEYS}, "souls": 0}
        order = {"warrior": ("vit", "str", "end", "foc"), "sage": ("foc", "vit", "end", "str"), "hunter": ("str", "end", "vit", "foc")}[cls]
        want = max(0, p1lvl - 3); have = sum(ch["stats"].values()); i = 0
        while have < want: ch["stats"][order[i % 4]] += 1; have += 1; i += 1
        ch["level"] = 1 + have; sv["p2"] = ch
        return ch
    def add_p2(s, cls, pad):
        if len(s.players) > 1 or s.save is None: return None
        ch = s.p2_char(cls); s.p_pad[1] = pad
        p = Player(s, 1, pad, ch); p.refill(); p0 = s.players[0]
        sx, sy = s.find_safe_xy(p0.x - p0.face * 14, p0.y, face=-p0.face, fallback=p0.safe)
        p.spawn(sx, sy); p.face = p0.face; p.safe = (sx, sy)
        s.players.append(p); sfx("join", 0.9); s.parts.burst(p.x, p.y - 10, P2_TINT[cls], 18, 1.6, 26)
        s.msg(tr("p2_joined", tr("cls_" + cls)))
        return p
    def remove_p2(s):
        if len(s.players) > 1:
            p = s.players.pop(1); s.p_pad[1] = None
            s.msg(tr("p2_left"))
    def msg(s, text, col=(255, 240, 200)):
        s.msgs.append([text, 200, col])
        if len(s.msgs) > 3: s.msgs.pop(0)
    # ---------- enemies ----------
    def spawn_enemies(s):
        s.enemies = [e for e in s.enemies if e.boss and not e.dead]
        s.projs = []; s.zones = []
        active=int(s.players[0].x//TILE) if s.players else 0
        if active>=446:trange=(446,487)
        else:trange=(0,446)
        for i,(k,tx,fr) in enumerate(SPAWNS):
            if abs(tx-active)>24 and not (420<=active<=445 and 400<=tx<=445):continue

            if any(abs(tx-bt)<=7 for bt in BONFIRES.values()):continue      # bonfires are safe ground
            x = tx * TILE + 8
            if k == "nakki":
                y = fr * TILE
                for ty in range(fr, ROWS):
                    if s.wd.tile(tx, ty) == WATER: y = ty * TILE + 8; break
            else:
                y = floor_row(tx, fr) * TILE
                if k in FLYERS: y -= 44
            s.enemies.append(Mob(s, k, x, y, i))
    def reset_boss(s):
        s.CHUNK_REV[0]+=1
        if s.boss is not None:
            if s.boss in s.enemies: s.enemies.remove(s.boss)
            k = s.boss.key; s.boss = None
            if ("d_%s_in" % k) in DYN: s.wd.set_open("d_%s_in" % k, True)
        s.arena = None
    def start_boss(s,key):
        if key=="louhi":
            for phase in (1,2,3):
                for pose in ("idle","windup","roar"):
                    spr=louhi_frame(pose,0,phase=phase);surf=pygame.Surface((W,H),pygame.SRCALPHA);surf.blit(spr,(0,0))
        a=ARENAS[key]
        s.wd.set_open("d_%s_in" % key, False); s.arena = key
        gy = a["ground"] * TILE
        span = a["x1"] - a["x0"]
        bx = (a["x0"] + max(8, min(12, span // 2))) if key in ("joukahainen", "ahti", "aino", "vellamo") else (a["x1"] - 5)
        b = BOSS_CLS[key](s, bx * TILE, gy)
        if key in ("joukahainen", "ahti", "aino", "vellamo"): b.face = -1
        s.boss = b; s.enemies.append(b); b.engage()
        for p in s.players:        # anyone left outside is carried in
            if p.alive() and not (a["x0"] + 1 <= p.x / TILE < a["x1"]):
                sx, sy = s.find_safe_xy((a["x0"] + 4) * TILE, gy, face=1)
                p.spawn(sx, sy); p.inv = 30; p.safe = (sx, sy)
        if key in ("joukahainen","ahti","aino","vellamo"):
            for p in s.players: p.inv=180
        center=(a["x0"]-1)*16//320
        for ci in (center-1, center, center+1):
            if 0<=ci<((COLS-1)//20+1): s.chunk(ci)
        if key in ("joukahainen","ahti","aino","vellamo"):
            for tx, _dir in ((a["x0"], -1), (a["x0"]+4, 1)):
                if tx>=486: s.chunk(tx//20); break
        s.snap_cam()
        MUSIC.request(a["track"]); b.shown_bar = 0.0
    def on_boss_dead(s, b):
        k = b.key; sv = s.save
        if k in ("joukahainen", "ahti"):
            if k not in sv["bosses"]: sv["bosses"].append(k)
            s.wd.set_open("d_%s_in" % k, True)
            s.felled = (k, 0)
            sv["bonfire"] = "b11" if k == "joukahainen" else "b12"
            s.save_game()
            gc.collect()
            return
        if k not in sv["bosses"]: sv["bosses"].append(k)
        a = ARENAS[k]
        if a["door_out"]: s.wd.set_open("d_%s_out" % k, True)
        s.wd.set_open("d_%s_in" % k, True)
        if k == "hiisi" and "feather" not in sv["taken"]:
            sv["taken"].append("feather")
            for p in s.players: p.recalc()
            s.msg(tr("found_item", tr("it_feather")), (255, 235, 150)); s.msg(tr("it_feather_d"), (200, 225, 200))
        s.felled = (k, 0); sfx("levelup", 0.9); s.shake(5, 30)
        s.parts.burst(b.x, b.y - 16, (255, 240, 180), 40, 3.0, 40, 2, 0.02, 0.5)
        if k == "tytti":
            sv["louhi_unlocked"]=True
            s.ending_t=1;s.save_game()
        elif k=="louhi":
            sv["done"]=True; sv["vellamo_unlocked"]=True
            s.wd.set_open("d_vellamo", True)
            s.save_game(); s.ending_t=0; s.end_t=0; s.true_end_delay=1
            s.msg(tr("vel_sign"), (160,240,210))
        elif k=="vellamo":
            sv["aino_freed"]=True; sv["vellamo_done"]=True; sv["ng_ready"]=True
            s.save_game(); s.vel_end_t=1
        else: s.save_game()
        gc.collect()
    def on_kill(s, e):
        s.kills += 1
    def enter_vellamo(s):
        sv=s.save; sv["vellamo_unlocked"]=True; sv["vellamo_visited"]=True; sv["bonfire"]="b10"
        if "b10" not in sv["seen"]: sv["seen"].append("b10")
        s.save_game(); s.poht_t=0; s.mapimg=None
        s.start_session(sv, s.p_pad[0] if s.p_pad[0] else s.kb)
        s.state_name="vellamo_arrival"
        MUSIC.request("ranta"); s.prewarm_vellamo()
    def prewarm_vellamo(s):
        for ar in ("ranta","syvanne","katedraali"):
            sky_surface(ar); layers_for(ar); fog_surface(ar)
        for ph in (1,2,3):
            for k in ("joukahainen","ahti","aino","vellamo"):
                for po in ("idle","windup","attack","roar","fish","maiden","reveal"):
                    newboss_frame(k, po, ph, 0)
        for ch in range(24, 28): s.chunk(ch)
    def start_aino_reveal(s):
        s.reset_boss(); s.state_name="aino_reveal"; s.reveal_t=0
        for p in s.players: p.spawn((646+p.idx*6)*TILE, 320); p.refill(); p.inv=180
        s.save["bonfire"]="b13"
        if "b13" not in s.save["seen"]: s.save["seen"].append("b13")
        s.save_game(); gc.collect()
    def start_vellamo_ending(s):
        gc.collect(); s.state_name="vellamo_ending"; s.vel_end_t=0
        s.save["vellamo_done"]=True; s.save["ng_ready"]=True; s.save_game()
    def water_level(s):
        return 228-s.tide if s.arena=="ahti" else 0
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
    # ---------- helpers used by entities ----------
    def nearest_player(s, x, y):
        best = None; bd = 1e9
        for p in s.players:
            if not p.alive(): continue
            d = abs(p.x - x) + abs(p.y - y) * 1.5
            if d < bd: bd = d; best = p
        return best
    def los(s, x1, y1, x2, y2):
        n = int(max(abs(x2 - x1), abs(y2 - y1)) // 8)
        for i in range(1, n):
            f = i / n
            if s.wd.solid(int((x1 + (x2 - x1) * f) // TILE), int((y1 + (y2 - y1) * f) // TILE)): return False
        return True
    def coop_mult(s, boss):
        if len(s.players) < 2: return 1.0
        return 1.8 if boss else 1.6
    def give_souls(s, n, x, y):
        if n <= 0: return
        for p in s.players:
            if p.alive(): p.souls += n; p.gain_t = 90; p.gain_n = getattr(p, "gain_n", 0) + n if getattr(p, "gain_t", 0) > 0 else n
        for i in range(min(12, 3 + n // 40)):
            s.parts.add(x, y, random.uniform(-1, 1), random.uniform(-1.8, -0.4), 36, (150, 230, 255), 1, 0.03)
    def dnum(s, x, y, val, col=(255, 255, 255), player=False):
        if not SETTINGS["dmgnum"]: return
        if len(s.dns) > 24: s.dns.pop(0)
        s.dns.append([x + random.randint(-4, 4), y, str(val) if not isinstance(val, str) else val, col, 0, isinstance(val, TStr)])
    def shake(s, amp, frames):
        if SETTINGS["shake"]: s.shk_amp = max(s.shk_amp if s.shk_t > 0 else 0, amp); s.shk_t = max(s.shk_t, frames)
    def spit_land(s, pr):
        ty = int(pr.y // TILE)
        for k in range(8):
            if s.wd.solid(int(pr.x // TILE), ty + k): y = (ty + k) * TILE; break
        else: return
        s.zones.append(Zone(pr.x, y, 24, 6, 0, 150, 12 * D()["dmg"], "puddle", 1.0, ("parry",)[:0]))
    def safe_ok(s, p):
        wd = s.wd; tx = int(p.x // TILE)
        for dx in (-1, 0, 1):
            for k in range(0, 3):
                if wd.tile(tx + dx, int(p.y // TILE) + k) in (THORN, WATER): return False
        return True
    def standing_free(s, x, y, w=PW_, h=PH_):
        """True if a body centred at x with feet at y stands on solid/platform, overlaps no solid, and is not in a hazard."""
        wd = s.wd; hw = w / 2.0
        # feet must rest on a surface
        foot = wd.tile(int(x // TILE), int(y // TILE))
        if foot not in (SOLID, PLAT) and not (foot == LADDER and wd.tile(int(x // TILE), int(y // TILE) - 1) != LADDER):
            # allow being a hair above the surface (spawn snap)
            if wd.tile(int(x // TILE), int((y + 1) // TILE)) not in (SOLID, PLAT): return False
            y = int((y + 1) // TILE) * TILE
        # body must not overlap solids (scan the AABB, ignore the floor row the feet stand on)
        top = int((y - h + 0.5) // TILE); bot = int((y - 1.0) // TILE)
        for ty in range(top, bot + 1):
            for tx in range(int((x - hw + 0.5) // TILE), int((x + hw - 0.5) // TILE) + 1):
                if wd.solid(tx, ty): return False
        # hazards at feet / shins
        for tx in range(int((x - hw + 1) // TILE), int((x + hw - 1) // TILE) + 1):
            for ty in (int((y - 3) // TILE), int((y - h * 0.5) // TILE), int(y // TILE)):
                if wd.tile(tx, ty) in (THORN, WATER): return False
        return True
    def find_safe_xy(s, x, y, face=1, fallback=None):
        """Nearest free standing spot near (x, y). Falls back to partner safe / last safe / bonfire."""
        # snap y down onto the first surface at this column
        def snap(xx, yy):
            tx = int(xx // TILE); ty0 = max(0, int(yy // TILE))
            for ty in range(ty0, min(ROWS, ty0 + 8)):
                if s.wd.tile(tx, ty) in (SOLID, PLAT): return xx, float(ty * TILE)
            for ty in range(ty0, -1, -1):
                if s.wd.tile(tx, ty) in (SOLID, PLAT): return xx, float(ty * TILE)
            return xx, yy
        x, y = snap(x, y)
        if s.standing_free(x, y): return x, y
        for dist in range(1, 18):
            for dx in (dist * face, -dist * face, dist, -dist):
                nx, ny = snap(x + dx * 4, y)
                if s.standing_free(nx, ny): return nx, ny
            for dy in (-dist, dist):
                nx, ny = snap(x, y + dy * TILE)
                if s.standing_free(nx, ny): return nx, ny
        # partner / own last safe ground
        for cand in (fallback,):
            if cand is None: continue
            cx, cy = snap(cand[0], cand[1])
            if s.standing_free(cx, cy): return cx, cy
        for p in s.players:
            if getattr(p, "safe", None):
                cx, cy = snap(p.safe[0], p.safe[1])
                if s.standing_free(cx, cy): return cx, cy
        if s.save is not None:
            bx, by = bonfire_pos(s.save["bonfire"]); return snap(bx, by)
        return x, y
    def poke_secret(s, rect):
        for k in ("secret_f", "secret_r"):
            if not s.wd.state[k]: continue
            for (tx, ty) in DYN[k]["tiles"]:
                if rect[0] < tx * TILE + TILE and rect[0] + rect[2] > tx * TILE and rect[1] < ty * TILE + TILE and rect[1] + rect[3] > ty * TILE:
                    s.open_dyn(k, True); return
    def open_dyn(s, k, silent=False):
        s.CHUNK_REV[0]+=1
        d = DYN[k]; s.wd.state[k] = not d["active"]; s.wd._rebuild()
        if k not in s.save["opened"]: s.save["opened"].append(k)
        tx, ty = d["tiles"][len(d["tiles"]) // 2]
        if d["key"] == "wall":
            sfx("boom", 0.7); s.shake(3, 12)
            for ty2 in range(d["tiles"][0][1], d["tiles"][-1][1] + 1):
                s.parts.burst(tx * TILE + 8, ty2 * TILE + 8, (150, 150, 170), 10, 2.0, 24, 2, 0.12, 0.8)
            s.msg(tr("secret_found"), (200, 220, 255))
        else: sfx("gate", 0.9); s.shake(2, 20)
    # ---------- player events ----------
    def player_down(s, p):
        sfx("die", 0.8)
        others = [q for q in s.players if q is not p and q.alive()]
        p.vx = 0; p.vy = min(p.vy, 0)
        if others:
            # snap onto safe ground so the body doesn't fall away from a helper
            sx, sy = s.find_safe_xy(p.x, p.y, fallback=p.safe)
            p.x, p.y = sx, sy; p.on_ground = True; p.safe = (sx, sy)
            p.state = "down"; p.down_t = 1200; p.revive_t = 0; p.hp = 0
            s.msg(tr("p_down", tr("pl_%d" % (p.idx + 1))), (255, 150, 150))
        else:
            p.state = "dead"; s.begin_death()
    def on_player_dead(s, p):
        if not any(q.alive() for q in s.players): s.begin_death()
    def begin_death(s):
        if s.dying: return
        s.dying = 1; sfx("die", 1.0); MUSIC.request(None) if False else None
        sv = s.save; sv["deaths"] += 1
        if SETTINGS["penalty"] == "classic":
            s.stains[:] = [x for x in s.stains if x["p"] not in [p.idx for p in s.players]]
            for p in s.players:
                if p.souls > 0:
                    x, y = (p.x, p.y) if (p.on_ground and s.safe_ok(p)) else p.safe
                    s.stains.append({"p": p.idx, "x": float(x), "y": float(y), "souls": p.souls}); p.souls = 0
    def respawn(s):
        if s.players and 446*TILE<=s.players[0].x<486*TILE:s.save["bonfire"]="b9"
        sv = s.save; bx, by = bonfire_pos(sv["bonfire"])
        s.reset_boss()
        for i, p in enumerate(s.players):
            sx, sy = s.find_safe_xy(bx + (24 if i else -26), by, face=1 if i else -1)
            p.refill(); p.spawn(sx, sy); p.face = 1; p.safe = (sx, sy)
        s.dying = 0; s.felled = None; s.dns = []
        s.spawn_enemies(); s.snap_cam(); s.save_game()
        s.area_popup = None
    def rest_at(s, p, bid):
        sv = s.save; first = bid not in sv["seen"]
        sv["bonfire"] = bid
        if first: sv["seen"].append(bid)
        for q in s.players:
            if q.state in ("down", "dead"): q.state = "free"; q.spawn(q.x, q.y)
            q.refill(); q.inv = 20
        s.reset_boss(); s.spawn_enemies(); s.dns = []
        sfx("bonfire", 1.0); bx, by = bonfire_pos(bid)
        s.parts.burst(bx, by - 14, (255, 190, 90), 24, 1.8, 36, 1, -0.02, 0.9)
        s.save_game()
        return first
    def interact(s, p, near):
        kind, ident = near
        if kind == "vellamo_gate":
            if _gate_unlocked(s): sfx("confirm", 0.7); s.enter_vellamo()
            return
        if kind == "bonfire":
            first = s.rest_at(p, ident)
            if first: s.banner = [tr("bonfire_lit"), 0]
            s.menu_owner = p.idx; s.open_bonfire()
        elif kind == "lever":
            lv = LEVERS[ident]; k = lv["opens"]
            if not s.wd.opened(k) if DYN[k]["code"] == SOLID else not s.wd.state[k]:
                sfx("lever", 0.9); s.open_dyn(k)
                s.msg(tr("lever_" + ident), (220, 230, 255))
    def buy_stat(s, p, k):
        lv = p.level
        if lv >= MAX_LEVEL: return False
        cost = level_cost(lv)
        if p.souls < cost: return False
        p.souls -= cost; p.ch["stats"][k] += 1; p.ch["level"] = p.level
        ohp = p.maxhp; p.recalc(); p.hp = min(p.maxhp, p.hp + (p.maxhp - ohp))
        sfx("levelup", 0.8)
        return True
    # ---------- items / interactables ----------
    def item_xy(s, k):
        tx, ty, kind, pl = ITEMS[k]
        return tx * TILE + 8, ty * TILE - 6
    def interactables(s):
        out = []
        for bid in BONFIRES:
            x, y = bonfire_pos(bid); out.append((x, y, "bonfire", bid))
        for lid, lv in LEVERS.items():
            k = lv["opens"]
            done = (not s.wd.state[k]) if DYN[k]["code"] == SOLID else s.wd.state[k]
            if not done: out.append((lv["tx"] * TILE + 8, lv["ty"] * TILE, "lever", lid))
        if _gate_unlocked(s): out.append((_VELLAMO_GATE[0], _VELLAMO_GATE[1], "vellamo_gate", "gate"))
        return out
    def nearby_for(s, p, its):
        best = None; bd = 1e9
        for (x, y, kind, ident) in its:
            dx = abs(p.x - x); dy = abs(p.y - y)
            if dx < 18 and dy < 26 and dx + dy < bd: bd = dx + dy; best = (kind, ident)
        return best
    def pickup(s, p, k):
        tx, ty, kind, pl = ITEMS[k]; sv = s.save
        sv["taken"].append(k); sfx("pickup", 0.9)
        x, y = s.item_xy(k); s.parts.burst(x, y, (255, 230, 150), 14, 1.6, 26, 1, -0.01, 0.6)
        name = desc = None
        if kind == "souls":
            p.souls += pl; s.msg(tr("got_souls", pl), (150, 230, 255))
        elif kind == "charm":
            for q in s.players: q.recalc()
            name, desc = tr("it_" + k), tr("it_" + k + "_d")
        elif kind == "flask":
            for q in s.players: q.recalc(); q.flasks += 1
            name, desc = tr("it_flask"), tr("it_flask_d")
        elif kind == "flaskpow":
            for q in s.players: q.recalc()
            name, desc = tr("it_flaskpow"), tr("it_flaskpow_d")
        if name:
            s.msg(tr("found_item", name), (255, 235, 150)); s.msg(desc, (200, 225, 200))
    # ---------- per-frame world update ----------
    def update_world(s):
        s.frames += 1
        wd = s.wd
        if not SETTINGS["flash"]:
            for e in s.enemies: e.flash = 0
            for p in s.players: p.flash = 0
        # death sequence
        if s.dying:
            s.dying += 1
            if s.dying > 190: s.respawn(); return
        # players
        its = s.interactables()
        for p in s.players:
            p.nearby = s.nearby_for(p, its) if p.alive() and not s.dying else None
        if s.hitstop > 0:
            s.hitstop -= 1
            s.parts.update(); s.tick_fx(); return
        for p in s.players: p.update()
        self_hz = [p for p in s.players if p.alive()]
        for p in self_hz:
            if p.climb: continue
            if hazard_at(wd, p) or p.y > ROWS * TILE - 12:
                s.hazard(p)
        # revive
        for d in s.players:
            if d.state != "down": continue
            helper = [q for q in s.players if q is not d and q.alive() and abs(q.x - d.x) < 40 and abs(q.y - d.y) < 40 and q.pad.held("up")]
            if helper:
                d.revive_t += 1
                q = helper[0]; q.inv = max(q.inv, 10)   # helping is committing: brief i-frames so a hit doesn't cancel the revive
                if abs(q.x - d.x) > 14:
                    q.x = d.x - (14 if q.x < d.x else -14); q.vx = 0
                if abs(q.y - d.y) > 20: q.y = d.y; q.vy = 0
            else: d.revive_t = max(0, d.revive_t - 2)
            if d.revive_t >= 70:
                sx, sy = s.find_safe_xy(d.x, d.y, fallback=d.safe)
                d.x, d.y = sx, sy; d.safe = (sx, sy)
                d.state = "free"; d.hp = d.maxhp * 0.4; d.inv = 90; d.revive_t = 0; d.stam = d.maxst
                sfx("revive", 0.9); s.parts.burst(d.x, d.y - 10, (150, 255, 180), 20, 1.6, 30, 1, -0.02, 0.7)
                s.msg(tr("p_revived", tr("pl_%d" % (d.idx + 1))), (170, 255, 190))
        # co-op: both downed
        if s.coop and not s.dying and not any(p.alive() for p in s.players): s.begin_death()
        # enemies
        ccx = s.cam[0] + W / 2; ccy = s.cam[1] + H / 2
        for e in s.enemies:
            if e.boss or (abs(e.x - ccx) < 330 and abs(e.y - ccy) < 240):
                e.update()
        s.enemies = [e for e in s.enemies if not (e.dead and e.dt > (40 if not e.boss else 240))]
        # projectiles / zones
        s.update_projs()
        for z in s.zones: z.update(s)
        s.zones = [z for z in s.zones if not z.dead]
        s.resolve_enemy_hits()
        s.update_arena()
        s.update_items()
        s.parts.update(); s.tick_fx()
        s.update_camera(); s.warm_chunks()
        s.update_area()
    def tick_fx(s):
        if s.shk_t > 0: s.shk_t -= 1
        for d in s.dns: d[4] += 1; d[1] -= 0.35
        s.dns = [d for d in s.dns if d[4] < 40]
        for m in s.msgs: m[1] -= 1
        s.msgs = [m for m in s.msgs if m[1] > 0]
        if s.banner:
            s.banner[1] += 1
            if s.banner[1] > 150: s.banner = None
        if s.felled:
            s.felled = (s.felled[0], s.felled[1] + 1)
            if s.felled[1] > 220: s.felled = None
        if s.area_popup:
            s.area_popup = (s.area_popup[0], s.area_popup[1] + 1)
            if s.area_popup[1] > 220: s.area_popup = None
        for p in s.players:
            if getattr(p, "gain_t", 0) > 0: p.gain_t -= 1
    def hazard(s, p):
        if p.x>=486*TILE:
            p.vy=min(p.vy, .8); return
        if p.inv > 0 and p.state == "roll": pass
        dmg = max(12.0, p.maxhp * 0.15)
        sfx("splash", 0.7); s.parts.burst(p.x, p.y - 4, (150, 200, 255), 10, 1.4, 20, 1, 0.1, 1.5)
        p.hp -= dmg; s.dnum(p.x, p.y - 26, int(dmg), (255, 90, 90), True)
        if p.hp <= 0: p.die(); return
        p.x, p.y = p.safe; p.vx = p.vy = 0; p.inv = 60; p.state = "free"; p.atk = None; p.act = None; p.climb = False; p.flash = 6
    def update_projs(s):
        for pr in s.projs: pr.update(s)
        for pr in s.projs:
            if pr.dead: continue
            if pr.enemy:
                for p in s.players:
                    if not p.alive() or p.idx in pr.hit: continue
                    if ov(pr.rect(), p.hurt_rect()):
                        r = p.take_hit(pr.dmg, pr.x - pr.vx * 2, pr.kbx, pr.tags, pr)
                        if pr.enemy is False: break
                        if r or p.inv > 0:
                            pr.hit.add(p.idx)
                            if pr.kind != "wave": pr.dead = True
                            break
            else:
                for e in s.enemies:
                    if e.dead or e.hidden or e.invuln or id(e) in pr.hit: continue
                    if ov(pr.rect(), e.hurt_rect()):
                        pr.hit.add(id(e)); pl = s.players[pr.pid] if pr.pid < len(s.players) else None
                        tg = set(pr.tags)
                        if e.take(pr.dmg, pr.vx * 0.5, pr.poise, pl, tg, 0.0) and pl is not None and pl.cls == "sage": pl.focus = min(pl.maxfoc, pl.focus + 2)
                        if pr.pierce > 0: pr.pierce -= 1
                        else: pr.dead = True; s.parts.burst(pr.x, pr.y, pr.col, 5, 1.0, 12)
                        break
        s.projs = [p for p in s.projs if not p.dead]
    def resolve_enemy_hits(s):
        for e in s.enemies:
            if e.dead: continue
            a = e.atk
            if not a: continue
            r = a.rect(e.x, e.y, e.face)
            for p in s.players:
                if not p.alive() or p.idx in a.hit: continue
                if ov(r, p.hurt_rect()):
                    a.hit.add(p.idx)
                    p.take_hit(a.dmg, e.x, a.kb, a.tags, e)
        for z in s.zones:
            if not z.active or z.dmg <= 0: continue
            r = z.rect()
            for p in s.players:
                if not p.alive(): continue
                last = z.hit_t.get(p.idx) if hasattr(z, "hit_t") else None
                if z.style == "puddle":
                    if not hasattr(z, "hit_t"): z.hit_t = {}
                    if last is not None and z.t - last < 50: continue
                elif p.idx in z.hit: continue
                if ov(r, p.hurt_rect()):
                    if z.style == "puddle": z.hit_t[p.idx] = z.t
                    else: z.hit.add(p.idx)
                    p.take_hit(z.dmg, z.x, z.kb, z.tags, None)
    def update_arena(s):
        if s.boss is None:
            if s.dying: return
            for key, a in ARENAS.items():
                if key in s.save["bosses"]: continue
                x0 = (a["x0"] + 3) * TILE; x1 = (a["x1"] - 1) * TILE; yt = a["y0"] * TILE; yb = (a["ground"] + 1) * TILE
                for p in s.players:
                    if p.alive() and x0 < p.x < x1 and yt - 8 < p.y < yb + 8:
                        s.start_boss(key); return
        else:
            b = s.boss
            if b.dead:
                if b.dt > 160 and s.arena:
                    s.arena = None; MUSIC.request(s.area)
                if b.dt > 240: s.boss = None
        if isinstance(s.boss, WaterBoss):
            k=s.boss.key; ph=s.boss.phase
            suffix="3" if ph>=3 else "2" if ph>=1.5 else ""
            MUSIC.request(k+suffix if k+suffix in TRACK_ORDER else k)
            if k=="ahti": s.tide=int(math.sin(s.frames*.015)*10)+(22 if ph>=2 else 0)
    def update_items(s):
        if s.dying: return
        taken = s.save["taken"]
        for k in ITEMS:
            if k in taken: continue
            x, y = s.item_xy(k)
            for p in s.players:
                if p.alive() and abs(p.x - x) < 11 and abs(p.y - 8 - y) < 18:
                    s.pickup(p, k); break
        for st in list(s.stains):
            for p in s.players:
                if p.idx == st["p"] and p.alive() and abs(p.x - st["x"]) < 14 and abs(p.y - st["y"]) < 22:
                    p.souls += st["souls"]; s.stains.remove(st); sfx("souls", 1.0)
                    s.parts.burst(st["x"], st["y"] - 10, (150, 230, 255), 24, 1.8, 30, 1, -0.03, 0.8)
                    s.msg(tr("stain_back", st["souls"]), (150, 230, 255)); break
    def explore(s):
        """fog of war: mark the map cells (and boss rooms) the players are in"""
        for q in s.players:
            if not q.alive(): continue
            tx = int(q.x // TILE); ty = int((q.y - 8) // TILE)
            s.mapseen.add(map_cell(tx, ty))
            for k, ar in ARENAS.items():
                if ar["x0"] < tx < ar["x1"] and ar["y0"] <= ty <= ar["ground"]: s.mapseen.add("arena:" + k)
        if s.boss is not None: s.mapseen.add("arena:" + s.boss.key)
    def update_area(s):
        if s.frames % 6 == 0: s.explore()
        p = s.players[0]; a = area_at(int(p.x // TILE))
        if a != s.area:
            s.area = a; s.area_popup = (a, 0)
        if s.boss is None or s.boss.dead:
            MUSIC.request(s.area)
        elif s.boss.engaged:          # phase 2 (from the transition roar on) gets the intensified version
            MUSIC.request("louhi" if s.boss.key=="louhi" and s.boss.phase==1 else "louhi2" if s.boss.key=="louhi" and s.boss.phase<2.5 else "louhi3" if s.boss.key=="louhi" else ARENAS[s.boss.key]["track"]+("2" if s.boss.phase>=1.5 else ""))
        pm = [q for q in s.players if q.alive()] or s.players
        dy = sum(q.y for q in pm) / len(pm)
        s.dark_target = max(0.0, min(1.0, (dy - 31 * TILE) / (4 * TILE)))
        if s.arena: s.dark_target = 0.35
        if s.area=="pohjola":s.dark_target=.67
        s.dark += (s.dark_target - s.dark) * 0.04
        if s.area in ("ranta","syvanne","katedraali"):
            tx=int(s.players[0].x//TILE); s.save["vellamo_visited"]=True
            if not s.aino_glimpse and not s.boss:
                if 493<=tx<499: s.aino_glimpse=(510*TILE, 0.)
                elif 548<=tx<554: s.aino_glimpse=(562*TILE, 0.)
                elif 602<=tx<609: s.aino_glimpse=(615*TILE, 0.)
            if s.aino_glimpse:
                x,t=s.aino_glimpse
                if t>28: x+=1.5
                s.aino_glimpse=(x, t+1) if t<150 else None
            if s.boss and s.boss.key=="vellamo" and s.boss.dead: s.vel_end_t+=1
            if s.vel_end_t>130: s.start_vellamo_ending()
        if s.frames==3 and _gate_unlocked(s) and s.area=="pohjola":
            s.msg(tr("vel_sign"), (160,240,210))
    # ---------- camera ----------
    def cam_goal(s):
        alive = [p for p in s.players if p.alive()] or s.players
        mx = sum(p.x for p in alive) / len(alive); my = sum(p.y - 10 for p in alive) / len(alive)
        lead = alive[0].face * 16 if len(alive) == 1 else 0
        tx = mx + lead - W / 2; ty = my - H * 0.56
        if s.arena:
            a = ARENAS[s.arena]
            room_l, room_r = a["x0"] * TILE, a["x1"] * TILE
            ty = a["ground"] * TILE + 8 - H
            margin = 36
            if room_r - room_l <= W:
                tx = room_l - 8
            else:
                if s.boss is not None and not s.boss.dead:
                    left = min(mx - 12, s.boss.x - 40)
                    right = max(mx + 12, s.boss.x + 40)
                else:
                    left, right = mx - 20, mx + 20
                if right - left <= W - 2 * margin:
                    tx = left - margin
                else:
                    tx = (left + right) * 0.5 - W * 0.5
                tx = max(room_l, min(room_r - W, tx))
        tx = max(0, min(COLS * TILE - W, tx)); ty = max(0, min(ROWS * TILE - H, ty))
        return tx, ty
    def snap_cam(s):
        s.cam[0], s.cam[1] = s.cam_goal()
    def update_camera(s):
        tx, ty = s.cam_goal()
        k = 0.2 if s.arena else 0.1
        s.cam[0] += (tx - s.cam[0]) * k; s.cam[1] += (ty - s.cam[1]) * (0.2 if s.arena else 0.08)
        s.cam[0] = max(0, min(COLS * TILE - W, s.cam[0])); s.cam[1] = max(0, min(ROWS * TILE - H, s.cam[1]))
        if s.coop and not s.dying:
            al = [p for p in s.players if p.alive()]
            if len(al) == 2:
                pinned = False
                reviving = any(p.state == "down" and p.revive_t > 0 for p in s.players)
                for p in al:
                    if reviving: continue          # don't yank a helper off a revive
                    lo = s.cam[0] + 8; hi = s.cam[0] + W - 8
                    if p.x < lo or p.x > hi:
                        nx = lo if p.x < lo else hi
                        sx, sy = s.find_safe_xy(nx, p.y, face=1 if p.x < lo else -1, fallback=p.safe)
                        p.x, p.y = sx, sy; p.vx = max(0, p.vx) if p.x < lo + 1 else min(0, p.vx); pinned = True
                far = abs(al[0].y - al[1].y) > 120 or abs(al[0].x - al[1].x) > W + 40
                offy = any(not (s.cam[1] - 6 < p.y - 10 < s.cam[1] + H + 6) for p in al)
                if far or offy or (pinned and abs(al[0].x - al[1].x) > W - 24): s.sep_t += 1
                else: s.sep_t = max(0, s.sep_t - 2)
                if s.sep_t > 150 and not s.arena:
                    s.sep_t = 0
                    a, b = al
                    lag = a if (abs(a.x - (s.cam[0] + W / 2)) + abs(a.y - (s.cam[1] + H / 2))) > (abs(b.x - (s.cam[0] + W / 2)) + abs(b.y - (s.cam[1] + H / 2))) else b
                    oth = b if lag is a else a
                    sx, sy = s.find_safe_xy(oth.x - oth.face * 14, oth.y, face=-oth.face, fallback=oth.safe)
                    lag.x, lag.y = sx, sy; lag.vx = lag.vy = 0; lag.inv = max(lag.inv, 40); lag.safe = (sx, sy); lag.on_ground = True
                    sfx("join", 0.7); s.parts.burst(lag.x, lag.y - 10, (200, 220, 255), 14, 1.4, 22)
            else: s.sep_t = 0
    # ---------- fireflies ----------
    def init_fireflies(s):
        r = random.Random(11)
        s.ffs = [[r.uniform(0, W), r.uniform(20, H - 10), r.uniform(-0.15, 0.15), r.uniform(-0.1, 0.1), r.uniform(0, 6.28)] for _ in range(22)]
    # ---------- world drawing ----------
    def draw_world(s, c, t):
        wd = s.wd; cx = int(s.cam[0]); cy = int(s.cam[1]); area = area_at(int((cx + W // 2) // TILE))
        pal = PAL[area]
        water = area in ("ranta", "syvanne", "katedraali")
        if water:
            for ch in range(cx // 320, min((COLS * TILE - 1) // 320, (cx + W - 1) // 320) + 1):
                strip = s.chunk(ch)
                if strip.get_colorkey() is None: strip.set_colorkey((0, 0, 0))
        c.blit(sky_surface(area), (0, 0))
        for (lay, f, yo) in layers_for(area):
            lw, lh = lay.get_size()
            y = H - lh + yo // 2 - int((cy - 370) * f * 0.45)
            x = -int(cx * f) % lw
            c.blit(lay, (x - lw, y)); c.blit(lay, (x, y))
            if x + lw < W: c.blit(lay, (x + lw, y))
        for ch in range(cx // 320, min((COLS * TILE - 1) // 320, (cx + W - 1) // 320) + 1):
            c.blit(s.chunk(ch), (ch * 320 - cx, -cy))
        # dynamic tiles
        for k, d in DYN.items():
            if not wd.state[k]: continue
            tl = d["tiles"]; x0 = tl[0][0] * TILE - cx; y0 = tl[0][1] * TILE - cy
            nx = tl[-1][0] - tl[0][0] + 1; ny = tl[-1][1] - tl[0][1] + 1
            if x0 > W or y0 > H or x0 + nx * TILE < 0 or y0 + ny * TILE < 0: continue
            kind = d["key"]
            if kind == "fog": c.blit(fog_door(nx, ny, t), (x0, y0))
            else: c.blit(dyn_tile_surf(kind, nx, ny), (x0, y0))
        # props
        its = s.interactables()
        seen = s.save["seen"]
        for (x, y, kind, ident) in its:
            sx = x - cx; sy = y - cy
            if -20 < sx < W + 20 and -30 < sy < H + 30:
                if kind == "bonfire": s.draw_bonfire(c, sx, sy, ident in seen, t)
                else: s.draw_lever(c, sx, sy, t)
        for k, (tx, ty, kind, pl) in ITEMS.items():
            if k in s.save["taken"]: continue
            sx = tx * TILE + 8 - cx; sy = ty * TILE - 6 - cy
            if -10 < sx < W + 10 and -10 < sy < H + 10: s.draw_item(c, sx, sy, kind, t, k)
        # lever already pulled: draw handle flipped
        for lid, lv in LEVERS.items():
            k = lv["opens"]; done = (not wd.state[k]) if DYN[k]["code"] == SOLID else wd.state[k]
            if done:
                sx = lv["tx"] * TILE + 8 - cx; sy = lv["ty"] * TILE - cy
                if -20 < sx < W + 20 and -30 < sy < H + 30: s.draw_lever(c, sx, sy, t, True)
        for st in s.stains:
            sx = int(st["x"] - cx); sy = int(st["y"] - cy)
            if -20 < sx < W + 20 and -30 < sy < H + 30:
                bob = int(math.sin(t * 0.08) * 2)
                pygame.draw.circle(c, (60, 120, 160), (sx, sy - 10 + bob), 5); pygame.draw.circle(c, (170, 235, 255), (sx, sy - 10 + bob), 3)
                c.fill((255, 255, 255), (sx - 1, sy - 12 + bob, 2, 2))
                for k in range(3): c.fill((150, 220, 255), (sx - 4 + ((t // 3 + k * 5) % 9), sy - 4 - ((t // 2 + k * 7) % 14), 1, 1))
        for e in s.enemies:
            if -105 < e.x - cx < W + 105 and -60 < e.y - cy < H + 80: e.draw(c, cx, cy)
        for z in s.zones:
            if -z.w-20<z.x-cx<W+z.w+20:z.draw(c,cx,cy)
        for p in s.players:
            p.draw(c, cx, cy)
        for pr in s.projs:
            if -20<pr.x-cx<W+20 and -20<pr.y-cy<H+30:pr.draw(c,cx,cy)
        s.parts.draw(c, cx, cy)
        # fog: water realms use a clear mist, not the opaque land fog
        if water:
            fs = getattr(GameCore, "_water_blank", None)
            if fs is None:
                fs = pygame.Surface((1, 1), pygame.SRCALPHA)
                GameCore._water_blank = fs
        else:
            fs = fog_surface(area)
        for (yy, f, sp) in ((H - 74, 1.25, 0.25), (H - 40, 1.6, -0.35)):
            fx = -int(cx * f + t * sp) % 640
            c.blit(fs, (fx - 640, yy)); c.blit(fs, (fx, yy))
        # light
        s.draw_light(c, t, cx, cy, pal)
        # fireflies (after lighting: they glow)
        fc = {"forest": (220, 255, 120), "swamp": (180, 255, 110), "river": (170, 200, 255), "pohjola":(106,138,225), "ranta":(100,210,176), "syvanne":(130,160,231), "katedraali":(153,221,190)}[area]
        for f in s.ffs:
            f[0] = (f[0] + f[2] + math.sin(t * 0.03 + f[4]) * 0.2 - (s.cam[0] - getattr(s, "_pcx", s.cam[0])) * 0.6) % (W + 10)
            f[1] = (f[1] + f[3] + math.cos(t * 0.027 + f[4]) * 0.18 - (s.cam[1] - getattr(s, "_pcy", s.cam[1])) * 0.6) % (H + 10)
            a = 0.5 + 0.5 * math.sin(t * 0.07 + f[4] * 3)
            if a > 0.25:
                col = (int(fc[0] * a), int(fc[1] * a), int(fc[2] * a)); c.fill(col, (int(f[0]) - 5, int(f[1]) - 5, 2, 2))
                if a > 0.8: c.fill((255, 255, 230), (int(f[0]) - 5, int(f[1]) - 5, 1, 1))
        s._pcx = s.cam[0]; s._pcy = s.cam[1]
        if getattr(s, "aino_glimpse", None):
            aino_glimpse(c, int(s.aino_glimpse[0]-s.cam[0]), t)
        if area in ("ranta","syvanne","katedraali"):
            tide=getattr(s, "tide", 0)
            for x in (-12,77,198,281):
                y=124+int(math.sin(x*.07+t*.04)*3)+tide//2
                pygame.draw.arc(c,(65,127,146),(x,y,18,6),.15,2.9,1)
        if _gate_unlocked(s) and area=="pohjola":
            x=int(_VELLAMO_GATE[0]-s.cam[0]); y=int(_VELLAMO_GATE[1]-s.cam[1])
            pygame.draw.rect(c,(35,116,133),(x-8,y-43,16,43),1)
            pygame.draw.rect(c,(67,182,184),(x-5,y-40,10,37),1)
            for k in range(3): pygame.draw.circle(c,(124,224,205),(x-6+k*6,y-35-((t//5+k*7)%25)),1)
            s.text(tr("vel_entrance"), x, y-51, (164,234,205), s.tiny)
    def draw_light(s, c, t, cx, cy, pal):
        water = s.area in ("ranta", "syvanne", "katedraali")
        saved_ff = None
        if water:
            saved_ff = s.ffs
            s.ffs = []
            pal = dict(pal, ambient={"ranta": (184, 208, 214), "syvanne": (187, 209, 231), "katedraali": (184, 214, 201)}[s.area])
        amb = pal["ambient"]; dk = s.dark
        night = (62, 68, 86)
        base = tuple(int(amb[i] + (night[i] - amb[i]) * dk) for i in range(3))
        lm = s.lightmap; lm.fill(base)
        fl = 0.9 + 0.1 * math.sin(t * 0.37) + 0.05 * math.sin(t * 0.13)
        def lit(x, y, r, col, f=1.0):
            if -r < x < W + r and -r < y < H + r:
                lm.blit(glow(r, tuple(min(255, int(v * f)) for v in col)), (int(x - r), int(y - r)), special_flags=pygame.BLEND_ADD)
        for bid in BONFIRES:
            x, y = bonfire_pos(bid)
            if bid in s.save["seen"]: lit(x - cx, y - cy - 10, 74, (255, 170, 80), fl)
            else: lit(x - cx, y - cy - 6, 14, (90, 40, 20))
        for p in s.players:
            if p.alive():
                col = (110, 100, 80) if p.cls != "sage" else (70, 110, 120)
                lit(p.x - cx, p.y - cy - 12, 44 + int(26 * dk), col)
        for e in s.enemies:
            if e.dead and e.dt > 20: continue
            if e.kind in ("virvatuli", "henki", "haamu", "tytti", "turso", "joutsen"):
                lit(e.x - cx, e.y - cy - e.h / 2, 28 if not e.boss else 56, {"virvatuli": (60, 150, 255), "henki": (60, 150, 140), "haamu": (60, 80, 140), "tytti": (160, 70, 150), "turso": (50, 90, 160), "joutsen": (90, 100, 140)}[e.kind])
            elif e.kind=="louhi":
                lit(e.x-cx,e.y-cy-58,105,(130,153,254),1.05)
                if e.warn:lit(e.x-cx,e.y-cy-58,70,(130,35,52))
            elif e.kind == "hiisi": lit(e.x - cx, e.y - cy - 20, 40, (120, 60, 30))
        for pr in s.projs: lit(pr.x - cx, pr.y - cy, 18, tuple(v // 2 for v in pr.col))
        for z in s.zones:
            if z.active and z.style in ("beam", "geyser"): lit(z.x - cx, z.y - cy - z.h / 2, 30, (120, 80, 120) if z.style == "beam" else (60, 100, 140))
        for f in s.ffs[::3]:
            lit(f[0] - 5, f[1] - 5, 9, (50, 60, 20))
        for st in s.stains: lit(st["x"] - cx, st["y"] - cy - 10, 22, (50, 100, 140))
        for k, (tx, ty, kind, pl) in ITEMS.items():
            if k not in s.save["taken"]: lit(tx * TILE + 8 - cx, ty * TILE - 6 - cy, 18, (90, 80, 40))
        c.blit(lm, (0, 0), special_flags=pygame.BLEND_MULT)
        c.blit(vignette(), (0, 0), special_flags=pygame.BLEND_MULT)
        if water:
            s.ffs = saved_ff
            fc = {"ranta": (99, 220, 161), "syvanne": (128, 200, 198), "katedraali": (172, 228, 198)}[s.area]
            for i in range(4):
                xx = (i * 83 + t // 17) % 317; yy = 111 + (i * 19) % 30
                w = 5 + int(3 * math.sin(t * .017 + i))
                pygame.draw.arc(c, (30, 78, 94), (xx, yy, w, 5), .4, 2.7, 1)
            for f in s.ffs[:30]:
                if f[0] > cx - 10 and f[0] < cx + 330: c.fill(fc, (int(f[0] - cx), int(f[1] - cy), 2, 2))
    def draw_bonfire(s, c, x, y, lit, t):
        x = int(x); y = int(y)
        pygame.draw.rect(c, (36, 34, 40), (x - 8, y - 3, 16, 3)); pygame.draw.rect(c, (70, 68, 78), (x - 8, y - 3, 16, 1))
        pygame.draw.line(c, (74, 50, 32), (x - 7, y - 4), (x + 5, y - 9), 2); pygame.draw.line(c, (96, 66, 40), (x + 7, y - 4), (x - 5, y - 9), 2)
        if lit:
            f = (t // 3) % 4; hgt = 14 + (f % 2) * 2 + int(math.sin(t * 0.3) * 1.5)
            pygame.draw.polygon(c, (214, 80, 30), [(x - 6, y - 7), (x - 2 + (f % 2), y - 7 - hgt + 2), (x + 1, y - 7 - hgt // 2), (x + 3, y - 7 - hgt), (x + 6, y - 7)])
            pygame.draw.polygon(c, (255, 170, 50), [(x - 4, y - 7), (x - 1, y - 7 - hgt + 5), (x + 1, y - 7 - hgt // 2 + 2), (x + 2 + (f % 2), y - 7 - hgt + 3), (x + 4, y - 7)])
            pygame.draw.polygon(c, (255, 235, 150), [(x - 2, y - 7), (x, y - 7 - hgt // 2 - 1), (x + 2, y - 7)])
            if s.state_name == "play" and t % 9 == 0 and random.random() < 0.7: s.parts.add(x + s.cam[0] + random.randint(-3, 3), y + s.cam[1] - 14, random.uniform(-0.2, 0.2), -0.5, 30, (255, 190, 90), 1, -0.005)
        else:
            c.fill((120, 50, 30), (x - 1, y - 8, 2, 1))
            if (t // 20) % 2 == 0: c.fill((190, 90, 40), (x, y - 9, 1, 1))
    def draw_lever(s, c, x, y, t, pulled=False):
        x = int(x); y = int(y)
        pygame.draw.rect(c, (60, 60, 70), (x - 5, y - 3, 10, 3)); pygame.draw.rect(c, (110, 110, 124), (x - 5, y - 3, 10, 1))
        pygame.draw.rect(c, (70, 52, 36), (x - 1, y - 6, 2, 3))
        dx = -6 if pulled else 6
        pygame.draw.line(c, (140, 100, 60), (x, y - 5), (x + dx, y - 12), 2); c.fill((220, 60, 50), (x + dx - 1, y - 14, 3, 3))
        if not pulled and (t // 30) % 2 == 0: c.fill((255, 255, 255), (x + dx, y - 14, 1, 1))
    def draw_item(s, c, x, y, kind, t, k):
        x = int(x); y = int(y + math.sin(t * 0.07 + x) * 1.5)
        if kind == "souls":
            pygame.draw.ellipse(c, (110, 80, 50), (x - 4, y - 3, 9, 8)); pygame.draw.rect(c, (70, 50, 34), (x - 2, y - 5, 5, 3))
            c.fill((230, 200, 90), (x - 1, y - 1, 2, 2))
        elif kind == "charm":
            pygame.draw.polygon(c, (230, 200, 110), [(x, y - 5), (x + 4, y), (x, y + 5), (x - 4, y)]); pygame.draw.polygon(c, (150, 230, 255), [(x, y - 3), (x + 2, y), (x, y + 3), (x - 2, y)])
        elif kind in ("flask", "flaskpow"):
            col = (230, 120, 70) if kind == "flask" else (255, 220, 100)
            pygame.draw.rect(c, (180, 200, 210), (x - 1, y - 6, 3, 3)); pygame.draw.ellipse(c, col, (x - 4, y - 4, 8, 9)); c.fill((255, 255, 255), (x - 2, y - 2, 1, 2))
        if (t // 25 + x) % 3 == 0: c.fill((255, 255, 220), (x + 3, y - 5, 1, 1))
