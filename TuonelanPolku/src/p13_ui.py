
# ---------------- UI: text, button glyphs, HUD, menus and screens ----------------
_ESC = [False]
def ks_quit():
    v = _ESC[0]; _ESC[0] = False; return v

BF_KEYS = {"b0": "bf_b0", "b1": "bf_b1", "b2": "bf_b2", "b3": "bf_b3", "b4": "bf_b4", "b5": "bf_b5", "b6": "bf_b6", "b7": "bf_b7", "b8": "bf_b8", "b9": "bf_b9", "b10": "bf_b10", "b11": "bf_b11", "b12": "bf_b12", "b13": "bf_b13"}
# glyph tables: action -> (label, color, shape)
GLYPHS = {
    "ps": {"jump": ("x", (110, 160, 255), "cross"), "dodge": ("o", (255, 100, 110), "circle"), "light": ("s", (240, 140, 220), "square"),
           "heavy": ("t", (110, 230, 150), "tri"), "guard": ("L1", None, "pill"), "skill": ("R1", None, "pill"), "flask": ("R2", None, "pill"),
           "interact": ("up", None, "dpadup"), "pause": ("Options", None, "pill"), "map": ("Share", None, "pill"), "move": ("L", None, "stick")},
    "xbox": {"jump": ("A", (90, 220, 110), "letter"), "dodge": ("B", (255, 90, 90), "letter"), "light": ("X", (90, 150, 255), "letter"),
             "heavy": ("Y", (255, 215, 80), "letter"), "guard": ("LB", None, "pill"), "skill": ("RB", None, "pill"), "flask": ("RT", None, "pill"),
             "interact": ("up", None, "dpadup"), "pause": ("Menu", None, "pill"), "map": ("View", None, "pill"), "move": ("L", None, "stick")},
    "kb": {"jump": ("Z", None, "key"), "dodge": ("V", None, "key"), "light": ("X", None, "key"), "heavy": ("C", None, "key"),
           "guard": ("A", None, "key"), "skill": ("S", None, "key"), "flask": ("D", None, "key"), "interact": ("up", None, "keyup"),
           "pause": ("Enter", None, "pill"), "map": ("Tab", None, "pill"), "move": ("arrows", None, "keyarrows")},
}
CLASS_KEYS = {"warrior": "cls_warrior", "sage": "cls_sage", "hunter": "cls_hunter"}
SETTING_ROWS = ["lang", "difficulty", "penalty", "music", "music_vol", "sfx", "sfx_vol", "shake", "dmgnum", "flash", "prompts", "runmode", "hints", "perf", "test_weapon", "controls", "back"]
HINTS = [(2, 9, "h_move"), (9, 13, "h_jump"), (13, 17, "h_attack"), (18, 23, "h_roll"), (25, 30, "h_special")]

