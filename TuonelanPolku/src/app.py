
# ---------------- the game object and main loop ----------------
class Game(GameCore, GameUI):
    def __init__(s, screen, test=False):
        s.screen = screen; s.test = test; s.canvas = pygame.Surface((W, H))
        s.init_core(); s.init_ui()
        s.pads = {}; kb = Pad("kb"); s.pads[kb.id] = kb; s.kb = kb
        s.running = True; s.title_save = None; s.title_status = "none"; s.pending = None; s.pend_pad = kb
        s.ctl_from = "title"; s.last_pad = None; s.mapimg = None; s.mapseen = set()
        s.frame_ms = []; s.update_ms=0; s.draw_ms=0;s.input_ms = 0.0; s.overlay = False; s.frame_no = 0;s.frames=0;s.event_samples=[];s.input_to_action_frames=None;s.pending_action=set()
        load_settings()
        s.open_title()
        if not test: MUSIC.start()
    # ----- devices -----
    def add_pad(s, p): s.pads[p.id] = p
    def handle_device(s, ev):
        if ev.type == pygame.JOYDEVICEADDED:
            idx = ev.device_index
            try:
                joy = pygame.joystick.Joystick(idx)   # one Joystick handle per device; keep it alive on the Pad
            except Exception:
                return
            iid = joy.get_instance_id(); p = None
            try:
                from pygame._sdl2 import controller
                if not controller.get_init():
                    try: controller.init()
                    except Exception: pass
                if controller.is_controller(idx):
                    try: con = controller.Controller.from_joystick(joy)
                    except Exception: con = controller.Controller(idx)
                    p = Pad("gc", con, iid=iid, joy=joy)
            except Exception:
                p = None
            if p is None:
                p = Pad("js", joy, iid=iid, joy=joy)
            s.add_pad(p)
        elif ev.type == pygame.JOYDEVICEREMOVED:
            s.lose_pad("js%d" % ev.instance_id)
    def lose_pad(s, pid):
        gone = s.pads.pop(pid, None)
        if gone is None: return
        if s.last_pad is gone: s.last_pad = None
        for i in (1, 0):
            if i < len(s.players) and s.p_pad[i] is gone:
                idle = IdlePad(); s.players[i].pad = idle; s.p_pad[i] = idle
                if i == 1: s.remove_p2()
                else: s.need_pad = 0
        if s.pend_pad is gone: s.pend_pad = s.kb
    # ----- frame -----
    def poll(s):
        ks = pygame.key.get_pressed()
        seen = set()
        for p in list(s.pads.values()) + [q for q in s.p_pad if q is not None]:
            if id(p) in seen: continue
            seen.add(id(p)); p.poll(ks)
        if any(p.held("back") and p.held("start") for p in s.pads.values()): s.quit_hold += 1
        else: s.quit_hold = 0
        if s.quit_hold >= 60:
            if s.save is not None: s.save_game()
            s.running = False
    def queue_event_sample(s,events,frame=None):
        if frame is None:frame=s.frames
        s.event_samples.append((frame,list(events)))
    def poll_events(s):
        if s.test: return
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: s.running = False
            elif ev.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED): s.handle_device(ev)
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: _ESC[0] = True
    def update(s):
        t0 = time.perf_counter(); s.frame_begin = t0; s.frame_no += 1; s.poll_events()
        if s.event_samples:
            stamp,ev=s.event_samples[-1]
            for attrs in ev:
                if attrs.get("type") in (pygame.KEYDOWN,pygame.JOYBUTTONDOWN,pygame.CONTROLLERBUTTONDOWN):s.input_to_action_frames=s.frames-stamp;break

        s.input_ms = (time.perf_counter() - t0) * 1000.0
        s.t_ui += 1; s.poll(); MUSIC.update()
        if s.state_name == "play" and s.need_pad is not None: s.open_pause()
        getattr(s, "up_" + s.state_name)()
    def draw(s):
        t0 = time.perf_counter()
        getattr(s, "dr_" + s.state_name)()
        s.overlay = SETTINGS.get("perf", False)
        if s.overlay and s.state_name == "play": s.draw_perf_overlay()
        dt = (time.perf_counter() - t0) * 1000.0
        s.draw_ms=dt;s.update_ms=(t0-s.frame_begin)*1000.0
        s.frame_ms.append((time.perf_counter()-s.frame_begin)*1000.0)
        if len(s.frame_ms) > 1200: del s.frame_ms[:240]
        c = s.canvas
        if s.quit_hold > 5:
            bw = 100; pygame.draw.rect(c, (0, 0, 0), (W // 2 - bw // 2, 4, bw, 12)); pygame.draw.rect(c, (255, 255, 255), (W // 2 - bw // 2 - 1, 3, bw + 2, 14), 1)
            pygame.draw.rect(c, (230, 60, 60), (W // 2 - bw // 2 + 1, 5, min(bw - 2, int((bw - 2) * s.quit_hold / 60)), 10)); s.text(tr("quitting"), W // 2, 10)
        ox = oy = 0
        if s.shk_t > 0 and SETTINGS["shake"] and s.state_name == "play":
            a = s.shk_amp * min(1.0, s.shk_t / 8.0); ox = int(random.uniform(-a, a)); oy = int(random.uniform(-a, a))
        if ox or oy: s.screen.fill((0, 0, 0))
        s.screen.blit(c, (ox, oy))

def main():
    os.environ.setdefault("SDL_GAMECONTROLLER_ALLOW_BACKGROUND_EVENTS", "1")
    load_settings()
    init_audio()
    pygame.init()
    flags = pygame.SCALED | pygame.FULLSCREEN
    if os.environ.get("TUONELA_WINDOWED"): flags = pygame.SCALED
    screen = pygame.display.set_mode((W, H), flags, vsync=1)
    pygame.display.set_caption("TUONELAN POLKU")
    pygame.mouse.set_visible(False)
    try:
        from pygame._sdl2 import controller; controller.init()
    except Exception: pass
    g = Game(screen)
    clock = pygame.time.Clock()
    while g.running:
        g.update(); g.draw()
        pygame.display.flip()
        clock.tick(60)
    if g.save is not None: g.save_game()
    save_settings()
    pygame.quit()