def fmt_time(sec):
    return tr("time_fmt", sec // 3600, (sec // 60) % 60)

class GameUI:
    def init_ui(s):
        s.font = PixelFont(tall=True); s.big = PixelFont(tall=True, scale=2, bold=True)
        s.mid = PixelFont(tall=True, bold=True); s.tiny = PixelFont()
        s.tcache = {}; s.gcache = {}; s.track = None
        s.lightmap = pygame.Surface((W, H)); s.dimmer = pygame.Surface((W, H)); s.dimmer.fill((0, 0, 0)); s.dimmer.set_alpha(150)
        s.menu_i = {}; s.quit_hold = 0; s.last_pad = None; s.menu_owner = 0; s.set_from = "title"; s.set_i = 0
        s.hp_ghost = [1.0, 1.0]; s.hint = None; s.hint_t = 0; s.cs_i = 0; s.cs_who = 0; s.cs_pad = None; s.need_pad = None
        s.lv_i = 0; s.lv_who = 0; s.map_from = "play"; s.t_ui = 0; s.title_msg = None; s.confirm_i = 1; s.end_page = 0; s.end_t = 0
        s.info_pad_lost = False
    # ---------- text ----------
    def render(s, t, f, col):
        k = (t, col, id(f))
        img = s.tcache.get(k)
        if img is None:
            if len(s.tcache) > 500: s.tcache.clear()
            img = f.render(str(t), False, col); s.tcache[k] = img
        return img
    def text(s, t, x, y, col=(255, 255, 255), font=None, anchor="c", shadow=True):
        f = font or s.font
        if s.track is not None and not isinstance(t, TStr): s.track.append(("untr", str(t), None))
        img = s.render(t, f, col); r = img.get_rect()
        if anchor == "c": r.center = (int(x), int(y))
        elif anchor == "l": r.midleft = (int(x), int(y))
        else: r.midright = (int(x), int(y))
        if s.track is not None: s.track.append(("rect", str(t), tuple(r)))
        if shadow: s.canvas.blit(s.render(t, f, (0, 0, 0)), r.move(1, 1))
        s.canvas.blit(img, r)
        return r
    def glyph(s, action):
        style = SETTINGS["prompts"]; k = (style, action)
        g = s.gcache.get(k)
        if g: return g
        lab, col, shape = GLYPHS[style][action]
        tf = s.tiny
        if shape in ("cross", "circle", "square", "tri", "letter"):
            g = pygame.Surface((13, 13), pygame.SRCALPHA); pygame.draw.circle(g, (30, 32, 44), (6, 6), 6); pygame.draw.circle(g, (90, 94, 110), (6, 6), 6, 1)
            if shape == "cross": pygame.draw.line(g, col, (3, 3), (9, 9), 2); pygame.draw.line(g, col, (9, 3), (3, 9), 2)
            elif shape == "circle": pygame.draw.circle(g, col, (6, 6), 3, 1)
            elif shape == "square": pygame.draw.rect(g, col, (3, 3, 7, 7), 1)
            elif shape == "tri": pygame.draw.polygon(g, col, [(6, 2), (10, 9), (2, 9)], 1)
            else:
                im = tf.render(lab, False, col); g.blit(im, (6 - im.get_width() // 2, 6 - im.get_height() // 2))
        elif shape == "pill" or shape == "key":
            im = tf.render(lab, False, (235, 235, 245)); w = max(13, im.get_width() + 6)
            g = pygame.Surface((w, 13), pygame.SRCALPHA)
            pygame.draw.rect(g, (30, 32, 44), (0, 0, w, 13), 0, 4 if shape == "pill" else 2); pygame.draw.rect(g, (130, 134, 150), (0, 0, w, 13), 1, 4 if shape == "pill" else 2)
            g.blit(im, (w // 2 - im.get_width() // 2, 6 - im.get_height() // 2 + 1))
        elif shape == "dpadup":
            g = pygame.Surface((13, 13), pygame.SRCALPHA)
            pygame.draw.rect(g, (60, 62, 76), (4, 0, 5, 13)); pygame.draw.rect(g, (60, 62, 76), (0, 4, 13, 5)); pygame.draw.rect(g, (235, 235, 245), (4, 0, 5, 5))
        elif shape == "keyup":
            g = pygame.Surface((13, 13), pygame.SRCALPHA); pygame.draw.rect(g, (30, 32, 44), (0, 0, 13, 13), 0, 2); pygame.draw.rect(g, (130, 134, 150), (0, 0, 13, 13), 1, 2)
            pygame.draw.polygon(g, (235, 235, 245), [(6, 3), (10, 8), (2, 8)])
        elif shape == "keyarrows":
            g = pygame.Surface((27, 13), pygame.SRCALPHA)
            for i, pts in enumerate(([(5, 3), (2, 8), (8, 8)], [(5, 11), (2, 6), (8, 6)])): pass
            pygame.draw.rect(g, (30, 32, 44), (0, 0, 13, 13), 0, 2); pygame.draw.rect(g, (130, 134, 150), (0, 0, 13, 13), 1, 2)
            pygame.draw.polygon(g, (235, 235, 245), [(4, 6), (8, 3), (8, 9)])
            pygame.draw.rect(g, (30, 32, 44), (14, 0, 13, 13), 0, 2); pygame.draw.rect(g, (130, 134, 150), (14, 0, 13, 13), 1, 2)
            pygame.draw.polygon(g, (235, 235, 245), [(23, 6), (19, 3), (19, 9)])
        else:   # stick
            g = pygame.Surface((13, 13), pygame.SRCALPHA); pygame.draw.circle(g, (30, 32, 44), (6, 6), 6); pygame.draw.circle(g, (130, 134, 150), (6, 6), 6, 1)
            im = tf.render(lab, False, (235, 235, 245)); g.blit(im, (6 - im.get_width() // 2, 6 - im.get_height() // 2))
        s.gcache[k] = g
        return g
    def rich(s, t, x, y, col=(255, 255, 255), font=None, anchor="c"):
        """Text with {action} tokens drawn as button glyphs."""
        f = font or s.font
        if s.track is not None and not isinstance(t, TStr): s.track.append(("untr", str(t), None))
        parts = []; i = 0; t = str(t)
        while i < len(t):
            j = t.find("{", i)
            if j < 0: parts.append(("t", t[i:])); break
            if j > i: parts.append(("t", t[i:j]))
            k = t.find("}", j)
            parts.append(("g", t[j + 1:k])); i = k + 1
        tw = 0; items = []
        for kind, v in parts:
            if kind == "t": im = s.render(v, f, col); sh = s.render(v, f, (0, 0, 0)); items.append((im, sh, im.get_width())); tw += im.get_width()
            else: g = s.glyph(v); items.append((g, None, g.get_width() + 2)); tw += g.get_width() + 2
        x0 = x - tw // 2 if anchor == "c" else (x if anchor == "l" else x - tw)
        if s.track is not None: s.track.append(("rect", t, (x0, y - 7, tw, 14)))
        cx = x0
        for im, sh, w in items:
            if sh is not None:
                s.canvas.blit(sh, (cx + 1, y - im.get_height() // 2 + 1)); s.canvas.blit(im, (cx, y - im.get_height() // 2))
            else: s.canvas.blit(im, (cx, y - im.get_height() // 2 + 0))
            cx += w
    def panel(s, x, y, w, h, alpha=210, border=(150, 130, 90)):
        r = pygame.Rect(int(x), int(y), int(w), int(h))
        if not hasattr(s, "panel_cache"): s.panel_cache = {}
        key=(r.w,r.h,alpha); sf=s.panel_cache.get(key)
        if sf is None:
            sf = pygame.Surface((r.w, r.h), pygame.SRCALPHA); sf.fill((12, 10, 18, alpha)); s.panel_cache[key]=sf
            if len(s.panel_cache)>32:s.panel_cache.clear()
        s.canvas.blit(sf, r.topleft)
        pygame.draw.rect(s.canvas, border, r, 1); pygame.draw.rect(s.canvas, (60, 50, 40), r.inflate(-4, -4), 1)
        if s.track is not None: s.track.append(("rect", "panel", tuple(r)))
        return r
    def menu_box(s, items, idx, cy=None, title=None, sub=None, minw=120, x=None, selcol=(255, 225, 140), draw_panel=True):
        """Auto-sized vertical menu. returns panel rect."""
        rows = len(items); rh = 16
        tw = max([s.font.size(it)[0] for it in items] + [s.mid.size(title)[0] if title else 0, s.tiny.size(sub)[0] if sub else 0, minw - 40])
        w = tw + 44; h = rows * rh + 14 + (20 if title else 0) + (12 if sub else 0)
        if cy is None: cy = H // 2
        px = (W - w) // 2 if x is None else x; py = int(cy - h / 2)
        if draw_panel: s.panel(px, py, w, h)
        y = py + 9
        if title: s.text(title, px + w // 2, y + 6, (255, 225, 150), s.mid); y += 20
        if sub: s.text(sub, px + w // 2, y + 4, (170, 170, 190), s.tiny); y += 12
        for i, it in enumerate(items):
            sel = i == idx
            if sel:
                pygame.draw.rect(s.canvas, (60, 40, 30), (px + 6, y + i * rh, w - 12, rh - 1)); pygame.draw.rect(s.canvas, (150, 110, 60), (px + 6, y + i * rh, w - 12, rh - 1), 1)
                a = 2 + (s.t_ui // 10) % 2
                pygame.draw.polygon(s.canvas, selcol, [(px + 10 + a, y + i * rh + 4), (px + 10 + a, y + i * rh + 11), (px + 15 + a, y + i * rh + 7)])
            s.text(it, px + w // 2, y + i * rh + 7, selcol if sel else (200, 200, 210))
        return pygame.Rect(px, py, w, h)
    # ---------- input helpers ----------
    def menu_in(s):
        r = {"up": 0, "down": 0, "left": 0, "right": 0, "ok": 0, "back": 0, "any": 0}
        if not hasattr(s, "menu_prev"): s.menu_prev = {}; s.menu_rep = {}
        held = {k: False for k in ("up", "down", "left", "right")}
        for p in s.pads.values():
            for k in held:
                if p.held(k): held[k] = True
            if p.pressed("jump") or p.pressed("start"): r["ok"] = 1; s.last_pad = p
            if p.pressed("dodge"): r["back"] = 1
        for k, on in held.items():
            was = s.menu_prev.get(k, False)
            if on and not was:
                r[k] = 1; r["any"] = 1; s.menu_rep[k] = 0
            elif on:
                s.menu_rep[k] = s.menu_rep.get(k, 0) + 1
                if s.menu_rep[k] >= 18 and (s.menu_rep[k] - 18) % 6 == 0:
                    r[k] = 1; r["any"] = 1
            else:
                s.menu_rep[k] = 0
        s.menu_prev = held
        if ks_quit(): r["back"] = 1
        return r
    def sel(s, key, n, r):
        i = s.menu_i.get(key, 0) % n
        if r["up"]: i = (i - 1) % n; sfx("select", 0.5)
        if r["down"]: i = (i + 1) % n; sfx("select", 0.5)
        s.menu_i[key] = i
        return i
    # ---------- state transitions ----------
    def go(s, st):
        s.state_name = st
    def has_save(s): return s.title_save is not None
    def open_title(s):
        s.state_name = "title"; MUSIC.request("title"); s.menu_i["title"] = 0
        s.title_save, s.title_status = load_save(None, set(BONFIRES))
    def new_game_flow(s):
        s.cs_who = 0; s.cs_pad = s.last_pad; s.cs_i = 0; s.state_name = "class"
    def begin_session(s, save):
        save=save.copy()
        if save.get("louhi_unlocked") or save.get("done") or "tytti" in save.get("bosses",[]):
            if "b9" not in save["seen"]:save["seen"].append("b9")
            save["bonfire"]="b9";save["louhi_unlocked"]=True;write_save(save)
        s.pending = save; s.pend_pad = s.last_pad or next(iter(s.pads.values())); s.state_name = "loading"
    def open_pause(s):
        s.state_name = "pause"; s.menu_i["pause"] = 0; sfx("select", 0.6)
    def open_bonfire(s):
        s.state_name = "bonfire"; s.menu_i["bonfire"] = 0
    def open_map(s, frm):
        s.map_from = frm; s.state_name = "map"
    def open_settings(s, frm):
        s.set_from = frm; s.state_name = "settings"; s.menu_i["settings"] = 0
    def back_to_title(s):
        if s.save is not None: s.save_game()
        s.save = None; s.players = []; s.enemies = []; s.boss = None; s.arena = None
        s.open_title()
    # ---------- title ----------
    def up_title(s):
        r = s.menu_in(); items = s.title_items(); n = len(items)
        i = s.sel("title", n, r); key = items[i][0]
        if r["ok"]:
            sfx("confirm", 0.7)
            if key == "cont": s.begin_session(s.title_save)
            elif key == "new":
                if s.title_save is not None: s.confirm_i = 1; s.menu_i["confirm"] = 1; s.state_name = "confirm"   # default = No
                else: s.new_game_flow()
            elif key == "settings": s.open_settings("title")
            elif key == "quit": s.running = False
        if r["back"]: s.menu_i["title"] = n - 1
    def title_items(s):
        it = []
        if s.title_save is not None: it.append(("cont", tr("m_continue")))
        it += [("new", tr("m_new")), ("settings", tr("m_settings")), ("quit", tr("m_quit"))]
        return it
    def dr_title(s):
        c = s.canvas; t = s.t_ui
        s.draw_title_bg(c, t)
        ttl = tr("title")
        for dx, dy, col in ((2, 2, (20, 10, 10)), (0, 0, (240, 215, 150))):
            img = s.render(ttl, s.big, col); r = img.get_rect(center=(W // 2 + dx, 34 + dy)); c.blit(img, r)
        if s.track is not None: s.track.append(("rect", str(ttl), tuple(img.get_rect(center=(W // 2, 34)))))
        s.text(tr("subtitle"), W // 2, 54, (200, 200, 170), s.font)
        items = s.title_items(); i = s.menu_i.get("title", 0)
        s.menu_box([x[1] for x in items], i, cy=112, minw=110)
        if s.title_save is not None:
            sv = s.title_save
            s.text(tr("save_info", tr(CLASS_KEYS[sv["cls"]]), 1 + sum(sv["stats"].values()), fmt_time(sv["time"])), W // 2, 152, (200, 200, 190), s.tiny)
        if s.title_status == "corrupt": s.text(tr("save_corrupt"), W // 2, 165, (255, 130, 120), s.tiny)
        elif s.title_status == "backup": s.text(tr("save_backup"), W // 2, 165, (255, 220, 130), s.tiny)
        s.text(num("VERSION " + VERSION), 4, H - 6, (220, 220, 235), s.tiny, "l")
    def draw_title_bg(s, c, t):
        area = "forest"; c.blit(sky_surface(area), (0, 0))
        for (lay, f, yo) in layers_for(area):
            lw, lh = lay.get_size(); x = -int(t * f * 0.3) % lw; y = H - lh + yo // 2 + 10
            c.blit(lay, (x - lw, y)); c.blit(lay, (x, y))
        pygame.draw.polygon(c, (10, 14, 16), [(0, H), (0, 150), (60, 144), (120, 150), (200, 146), (260, 152), (320, 148), (320, H)])
        pygame.draw.rect(c, (8, 10, 12), (0, 158, W, 22))
        s.draw_bonfire(c, 40, 156, True, t)
        for k in range(3):
            fs = fog_surface(area); fx = -int(t * (0.2 + k * 0.1)) % 640; c.blit(fs, (fx - 640, 100 + k * 26)); c.blit(fs, (fx, 100 + k * 26))
        lm = s.lightmap; lm.fill((150, 160, 175))
        fl = 0.9 + 0.1 * math.sin(t * 0.37)
        lm.blit(glow(90, (int(255 * fl), int(170 * fl), int(80 * fl))), (40 - 90, 150 - 90), special_flags=pygame.BLEND_ADD)
        c.blit(lm, (0, 0), special_flags=pygame.BLEND_MULT); c.blit(vignette(), (0, 0), special_flags=pygame.BLEND_MULT)
        if not s.ffs: s.init_fireflies()
        for f in s.ffs:
            f[0] = (f[0] + f[2] + math.sin(t * 0.03 + f[4]) * 0.2) % W; f[1] = (f[1] + f[3] + math.cos(t * 0.027 + f[4]) * 0.18) % H
            a = 0.5 + 0.5 * math.sin(t * 0.07 + f[4] * 3)
            if a > 0.25: c.fill((int(220 * a), int(255 * a), int(120 * a)), (int(f[0]), int(f[1]), 2, 2))
    # ---------- confirm ----------
    def up_confirm(s):
        r = s.menu_in(); i = s.sel("confirm", 2, r)
        if r["ok"]:
            if i == 0: s.new_game_flow()
            else: s.state_name = "title"
        if r["back"]: s.state_name = "title"
    def dr_confirm(s):
        s.draw_title_bg(s.canvas, s.t_ui)
        s.panel(30, 50, 260, 80)
        for k, ln in enumerate(wrap(s.font, tr("confirm_new"), 236)): s.text(ln, W // 2, 66 + k * 13, (255, 220, 170))
        i = s.menu_i.get("confirm", 1)
        for k, lab in enumerate((tr("yes"), tr("no"))):
            s.text(lab, W // 2 - 40 + k * 80, 112, (255, 225, 140) if i == k else (170, 170, 180))
            if i == k: pygame.draw.rect(s.canvas, (200, 150, 80), (W // 2 - 40 + k * 80 - 24, 104, 48, 16), 1)
    def up_confirm_nav(s): pass
    # ---------- class select ----------
    def up_class(s):
        r = s.menu_in(); s.cs_i = (s.cs_i + (1 if r["right"] else -1 if r["left"] else 0)) % 3
        if r["left"] or r["right"]: sfx("select", 0.5)
        if r["ok"]:
            cls = CLASSES[s.cs_i]; sfx("confirm", 0.8)
            if s.cs_who == 0:
                sv = new_save(cls); s.begin_session(sv)
            else:
                pad = s.cs_pad
                s.add_p2(cls, pad); s.state_name = "play"
        if r["back"]:
            if s.cs_who == 0: s.state_name = "title"
            else: s.state_name = "play"
    def dr_class(s):
        c = s.canvas
        if s.cs_who == 0: s.draw_title_bg(c, s.t_ui)
        else: s.draw_play_scene(); c.blit(s.dimmer, (0, 0))
        s.text(tr("choose_class") if s.cs_who == 0 else tr("choose_class_p2"), W // 2, 12, (255, 225, 150), s.mid)
        for i, cls in enumerate(CLASSES):
            x = 8 + i * 104; sel = i == s.cs_i
            s.panel(x, 24, 98, 130, 225 if sel else 170, (255, 215, 130) if sel else (90, 80, 70))
            spr = player_frame(cls, "idle", (s.t_ui // 24) % 2, False, P2_TINT[cls] if s.cs_who == 1 else None)
            spr = pygame.transform.scale(spr, (spr.get_width() * 2, spr.get_height() * 2))
            if not sel: spr = spr.copy(); spr.fill((120, 120, 120, 255), special_flags=pygame.BLEND_RGBA_MULT)
            c.blit(spr, (x + 49 - spr.get_width() // 2, 30))
            s.text(tr(CLASS_KEYS[cls]), x + 49, 92, (255, 235, 170) if sel else (160, 160, 170), s.font)
            for k, ln in enumerate(wrap(s.tiny, tr("cd_" + cls), 88)): s.text(ln, x + 6, 106 + k * 9, (210, 210, 200) if sel else (130, 130, 140), s.tiny, "l")
        s.rich(tr("hint_choose"), W // 2, 168, (200, 200, 210), s.tiny)
    # ---------- loading ----------
    def up_loading(s):
        sv = s.pending
        s.start_session(sv, s.pend_pad); s.pending = None; s.title_msg = None
        if s.save["bonfire"] == "b0" and not s.save["bosses"] and s.frames == 0 and s.save["time"] < 5: s.hint_t = 0
        s.save_game()
    def dr_loading(s):
        s.canvas.fill((0, 0, 0)); s.text(tr("loading"), W // 2, H // 2, (200, 200, 190))
    # ---------- play ----------
    def up_play(s):
        if getattr(s,"true_end_delay",0):
            s.true_end_delay+=1
            if s.true_end_delay>240:s.state_name="true";s.true_t=0
            return
        pad_start = any(pd.pressed("start") for pd in s.p_pad if pd is not None)
        if ks_quit() or pad_start: s.open_pause(); return
        if not s.coop and not s.dying:
            pd = join_pad(s, lambda pd: pd is not s.p_pad[0] and pd.pressed("start") and not isinstance(pd, IdlePad))
            if pd is not None:
                s.cs_who = 1; s.cs_pad = pd; s.cs_i = 0; s.state_name = "class"; return
        if any(pd.pressed("back") for pd in s.p_pad if pd is not None): s.open_map("play"); return
        s.update_world(); s.update_hints()
        if s.ending_t:
            s.ending_t += 1
            if s.ending_t > 260: s.start_ending()
    def update_hints(s):
        if not SETTINGS["hints"] or s.save["bosses"] or "b1" in s.save["seen"] or s.dying: return
        p = s.players[0]; tx = p.x / TILE
        if s.hint_t > 0: s.hint_t -= 1
        if p.y > 31 * TILE: return
        for (a, b, key) in HINTS:
            if a <= tx < b and key not in s.hints_seen:
                s.hints_seen.add(key); s.hint = key; s.hint_t = 330
    def dr_play(s):
        s.draw_play_scene()
    def draw_play_scene(s):
        c = s.canvas
        s.draw_world(c, s.frames)
        s.draw_overlays(c)
    def draw_overlays(s, c):
        if SETTINGS.get("test_weapon"):
            s.text(tr("test_weapon_hud"), W // 2, 8, (255, 80, 80), s.tiny)
        cx = int(s.cam[0]); cy = int(s.cam[1])
        for d in s.dns:
            x = int(d[0] - cx); y = int(d[1] - cy); col = d[3]
            if d[5]: s.text(d[2], x, y, col, s.tiny)
            else: s.text(num(d[2]), x, y, col, s.tiny)
        for p in s.players:
            if p.nearby and p.alive() and not s.dying:
                k, ident = p.nearby
                lab = tr("p_rest") if k == "bonfire" else tr("p_lever")
                s.rich(TStr("{interact} " + lab), int(p.x - cx), int(p.y - cy - 38), (255, 240, 200), s.tiny)
            if p.state == "down":
                s.rich(tr("p_revive"), int(p.x - cx), int(p.y - cy - 44), (170, 255, 190), s.tiny)
        s.draw_hud(c)
        if s.sep_t > 70:
            s.text(tr("p_keep_close"), W // 2, 30, (255, 200, 140), s.tiny)
    def draw_perf_overlay(s):
        ar = s.frame_ms; cur = ar[-1] if ar else 0.0; hi = max(ar[-120:]) if ar else 0.0
        txt = TStr("FPS %.0f  FRAME %.1f ms  MAX %.1f ms" % (1000.0 / max(cur, 0.01), cur, hi))
        x = 3; y = H - 26; pygame.draw.rect(s.canvas, (0, 0, 0), (x, y - 6, 182, 20))
        s.text(txt, x + 2, y, (140, 240, 160), s.tiny, "l")
        s.text(TStr("INPUT %.2f ms  CHUNKS %d/%d  AI stream" % (s.input_ms, len(s.chunks), len(GameCore.CHUNK_CACHE))), x + 2, y + 8, (160, 200, 240), s.tiny, "l")
    def draw_hud(s, c):
        for p in s.players:
            right = p.idx == 1
            hw = max(50, min(150, int(p.maxhp * 0.8))); x = W - 6 - hw if right else 6; y = 8
            g = s.hp_ghost[p.idx]; fr = max(0.0, p.hp / p.maxhp)
            g = fr if fr > g else g + (fr - g) * 0.04; s.hp_ghost[p.idx] = g
            col = P2_TINT[p.cls] if right else (255, 220, 120)
            tx = x - 7 if right else x + hw + 2
            pygame.draw.polygon(c, col, [(tx, y), (tx + 5, y), (tx + 2, y + 5)])
            pygame.draw.rect(c, (10, 6, 10), (x - 1, y - 1, hw + 2, 9)); pygame.draw.rect(c, (60, 20, 24), (x, y, hw, 7))
            pygame.draw.rect(c, (200, 160, 120), (x, y, int(hw * g), 7)); pygame.draw.rect(c, (210, 50, 56), (x, y, int(hw * fr), 7))
            pygame.draw.rect(c, (255, 120, 120), (x, y, int(hw * fr), 2)); pygame.draw.rect(c, (120, 100, 70), (x - 1, y - 1, hw + 2, 9), 1)
            sw = max(40, min(140, int(p.maxst * 0.8))); sx = W - 6 - sw if right else 6; fr2 = p.stam / p.maxst
            pygame.draw.rect(c, (10, 6, 10), (sx - 1, y + 9, sw + 2, 6)); pygame.draw.rect(c, (30, 50, 30), (sx, y + 10, sw, 4))
            pygame.draw.rect(c, (110, 220, 90) if p.stam > 20 and p.exh <= 0 else (220, 150, 70), (sx, y + 10, int(sw * fr2), 4))
            yy = y + 16
            if p.cls == "sage":
                fw = max(40, min(120, int(p.maxfoc * 0.7))); fx = W - 6 - fw if right else 6
                pygame.draw.rect(c, (10, 6, 10), (fx - 1, yy + 1, fw + 2, 5)); pygame.draw.rect(c, (20, 50, 60), (fx, yy + 2, fw, 3))
                pygame.draw.rect(c, (90, 220, 230), (fx, yy + 2, int(fw * p.focus / p.maxfoc), 3)); yy += 6
            fx = W - 6 - 24 if right else 6
            pygame.draw.rect(c, (180, 200, 210), (fx + 2, yy + 3, 3, 2)); pygame.draw.ellipse(c, (230, 120, 70) if p.flasks > 0 else (80, 60, 60), (fx, yy + 5, 7, 8))
            s.text(num("x%d" % p.flasks), fx + 9, yy + 10, (230, 230, 220), s.tiny, "l")
            # souls
            sx2 = 8 if right else W - 8
            c.fill((150, 230, 255), (sx2 - (0 if right else 3), H - 14, 3, 3)); c.fill((60, 130, 170), (sx2 - (0 if right else 3) + 1, H - 11, 1, 2))
            s.text(num(p.souls), sx2 + 6 if right else sx2 - 6, H - 11, (230, 245, 255), s.font, "l" if right else "r")
            if getattr(p, "gain_t", 0) > 0 and p.gain_n:
                s.text(num("+%d" % p.gain_n), sx2 + 6 if right else sx2 - 6, H - 23, (150, 230, 255), s.tiny, "l" if right else "r")
        b = s.boss
        if b is not None and b.engaged and not (b.dead and b.dt > 90):
            want = max(0.0, b.hp / b.maxhp); b.shown_bar += (want - b.shown_bar) * 0.1 if want < b.shown_bar else (0.02 if want > b.shown_bar else 0)
            bw = 96; bx = (W - bw) // 2; by = 5
            s.text(tr("boss_" + b.key), W // 2, by + 14, (240, 225, 190), s.font)
            pygame.draw.rect(c, (10, 6, 10), (bx - 2, by - 2, bw + 4, 9)); pygame.draw.rect(c, (60, 20, 24), (bx, by, bw, 5))
            pygame.draw.rect(c, (220, 180, 130), (bx, by, int(bw * b.shown_bar), 5)); pygame.draw.rect(c, (190, 40, 50), (bx, by, int(bw * want), 5))
            pygame.draw.rect(c, (150, 120, 80), (bx - 2, by - 2, bw + 4, 9), 1)
            if b.phase >= 2:
                pygame.draw.polygon(c, (255, 200, 100), [(bx + bw // 2 - 3, by - 1), (bx + bw // 2 + 3, by - 1), (bx + bw // 2, by + 5)]) if False else None
        # messages
        for i, (t, life, col) in enumerate(reversed(s.msgs)):
            a = min(1.0, life / 30.0); cc = tuple(int(v * a) for v in col)
            s.text(t, W // 2, H - 44 - i * 11, cc, s.tiny)
        if s.hint_t > 0 and s.hint and not s.dying:
            a = min(1.0, s.hint_t / 30.0); cc = tuple(int(v * a) for v in (240, 235, 200))
            lines = wrap(s.font, tr(s.hint + "_" + s.players[0].cls) if s.hint == "h_special" else tr(s.hint), 280)
            for i, ln in enumerate(lines): s.rich(ln, W // 2, 98 + i * 12, cc, s.tiny)
        if s.area_popup and not s.dying:
            a, tt = s.area_popup; f = min(1.0, tt / 30.0, (220 - tt) / 40.0)
            if f > 0:
                col = tuple(int(v * f) for v in (235, 225, 190)); img = s.render(tr("area_" + a), s.big, col); r = img.get_rect(center=(W // 2, 38))
                if s.track is not None: s.track.append(("rect", "area", tuple(r)))
                c.blit(s.render(tr("area_" + a), s.big, (0, 0, 0)), r.move(1, 1)); c.blit(img, r)
        if s.felled:
            k, tt = s.felled; f = min(1.0, tt / 25.0, (220 - tt) / 40.0)
            if f > 0:
                col = tuple(int(v * f) for v in (255, 220, 130)); txt = tr("felled", tr("boss_" + k))
                img = s.render(txt, s.mid, col); r = img.get_rect(center=(W // 2, 70))
                if s.track is not None: s.track.append(("rect", str(txt), tuple(r)))
                c.blit(s.render(txt, s.mid, (0, 0, 0)), r.move(1, 1)); c.blit(img, r)
        if s.banner:
            txt, tt = s.banner; f = min(1.0, tt / 20.0, (150 - tt) / 30.0)
            if f > 0:
                col = tuple(int(v * f) for v in (255, 205, 120)); s.text(txt, W // 2, 80, col, s.mid)
        if s.dying:
            f = min(1.0, s.dying / 50.0); ov_ = pygame.Surface((W, H)); ov_.fill((20, 0, 4)); ov_.set_alpha(int(150 * f)); c.blit(ov_, (0, 0))
            col = tuple(int(v * f) for v in (190, 30, 40)); s.text(tr("you_died") if SETTINGS["lang"] else tr("you_died"), W // 2, H // 2 - 6, col, s.big)
            if s.dying > 60 and SETTINGS["penalty"] == "classic" and any(st["souls"] for st in s.stains):
                s.text(tr("stain_hint"), W // 2, H // 2 + 16, (190, 200, 220), s.tiny)
    # ---------- pause ----------
    def pause_items(s):
        it = [("resume", tr("m_resume")), ("map", tr("m_map")), ("settings", tr("m_settings")), ("controls", tr("m_controls"))]
        if s.coop: it.append(("p2off", tr("m_p2_leave")))
        it += [("title", tr("m_to_title")), ("quit", tr("m_quit"))]
        return it
    def up_pause(s):
        if s.need_pad is not None:
            pd = join_pad(s, lambda pd: pd not in s.p_pad and not isinstance(pd, IdlePad) and (pd.pressed("start") or pd.pressed("jump")))
            if pd is not None:
                s.players[s.need_pad].pad = pd; s.p_pad[s.need_pad] = pd; s.need_pad = None
            ks_quit(); return
        pad_start = any(pd.pressed("start") for pd in s.p_pad if pd is not None)
        r = s.menu_in(); items = s.pause_items(); i = s.sel("pause", len(items), r)
        if r["back"] or pad_start: s.state_name = "play"; return
        if r["ok"]:
            k = items[i][0]; sfx("confirm", 0.6)
            if k == "resume": s.state_name = "play"
            elif k == "map": s.open_map("pause")
            elif k == "settings": s.open_settings("pause")
            elif k == "controls": s.state_name = "controls"; s.ctl_from = "pause"
            elif k == "p2off": s.remove_p2(); s.state_name = "play"
            elif k == "title": s.back_to_title()
            elif k == "quit": s.save_game(); s.running = False
    def dr_pause(s):
        s.draw_play_scene(); s.canvas.blit(s.dimmer, (0, 0))
        if s.need_pad is not None:
            s.panel(40, 60, 240, 56)
            s.text(tr("pad_lost", tr("pl_%d" % (s.need_pad + 1))), W // 2, 78, (255, 200, 150))
            s.rich(tr("pad_lost_d"), W // 2, 98, (200, 200, 210), s.tiny); return
        items = s.pause_items()
        s.menu_box([x[1] for x in items], s.menu_i.get("pause", 0), title=tr("paused"), sub=None if s.coop else tr("p2_hint"), minw=130)
    # ---------- bonfire ----------
    def bonfire_items(s):
        it = [("go", tr("m_leave_fire")), ("lvl0", tr("m_levelup", tr("pl_1")) if s.coop else tr("m_levelup1"))]
        if s.coop: it.append(("lvl1", tr("m_levelup", tr("pl_2"))))
        it += [("map", tr("m_map")), ("title", tr("m_save_exit"))]
        return it
    def up_bonfire(s):
        r = s.menu_in(); items = s.bonfire_items(); i = s.sel("bonfire", len(items), r)
        if r["back"]: s.state_name = "play"; return
        if r["ok"]:
            k = items[i][0]; sfx("confirm", 0.6)
            if k == "go": s.state_name = "play"
            elif k.startswith("lvl"): s.lv_who = int(k[3]); s.lv_i = 0; s.state_name = "levelup"
            elif k == "map": s.open_map("bonfire")
            elif k == "title": s.back_to_title()
    def dr_bonfire(s):
        s.draw_play_scene(); s.canvas.blit(s.dimmer, (0, 0))
        items = s.bonfire_items(); bid = s.save["bonfire"]
        s.menu_box([x[1] for x in items], s.menu_i.get("bonfire", 0), title=tr(BF_KEYS[bid]), sub=tr("fire_sub"), minw=150)
    # ---------- level up ----------
    def up_levelup(s):
        r = s.menu_in(); p = s.players[min(s.lv_who, len(s.players) - 1)]
        if r["up"]: s.lv_i = (s.lv_i - 1) % 4; sfx("select", 0.5)
        if r["down"]: s.lv_i = (s.lv_i + 1) % 4; sfx("select", 0.5)
        if r["back"]: s.state_name = "bonfire"; return
        if r["ok"]:
            if not s.buy_stat(p, STAT_KEYS[s.lv_i]): sfx("hurt", 0.4)
    def dr_levelup(s):
        s.draw_play_scene(); s.canvas.blit(s.dimmer, (0, 0)); c = s.canvas
        p = s.players[min(s.lv_who, len(s.players) - 1)]
        s.panel(10, 8, 300, 154)
        s.text(tr("lv_title"), W // 2, 20, (255, 225, 150), s.mid)
        s.text(tr(CLASS_KEYS[p.cls]) if not s.coop else tr("lv_who", tr("pl_%d" % (p.idx + 1)), tr(CLASS_KEYS[p.cls])), 20, 38, (220, 220, 230), s.font, "l")
        cost = level_cost(p.level) if p.level < MAX_LEVEL else 0
        s.text(tr("lv_level", p.level), 300, 38, (255, 235, 170), s.font, "r")
        names = [tr("st_vit"), tr("st_end"), tr("st_str"), tr("st_foc_" + p.cls)]
        vals = [p.ch["stats"][k] for k in STAT_KEYS]
        for i in range(4):
            y = 58 + i * 20; sel = i == s.lv_i
            if sel: pygame.draw.rect(c, (60, 40, 30), (16, y - 9, 288, 19)); pygame.draw.rect(c, (150, 110, 60), (16, y - 9, 288, 19), 1)
            s.text(names[i], 24, y, (255, 225, 140) if sel else (200, 200, 210), s.font, "l")
            s.text(num(vals[i]), 150, y, (255, 255, 255), s.font, "r")
            dl = wrap(s.tiny, tr("st_%s_d" % STAT_KEYS[i] if i < 3 else "st_foc_%s_d" % p.cls), 140)[:2]
            for j, ln in enumerate(dl): s.text(ln, 160, y + (j * 9 - 4 if len(dl) > 1 else 0), (150, 190, 160) if sel else (110, 140, 120), s.tiny, "l")
        yb = 137
        s.text(tr("lv_souls", p.souls), 24, yb, (150, 230, 255), s.font, "l")
        if p.level >= MAX_LEVEL: s.text(tr("lv_max"), 296, yb, (255, 200, 120), s.font, "r")
        else: s.text(tr("lv_cost", cost), 296, yb, (150, 255, 160) if p.souls >= cost else (255, 120, 110), s.font, "r")
        s.rich(tr("hint_levelup"), W // 2, 152, (190, 190, 200), s.tiny)
    # ---------- map ----------
    def build_map(s):
        if getattr(s, "mapimg", None): return
        s.mapimg = []
        cols = {"forest": ((70, 80, 62), (110, 150, 80)), "swamp": ((70, 78, 56), (140, 160, 80)), "river": ((84, 84, 120), (150, 190, 220)), "pohjola":((36,40,57),(83,105,150))}
        for (nm, a, b) in AREAS:
            surf = pygame.Surface(((b - a) * 2, ROWS)); surf.fill((14, 12, 20)); base, top = cols[nm]
            for tx in range(a, b):
                for ty in range(ROWS):
                    v = GRID[ty][tx]; x = (tx - a) * 2
                    if v == SOLID: surf.fill(top if GRID[ty - 1][tx] != SOLID else base, (x, ty, 2, 1))
                    elif v == PLAT: surf.fill((150, 110, 70), (x, ty, 2, 1))
                    elif v == WATER: surf.fill((50, 90, 170), (x, ty, 2, 1))
                    elif v == THORN: surf.fill((180, 60, 70), (x, ty, 2, 1))
                    elif v == LADDER: surf.fill((170, 120, 70), (x + 0, ty, 1, 1))
            sil = pygame.Surface(surf.get_size()); sil.fill((14, 12, 20))      # "unknown" silhouette version
            for tx in range(a, b):
                for ty in range(ROWS):
                    if GRID[ty][tx] in (SOLID, WATER): sil.fill((34, 32, 42) if GRID[ty][tx] == SOLID else (28, 30, 46), ((tx - a) * 2, ty, 2, 1))
            s.mapimg.append((nm, a, b, surf, sil))
    def up_map(s):
        r = s.menu_in()
        if r["back"] or r["ok"] or any(pd.pressed("back") for pd in s.pads.values()): s.state_name = s.map_from
    def map_known(s):
        """visited cells, and the unknown-but-adjacent frontier (shown as dark silhouettes)."""
        vis = set(); front = set()
        for k in s.mapseen:
            if "," in k:
                try: cx, cy = k.split(","); vis.add((int(cx), int(cy)))
                except ValueError: pass
        for (cx, cy) in vis:
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c2 = (cx + d[0], cy + d[1])
                if c2 not in vis: front.add(c2)
        return vis, front
    def dr_map(s):
        s.build_map(); c = s.canvas;s.msgs.clear()
        if s.save is not None: s.draw_play_scene()
        c.blit(s.dimmer, (0, 0)); c.fill((10, 8, 14), (0, 0, W, H))
        s.text(tr("m_map"), W // 2, 7, (255, 225, 150), s.font)
        vis, front = s.map_known()
        for i, (nm, a, b, surf, sil) in enumerate(s.mapimg):
            y = map_y(s,i) if len(s.mapimg)>4 else (17+i*39); x = (W - surf.get_width()) // 2
            known = any(a <= cx * MAP_CW + MAP_CW - 1 and cx * MAP_CW < b for (cx, cy) in vis)
            pygame.draw.rect(c, (10,8,14) if not known else (18,16,24), (x - 1, y - 1, surf.get_width() + 2, ROWS + 2))
            for cx in range(a // MAP_CW, (b - 1) // MAP_CW + 1):
                for cy in range((ROWS + MAP_CH - 1) // MAP_CH):
                    src = surf if (cx, cy) in vis else (sil if (cx, cy) in front else None)
                    if src is None: continue
                    t0 = max(a, cx * MAP_CW); t1 = min(b, cx * MAP_CW + MAP_CW)
                    r = pygame.Rect((t0 - a) * 2, cy * MAP_CH, (t1 - t0) * 2, min(MAP_CH, ROWS - cy * MAP_CH))
                    c.blit(src, (x + r.x, y + r.y), r)
            for k, ar in ARENAS.items():          # boss rooms stay secret until seen
                if a <= ar["x0"] < b:
                    if ("arena:" + k) not in s.mapseen:
                        c.fill((10, 8, 14), (x + (ar["x0"] + 1 - a) * 2, y + ar["y0"], (ar["x1"] - ar["x0"] - 1) * 2, ar["ground"] - ar["y0"] + 2)); continue
                    done = k in s.save["bosses"]; mx = x + (ar["x0"] + 10 - a) * 2; my = y + ar["y0"] + 6
                    pygame.draw.rect(c, (90, 90, 100) if done else (220, 60, 60), (mx - 2, my - 2, 5, 5), 1); c.fill((90, 90, 100) if done else (220, 60, 60), (mx, my, 1, 1))
            for bid, tx in BONFIRES.items():
                if a <= tx < b and bid in s.save["seen"]:
                    by = floor_row(tx, BF_START[bid]); c.fill((255, 170, 70), (x + (tx - a) * 2 - 1, y + by - 3, 4, 3)); c.fill((255, 235, 150), (x + (tx - a) * 2, y + by - 3, 2, 1))
            for p in s.players:
                tx = p.x / TILE
                if a <= tx < b and (s.t_ui // 15) % 2 == 0:
                    col = (255, 255, 255) if p.idx == 0 else P2_TINT[p.cls]; c.fill(col, (x + int((tx - a) * 2) - 1, y + int(p.y / TILE) - 2, 3, 3))
            if known: s.text(tr("area_" + nm), x + 3, y - 5, (220, 215, 200), s.tiny, "l")
        s.text(tr("map_legend"), W // 2, H - 6, (170, 170, 180), s.tiny)
    # ---------- settings ----------
    def setting_label(s, k):
        return tr("set_" + k)
    def setting_value(s, k):
        v = SETTINGS.get(k)
        if k == "lang": return tr("lang_" + v)
        if k == "difficulty": return tr("dn_" + v)
        if k == "penalty": return tr("pen_" + v)
        if k in ("music", "sfx", "shake", "dmgnum", "hints", "perf", "test_weapon"): return tr("on") if v else tr("off")
        if k == "flash": return tr("fl_full") if v else tr("fl_reduced")
        if k == "prompts": return tr("pr_" + v)
        if k == "runmode": return tr("run_" + v)
        return None
    def change_setting(s, k, d):
        if k in ("music", "sfx", "shake", "dmgnum", "flash", "hints", "perf", "test_weapon"): SETTINGS[k] = not SETTINGS[k]
        elif k in CHOICES:
            ch = CHOICES[k]; SETTINGS[k] = ch[(ch.index(SETTINGS[k]) + d) % len(ch)]
            if k == "lang": s.tcache.clear(); s.gcache.clear()
        elif k in ("music_vol", "sfx_vol"): SETTINGS[k] = max(0, min(10, SETTINGS[k] + d))
        save_settings(); sfx("select", 0.8)
    def up_settings(s):
        r = s.menu_in(); n = len(SETTING_ROWS); i = s.sel("settings", n, r); k = SETTING_ROWS[i]
        d = 1 if r["right"] else -1 if r["left"] else 0
        if k in ("controls", "back"):
            if r["ok"]:
                if k == "back": s.state_name = s.set_from
                else: s.state_name = "controls"; s.ctl_from = "settings"
        elif d: s.change_setting(k, d)
        elif r["ok"]: s.change_setting(k, 1)
        if r["back"]: s.state_name = s.set_from
    def dr_settings(s):
        c = s.canvas
        if s.set_from == "title": s.draw_title_bg(c, s.t_ui)
        else: s.draw_play_scene(); c.blit(s.dimmer, (0, 0))
        s.panel(12, 6, 296, 168)
        s.text(tr("m_settings"), W // 2, 17, (255, 225, 150), s.mid)
        n = len(SETTING_ROWS); i = s.menu_i.get("settings", 0); vis = 9
        top = max(0, min(n - vis, i - vis // 2))
        for row in range(vis):
            idx = top + row; k = SETTING_ROWS[idx]; y = 35 + row * 12; sel = idx == i
            if sel: pygame.draw.rect(c, (60, 40, 30), (18, y - 6, 284, 12)); pygame.draw.rect(c, (150, 110, 60), (18, y - 6, 284, 12), 1)
            col = (255, 225, 140) if sel else (200, 200, 210)
            s.text(s.setting_label(k), 26, y, col, s.font, "l")
            if k in ("music_vol", "sfx_vol"):
                v = SETTINGS[k]
                for q in range(10): c.fill((255, 225, 140) if q < v and sel else (200, 200, 210) if q < v else (60, 56, 64), (222 + q * 7, y - 3, 5, 6))
                if sel: s.text(tr("lt"), 214, y, col, s.font, "r"); s.text(tr("gt"), 296, y, col, s.font, "r")
            elif k in ("controls", "back"):
                if sel: s.text(tr("gt"), 296, y, col, s.font, "r")
            else:
                v = s.setting_value(k)
                s.text(TStr(tr("lt") + " " + v + " " + tr("gt")) if sel else v, 296, y, col, s.font, "r")
        if top > 0: pygame.draw.polygon(c, (200, 180, 120), [(160, 27), (164, 27), (162, 24)])
        if top + vis < n: pygame.draw.polygon(c, (200, 180, 120), [(160, 138), (164, 138), (162, 141)])
        k = SETTING_ROWS[i]; desc = "sd_" + k + ("_" + SETTINGS[k] if k in ("difficulty", "penalty") else "")
        for j, ln in enumerate(wrap(s.tiny, tr(desc), 276)[:2]): s.text(ln, W // 2, 152 + j * 10, (190, 190, 170), s.tiny)
    # ---------- controls ----------
    def up_controls(s):
        r = s.menu_in()
        if r["back"] or r["ok"]: s.state_name = s.ctl_from
    def dr_controls(s):
        c = s.canvas
        if s.ctl_from == "pause" and s.save is not None: s.draw_play_scene(); c.blit(s.dimmer, (0, 0))
        elif s.ctl_from == "title": s.draw_title_bg(c, s.t_ui)
        else: c.fill((10, 8, 14))
        cls = s.players[0].cls if s.save is not None and s.players else (s.save["cls"] if s.save else "warrior")
        s.panel(8, 4, 304, 172)
        s.text(tr("m_controls"), W // 2, 14, (255, 225, 150), s.mid)
        rows = [("move", "c_move"), ("jump", "c_jump"), ("light", "c_light_" + cls), ("heavy", "c_heavy_" + cls), ("dodge", "c_dodge"), ("guard", "c_guard_" + cls),
                ("skill", "c_skill_" + cls), ("flask", "c_flask"), ("interact", "c_interact"), ("map", "c_map"), ("pause", "c_pause")]
        for i, (act, lab) in enumerate(rows):
            y = 30 + i * 11
            g = s.glyph(act); s.canvas.blit(g, (20, y - 6)); s.text(tr(lab), 56, y, (225, 225, 215), s.tiny, "l")
        s.text(tr("c_drop"), 20, 150, (200, 200, 190), s.tiny, "l")
        s.text(tr("c_quit"), 20, 159, (255, 190, 150), s.tiny, "l")
        s.text(tr("c_join"), 20, 168, (170, 220, 190), s.tiny, "l")
    # ---------- ending / secret encounter entrance ----------
    def _arm_cut(s):
        s.cut_wait = any(p.held("jump") or p.held("start") for p in s.pads.values())
    def _fresh_ok(s, r):
        held = any(p.held("jump") or p.held("start") for p in s.pads.values())
        if getattr(s, "cut_wait", False):
            if not held: s.cut_wait = False
            return False
        return bool(r["ok"])
    def start_ending(s):
        s.save["done"]=True;s.save["louhi_unlocked"] = "louhi" in s.save["bosses"];s.save_game()
        s.state_name="ending";s.end_page=0;s.end_t=0;s._arm_cut();MUSIC.request("title")
    def up_ending(s):
        r=s.menu_in();s.end_t+=1
        if s._fresh_ok(r) and s.end_t>45:s.end_page+=1;s.end_t=0;s._arm_cut()
        if s.end_page==1 and s.end_t>150 and "louhi" not in s.save["bosses"]:
            s.state_name="interrupt";s.interrupt_t=0;s._arm_cut()
        elif s.end_page>=4:s.enter_pohjola(s.save)
    def dr_ending(s):
        c=s.canvas;c.fill((6,6,12));fs=fog_surface("river");t=s.t_ui;fx=-int(t*.3)%640;c.blit(fs,(fx-640,60));c.blit(fs,(fx,60))
        pg=s.end_page;f=min(1,s.end_t/50)
        if pg<3:
            lines=wrap(s.font,tr("end_%d"%pg),260)
            for i,line in enumerate(lines):s.text(line,160,70+i*15-len(lines)*6,tuple(int(v*f) for v in (225,215,190)))
        else:s.text(tr("end_title"),160,70,tuple(int(v*f) for v in (255,225,150)),s.big);s.text(tr("end_thanks"),160,112,(190,200,190))
    def up_interrupt(s):
        r=s.menu_in();s.interrupt_t+=1
        if s.interrupt_t>200 or (s.interrupt_t>160 and s._fresh_ok(r)):s.enter_pohjola(s.save)
    def dr_interrupt(s):
        c=s.canvas
        c.fill((7,3,12))
        spr=louhi_frame("windup",s.interrupt_t//6,phase=3)
        c.blit(spr,(160-spr.get_width()//2,78-spr.get_height()//2))
        if s.interrupt_t<170:s.text(tr("louhi_intro"),160,156,(225,122,131),s.font)
        else:c.fill((0,0,0))
    def up_poht(s):
        s.poht_t+=1
        if s.poht_t==40:MUSIC.request("pohjola")
        if s.poht_t>100:
            if s.save.get("p2") and len(s.players)==1:
                second=physical_pad(s, s.p_pad[0])
                if second is not None: s.add_p2(s.save["p2"]["cls"], second)
            s.state_name="play";s.dark=.67;MUSIC.request("pohjola")
    def dr_poht(s):
        c=s.canvas;c.fill((0,0,0))
        if s.poht_t>=45:s.chunk(int(s.cam[0])//320);s.draw_world(c,0);s.draw_light(c,0,s.cam[0],s.cam[1],PAL["pohjola"])
    def up_true(s):
        s.menu_in();s.true_t+=1
        if s.true_t>120:s.state_name="true_ending";s.true_page=0;s.true_t=0
    def dr_true(s):s.canvas.fill((0,0,0))
    def up_true_ending(s):
        r=s.menu_in();s.true_t+=1
        if r["ok"] and s.true_t>30:s.true_page+=1;s.true_t=0
        if s.true_page>=4:s.back_to_title()
    def dr_true_ending(s):
        c=s.canvas;c.fill((7,10,19));pg=s.true_page
        if pg<3:
            lines=wrap(s.font,tr("real_%d"%pg),260)
            for i,line in enumerate(lines):s.text(line,160,70+i*15-len(lines)*5,(220,222,209))
        else:s.text(tr("real_title"),160,52,(245,221,158),s.big);s.text(tr("end_thanks"),160,110,(205,220,222));s.rich(tr("hint_next"),160,156,(150,170,180),s.tiny)
