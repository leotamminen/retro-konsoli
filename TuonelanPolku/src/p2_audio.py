
# ---------------- audio: everything synthesised in code ----------------
RATE = 22050
CH = 2
SFX = {}
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)

def _to_sound(fl, gain=1.0):
    """float list (-1..1) -> pygame Sound in the mixer's real format."""
    a = array.array("h")
    if CH == 2:
        a = array.array("h", bytes(4 * len(fl)))
        for i, v in enumerate(fl):
            sv = int(max(-1.0, min(1.0, v * gain)) * 30000); a[2 * i] = sv; a[2 * i + 1] = sv
    else:
        a = array.array("h", bytes(2 * len(fl)))
        for i, v in enumerate(fl): a[i] = int(max(-1.0, min(1.0, v * gain)) * 30000)
    return pygame.mixer.Sound(buffer=a.tobytes())

def tone(f0, f1, dur, vol=0.3, wave="sine", atk=0.004, dpow=2.0, lp=0.0, seed=1):
    """One synthesised blip: frequency sweep f0->f1, envelope, optional one-pole low-pass (lp 0..1)."""
    n = max(1, int(RATE * dur)); out = [0.0] * n; ph = 0.0; rnd = random.Random(seed); y = 0.0
    an = max(1, int(RATE * atk))
    for i in range(n):
        t = i / n; f = f0 + (f1 - f0) * t; ph += f / RATE
        if wave == "sine": v = math.sin(6.2831853 * ph)
        elif wave == "sq": v = 1.0 if (ph % 1) < 0.5 else -1.0
        elif wave == "tri": v = 4 * abs((ph % 1) - 0.5) - 1
        elif wave == "saw": v = 2 * (ph % 1) - 1
        else: v = rnd.uniform(-1, 1)
        if lp: y += lp * (v - y); v = y
        e = min(1.0, i / an) * (1 - t) ** dpow
        out[i] = v * vol * e
    return out

def smix(*parts):
    n = max(len(p) for p in parts); out = [0.0] * n
    for p in parts:
        for i, v in enumerate(p): out[i] += v
    return out

def pluck(freq, dur, bright=0.5, damp=0.997, seed=3):
    """Karplus-Strong string = the kantele voice."""
    n = int(RATE * dur); p = max(2, int(RATE / freq)); rnd = random.Random(seed)
    buf = [rnd.uniform(-1, 1) * bright for _ in range(p)]
    y = 0.0
    for i in range(p):                       # soften the initial burst
        y += 0.6 * (buf[i] - y); buf[i] = y * 1.7
    out = [0.0] * n; k = 0
    for i in range(n):
        a = buf[k]; b = buf[(k + 1) % p]
        v = (a + b) * 0.5 * damp; buf[k] = v; out[i] = a
        k += 1
        if k >= p: k = 0
    fade = int(RATE * 0.05)
    for i in range(min(fade, n)): out[n - 1 - i] *= i / fade
    return out

def init_audio():
    global RATE, CH
    ok = False
    for kw in ({"allowedchanges": 0}, {}):
        try:
            pygame.mixer.pre_init(RATE, -16, 2, 512)
            pygame.mixer.init(RATE, -16, 2, 512, **kw); ok = True; break
        except Exception as e:
            try: pygame.mixer.quit()
            except Exception: pass
    if not ok:
        print("audio disabled"); return False
    try:
        fr, fmt, ch = pygame.mixer.get_init()
        RATE = int(fr); CH = 2 if ch >= 2 else 1
        if fmt != -16: print("unexpected audio format", fmt)
        pygame.mixer.set_num_channels(24)
        build_sfx()
        MUSIC.start()
        return True
    except Exception as e:
        print("audio disabled:", e); return False

def build_sfx():
    def reg(name, fl, gain=1.0): SFX[name] = _to_sound(fl, gain)
    reg("select", tone(700, 700, 0.04, 0.25, "tri"))
    reg("confirm", smix(tone(520, 780, 0.1, 0.25, "tri"), tone(1040, 1040, 0.08, 0.1, "sine")))
    reg("back", tone(500, 300, 0.08, 0.25, "tri"))
    reg("jump", tone(240, 420, 0.1, 0.18, "tri", lp=0.5))
    reg("djump", tone(380, 700, 0.12, 0.18, "sine"))
    reg("land", tone(110, 60, 0.07, 0.35, "noise", lp=0.2))
    reg("swing", tone(900, 300, 0.09, 0.14, "noise", lp=0.25, dpow=1.0))
    reg("swing2", tone(600, 200, 0.16, 0.2, "noise", lp=0.18, dpow=1.0))
    reg("hit", smix(tone(200, 90, 0.1, 0.35, "noise", lp=0.4), tone(160, 60, 0.12, 0.3, "sine")))
    reg("hit2", smix(tone(150, 50, 0.2, 0.5, "noise", lp=0.3), tone(110, 40, 0.25, 0.45, "sine")))
    reg("hurt", smix(tone(260, 110, 0.18, 0.35, "saw", lp=0.2), tone(180, 80, 0.2, 0.25, "noise", lp=0.3)))
    reg("block", smix(tone(1400, 1100, 0.08, 0.2, "sq", lp=0.3), tone(300, 200, 0.07, 0.3, "noise", lp=0.5)))
    reg("parry", smix(tone(1800, 2400, 0.25, 0.22, "sine", dpow=1.5), tone(900, 1200, 0.2, 0.15, "tri")))
    reg("roll", tone(500, 150, 0.17, 0.12, "noise", lp=0.12, dpow=0.8))
    reg("flask", smix(tone(300, 500, 0.2, 0.2, "sine"), tone(500, 300, 0.2, 0.15, "tri")))
    reg("heal", smix(tone(520, 520, 0.4, 0.15, "sine", dpow=1), tone(780, 780, 0.4, 0.12, "sine", dpow=1), tone(1040, 1040, 0.4, 0.1, "sine", dpow=1)))
    reg("bonfire", smix(tone(110, 110, 0.7, 0.3, "saw", lp=0.05, dpow=1), tone(165, 165, 0.7, 0.2, "sine", dpow=1), tone(330, 330, 0.7, 0.14, "sine", dpow=1.5)))
    reg("souls", smix(tone(880, 1320, 0.2, 0.2, "sine"), tone(1320, 1760, 0.3, 0.14, "sine")))
    reg("levelup", smix(tone(440, 880, 0.5, 0.2, "tri", dpow=1), tone(660, 1320, 0.5, 0.15, "sine", dpow=1)))
    reg("edie", smix(tone(240, 50, 0.35, 0.3, "saw", lp=0.2), tone(200, 50, 0.35, 0.3, "noise", lp=0.25)))
    reg("die", smix(tone(200, 40, 1.2, 0.4, "saw", lp=0.1, dpow=1), tone(100, 35, 1.2, 0.4, "sine", dpow=1)))
    reg("bolt", smix(tone(1200, 400, 0.18, 0.2, "sine"), tone(900, 300, 0.2, 0.12, "noise", lp=0.15)))
    reg("orb", smix(tone(300, 120, 0.4, 0.3, "sine"), tone(500, 200, 0.4, 0.15, "tri")))
    reg("arrow", smix(tone(1500, 600, 0.1, 0.14, "noise", lp=0.3, dpow=1), tone(220, 120, 0.12, 0.2, "tri")))
    reg("bow", tone(160, 220, 0.08, 0.2, "tri", lp=0.4))
    reg("kantele", smix(_pl(293.7, 0.9, 0.5), _pl(440, 0.9, 0.4), _pl(587.3, 0.9, 0.3)))
    reg("lever", smix(tone(120, 80, 0.15, 0.4, "noise", lp=0.3), tone(240, 160, 0.1, 0.2, "sq", lp=0.3)))
    reg("gate", smix(tone(70, 50, 0.9, 0.4, "noise", lp=0.08, dpow=0.7), tone(55, 45, 0.9, 0.35, "saw", lp=0.1, dpow=0.7)))
    reg("pickup", smix(tone(660, 990, 0.2, 0.2, "sine"), tone(990, 1320, 0.35, 0.18, "sine")))
    reg("boom", smix(tone(80, 30, 0.5, 0.55, "sine", dpow=1.2), tone(120, 40, 0.5, 0.4, "noise", lp=0.1, dpow=1.2)))
    reg("roar", smix(tone(90, 55, 1.1, 0.4, "saw", lp=0.08, dpow=0.6), tone(130, 60, 1.1, 0.3, "noise", lp=0.1, dpow=0.6)))
    reg("warn", tone(1000, 1000, 0.05, 0.12, "tri"))
    reg("splash", tone(600, 200, 0.2, 0.18, "noise", lp=0.2))
    reg("fall", tone(500, 100, 0.4, 0.2, "tri", dpow=1))
    reg("revive", smix(tone(400, 800, 0.4, 0.2, "sine"), tone(600, 1200, 0.4, 0.15, "tri")))
    reg("join", smix(tone(520, 520, 0.12, 0.2, "tri"), tone(780, 780, 0.2, 0.2, "tri")))
    reg("crow", smix(tone(900, 500, 0.15, 0.15, "sq", lp=0.3), tone(700, 400, 0.18, 0.1, "saw", lp=0.3)))
    reg("ice", smix(tone(2000, 800, 0.2, 0.12, "sine"), tone(1400, 600, 0.25, 0.1, "tri")))

def _pl(f, d, v):
    return [x * v for x in pluck(f, d, 0.6, 0.996)]

def sfx(name, vol=1.0):
    if not SETTINGS["sfx"]: return
    s = SFX.get(name)
    if s:
        try: s.set_volume(min(1.0, SETTINGS["sfx_vol"] / 10 * vol)); s.play()
        except pygame.error: pass

# ---------------- music ----------------
def _wavetable(harm):
    n = 1024; t = [0.0] * n
    for h, a in harm:
        for i in range(n): t[i] += a * math.sin(6.2831853 * h * i / n)
    pk = max(abs(v) for v in t) or 1
    return [v / pk for v in t]
_CHOIR = None; _DRONE = None
def _tabs():
    global _CHOIR, _DRONE
    if _CHOIR is None:
        _CHOIR = _wavetable([(1, 1.0), (2, 0.55), (3, 0.5), (4, 0.18), (5, 0.12), (7, 0.07)])   # "oo-ah" vowel
        _DRONE = _wavetable([(1, 1.0), (2, 0.45), (3, 0.3), (4, 0.12), (5, 0.08)])
    return _CHOIR, _DRONE

def _osc(tab, freq, n, det=1.0, ph0=0.0):
    inc = freq * det * 1024.0 / RATE; ph = ph0; out = [0.0] * n
    for i in range(n):
        out[i] = tab[int(ph) & 1023]; ph += inc
    return out

def _mixin(buf, src, pos, amp):
    n = min(len(src), len(buf) - pos)
    if n <= 0: return
    buf[pos:pos + n] = [a + b * amp for a, b in zip(buf[pos:pos + n], src)]

def _kick():
    n = int(RATE * 0.45); out = []; ph = 0.0
    for i in range(n):
        t = i / RATE; f = 42 + 90 * math.exp(-t * 26); ph += f / RATE
        out.append(math.tanh(1.8 * math.sin(6.2831853 * ph)) * math.exp(-t * 7))
    return out
def _taiko():
    n = int(RATE * 0.7); out = []; ph = 0.0; rnd = random.Random(4); lp = 0.0
    for i in range(n):
        t = i / RATE; f = 70 + 60 * math.exp(-t * 18); ph += f / RATE
        lp += 0.15 * (rnd.uniform(-1, 1) - lp)
        out.append((math.sin(6.2831853 * ph) * 0.9 + lp * 0.5 * math.exp(-t * 30)) * math.exp(-t * 5.5))
    return out
def _shaker():
    n = int(RATE * 0.06); rnd = random.Random(9); out = []; lp = 0.0
    for i in range(n):
        v = rnd.uniform(-1, 1); lp += 0.5 * (v - lp)
        out.append((v - lp) * math.exp(-i / RATE * 60) * 0.5)
    return out

# name -> spec. chords are (bass midi, pad notes); mel = scale for the kantele line
TRACKS = {
 "title":  dict(bpm=58, seed=11, pad=0.045, drone=0.05, pluck=0.55, drums=None, echo=True, density=0.5,
                chords=[(38, [57, 62, 65]), (34, [58, 62, 65]), (31, [58, 62, 67]), (33, [57, 61, 64])],
                scale=[62, 64, 65, 67, 69, 70, 72, 74, 76], bars=16),
}

def render_classic(name):
    sp = TRACKS[name]; rnd = random.Random(sp["seed"])
    choir, dtab = _tabs()
    beat = 60.0 / sp["bpm"]; bar_n = int(RATE * beat * 4); st = bar_n // 16
    tail = int(RATE * 1.4); total = bar_n * sp["bars"]
    buf = [0.0] * (total + tail)
    padc = {}; drc = {}; plc = {}
    def get_pad(notes):
        k = tuple(notes)
        if k not in padc:
            n = bar_n + tail; acc = [0.0] * n
            for nt in notes:
                for det in (0.9965, 1.0035):
                    _mixin(acc, _osc(choir, midi(nt), n, det, rnd.random() * 1024), 0, 1.0)
            a = int(RATE * 1.1); r = int(RATE * 1.2)
            for i in range(min(a, n)): acc[i] *= i / a
            for i in range(min(r, n)): acc[n - 1 - i] *= i / r
            padc[k] = acc
        return padc[k]
    def get_drone(root):
        if root not in drc:
            n = bar_n + tail; f = midi(root - 12 if root > 40 else root)
            d = _osc(dtab, f, n, 1.0); d2 = _osc(dtab, f * 1.5, n, 1.002)
            acc = [a * 0.8 + b * 0.25 for a, b in zip(d, d2)]
            a = int(RATE * 0.8); r = int(RATE * 1.2)
            for i in range(min(a, n)): acc[i] *= i / a
            for i in range(min(r, n)): acc[n - 1 - i] *= i / r
            drc[root] = acc
        return drc[root]
    def get_pl(note):
        if note not in plc:
            p = pluck(midi(note), 2.4 if not sp.get("fast") else 0.9, 0.8 if sp.get("high") else 0.6, 0.9965 if not sp.get("fast") else 0.994, seed=note)
            if sp.get("echo"):
                d1 = int(RATE * beat * 0.75); d2 = int(RATE * beat * 1.5)
                p = p + [0.0] * d2
                for i in range(len(p) - d2 - 1, -1, -1):
                    p[i + d1] += p[i] * 0.33; p[i + d2] += p[i] * 0.16
            plc[note] = p
        return plc[note]
    K, T, S = (_kick(), _taiko(), _shaker()) if sp["drums"] else (None, None, None)
    scale = sp["scale"]; ci_of = lambda b: (b // 2) % 4
    motif = None
    for b in range(sp["bars"]):
        pos = b * bar_n; root, pad = sp["chords"][ci_of(b)]
        _mixin(buf, get_pad(pad), pos, sp["pad"])
        _mixin(buf, get_drone(root), pos, sp["drone"] * (1.0 if b % 2 == 0 else 0.85))
        if sp.get("dis") and b % 4 == 2:       # swamp: a second-interval beating note
            _mixin(buf, get_pad([pad[0] + 1]), pos, sp["pad"] * 0.5)
        # kantele line
        if b % 4 == 0 or motif is None:
            steps = [0, 3, 6, 8, 11, 14] if not sp.get("fast") else list(range(0, 16, 2))
            motif = []
            idx = rnd.randrange(2, len(scale) - 2)
            for s_ in steps:
                if rnd.random() < sp["density"]:
                    idx = max(0, min(len(scale) - 1, idx + rnd.choice([-2, -1, -1, 0, 1, 1, 2])))
                    motif.append((s_, scale[idx]))
        line = list(motif)
        if b % 4 == 3 and line:          # variation / cadence
            line = [(s_, n_ if s_ < 8 else scale[(scale.index(n_) + 1) % len(scale)]) for s_, n_ in line]
        if b % 8 >= 4 and not sp.get("fast"):
            line = [(s_, n_) for i, (s_, n_) in enumerate(line) if i % 2 == 0] if b % 8 in (5, 6) else line
        for (s_, n_) in line:
            if sp.get("fast") and n_ in (scale[0], scale[2]) and rnd.random() < 0.3: n_ = scale[0]
            _mixin(buf, get_pl(n_), pos + s_ * st, sp["pluck"] * (0.8 + 0.3 * rnd.random()))
        if sp.get("fast"):               # ostinato on the root
            for s_ in range(0, 16, 2):
                _mixin(buf, get_pl(root + 24), pos + s_ * st, sp["pluck"] * (0.5 if s_ % 4 else 0.75))
        if sp["drums"]:
            for s_, v in ((0, 1.0), (8, 0.9), (10, 0.6)):
                _mixin(buf, T, pos + s_ * st, 0.34 * v)
            for s_ in (0, 6, 12):
                _mixin(buf, K, pos + s_ * st, 0.42)
            for s_ in range(0, 16, 2): _mixin(buf, S, pos + s_ * st, 0.14 if s_ % 4 else 0.08)
        time.sleep(0.002)               # let the game thread run (background build)
    for i in range(tail): buf[i] += buf[total + i]
    buf = buf[:total]
    pk = max(abs(v) for v in buf) or 1.0
    return [math.tanh(v / pk * 1.15) * 0.8 for v in buf]

# ---------------- v1.1 music: a distinct piece per area and per boss ----------------
# Same palette as before (kantele plucks, choir/string pads, drones, frame drums) but every area and
# boss has its own key, mode, tempo, metre, rhythm and lead voice. "<boss>2" = phase 2: faster, more layers.
_TABS = {}
def _tab(kind):
    if kind not in _TABS:
        if kind == "choir": _TABS[kind] = _tabs()[0]
        elif kind == "drone": _TABS[kind] = _tabs()[1]
        elif kind == "string": _TABS[kind] = _wavetable([(h, 1.0 / h) for h in range(1, 9)])
        elif kind == "reed": _TABS[kind] = _wavetable([(1, 1.0), (2, 0.25), (3, 0.75), (4, 0.15), (5, 0.45), (7, 0.25), (9, 0.1)])
        elif kind == "voice": _TABS[kind] = _wavetable([(1, 1.0), (2, 0.35), (3, 0.6), (4, 0.1), (6, 0.08)])
    return _TABS[kind]

def _lead_note(inst, freq, dur, seed=1):
    """flute / reed / voice / horn: vibrato, breath and a soft envelope."""
    n = max(1, int(RATE * dur)); out = [0.0] * n; rnd = random.Random(seed)
    a = int(RATE * (0.06 if inst != "horn" else 0.09)); r = int(RATE * min(0.3, dur * 0.4)) or 1
    if inst == "flute":
        ph = 0.0; lp = 0.0
        for i in range(n):
            t = i / RATE; ph += freq * (1 + 0.006 * math.sin(31.4 * t) * min(1.0, t * 3)) / RATE
            x = 6.2831853 * ph; lp += 0.06 * (rnd.uniform(-1, 1) - lp)
            out[i] = (math.sin(x) + 0.16 * math.sin(2 * x) + lp * 0.5) * min(1.0, i / a) * min(1.0, (n - i) / r)
    elif inst == "horn":
        ph1 = 0.0; ph2 = 0.0; y = 0.0
        for i in range(n):
            ph1 += freq / RATE; ph2 += freq * 1.004 / RATE
            v = (ph1 % 1.0) + (ph2 % 1.0) - 1.0
            c = 0.03 + 0.16 * min(1.0, i / a); y += c * (v - y)
            out[i] = y * 2.2 * min(1.0, i / a) * min(1.0, (n - i) / r)
    else:
        tb = _tab(inst); ph = rnd.random() * 1024
        for i in range(n):
            t = i / RATE; ph += freq * (1 + 0.008 * math.sin(33.0 * t) * min(1.0, t * 2.5)) * 1024.0 / RATE
            out[i] = tb[int(ph) & 1023] * min(1.0, i / a) * min(1.0, (n - i) / r)
    return out

def _bell(freq, dur=2.6):
    n = int(RATE * dur); out = [0.0] * n
    for mult, amp, dec in ((1.0, 1.0, 1.1), (2.0, 0.45, 1.8), (2.76, 0.35, 2.4), (5.4, 0.18, 3.8), (8.93, 0.08, 6.0)):
        w = 6.2831853 * freq * mult / RATE
        for i in range(n): out[i] += math.sin(w * i) * amp * math.exp(-i / RATE * dec)
    for i in range(min(60, n)): out[i] *= i / 60
    return out

def _tom(f0=150):
    n = int(RATE * 0.4); out = []; ph = 0.0
    for i in range(n):
        t = i / RATE; ph += (f0 * 0.6 + f0 * 0.6 * math.exp(-t * 22)) / RATE
        out.append(math.sin(6.2831853 * ph) * math.exp(-t * 9))
    return out

def _drop():
    n = int(RATE * 0.12); out = []; ph = 0.0
    for i in range(n):
        t = i / n; ph += (1700 - 1100 * t) / RATE
        out.append(math.sin(6.2831853 * ph) * (1 - t) ** 2)
    return out

def _swell(dur=4.0, seed=5):
    n = int(RATE * dur); rnd = random.Random(seed); out = [0.0] * n; lp = 0.0; lp2 = 0.0
    for i in range(n):
        lp += 0.05 * (rnd.uniform(-1, 1) - lp); lp2 += 0.05 * (lp - lp2)
        out[i] = (lp - lp2) * 3.0 * math.sin(3.14159 * i / n) ** 2
    return out

def _echo(p, d1, d2, f1=0.33, f2=0.16):
    p = p + [0.0] * d2
    for i in range(len(p) - d2 - 1, -1, -1):
        p[i + d1] += p[i] * f1; p[i + d2] += p[i] * f2
    return p

def _fade(acc, a, r):
    n = len(acc)
    for i in range(min(a, n)): acc[i] *= i / a
    for i in range(min(r, n)): acc[n - 1 - i] *= i / r
    return acc

C_DM, C_C, C_G, C_AM = (38, [57, 62, 65]), (36, [55, 60, 64]), (31, [55, 59, 62]), (33, [57, 60, 64])
SONGS = {
 # Metsä: D dorian, lilting 6/8, string pad, kantele arpeggios, wooden flute, soft frame drum
 "forest": dict(bpm=84, steps=12, bars=16, seed=21, chords=[C_DM, C_C, C_G, C_AM], chord_bars=2,
                scale=[62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79],
                pad=("string", 0.032), drone=0.03, pluck=dict(mode="arp", amp=0.42, steps=[0, 2, 4, 6, 8, 10], octave=12),
                lead=dict(inst="flute", amp=0.26, bars=range(4, 16), rhythm=[(0, 4), (4, 2), (6, 4), (10, 2), (12, 6), (18, 2), (20, 4)]),
                drums=dict(taiko=[(0, 0.45), (6, 0.25)], shaker=[(s_, 0.06) for s_ in range(0, 12, 2)])),
 # Suo: F phrygian murk, very slow, choir with a beating second, water drops, wind, low reed groans, heartbeat
 "swamp":  dict(bpm=46, steps=16, bars=12, seed=31, chords=[(41, [53, 56, 60]), (42, [54, 58, 61]), (41, [53, 56, 60]), (40, [52, 56, 59])], chord_bars=2,
                scale=[65, 66, 68, 70, 72, 73, 75, 77], dis=True,
                pad=("choir", 0.05), drone=0.075, pluck=dict(mode="sparse", amp=0.42, prob=0.3, echo=True),
                lead=dict(inst="reed", amp=0.16, bars=range(6, 12), octave=-12, rhythm=[(0, 12), (16, 8), (24, 8)]),
                drops=0.2, swell=0.16, drums=dict(taiko=[(0, 0.32), (3, 0.18)])),
 # Tuonelan joki: C# minor with the harmonic-minor V, tolling bell, cor anglais (reed) lead, glassy echoes
 "river":  dict(bpm=60, steps=16, bars=16, seed=41, chords=[(37, [61, 64, 68]), (33, [61, 64, 69]), (30, [61, 66, 69]), (32, [60, 63, 68])], chord_bars=2,
                scale=[61, 63, 64, 66, 68, 69, 72, 73, 75, 76],
                pad=("choir", 0.045), drone=0.045, pluck=dict(mode="motif", amp=0.22, density=0.45, octave=12, echo=True),
                lead=dict(inst="reed", amp=0.24, bars=range(2, 16), rhythm=[(0, 6), (6, 2), (8, 8), (16, 4), (20, 4), (24, 8)]),
                bell=dict(amp=0.16, steps=[0])),
 # Hiisi: A aeolian forest war-dance, taiko + toms, kantele ostinato, horn
 "boss_hiisi":  dict(bpm=116, steps=16, bars=16, seed=51, chords=[(33, [57, 60, 64]), (29, [57, 60, 65]), (31, [55, 59, 62]), (28, [56, 59, 64])], chord_bars=2,
                scale=[57, 59, 60, 62, 64, 65, 67, 69, 72],
                pad=("string", 0.03), drone=0.05, pluck=dict(mode="ostinato", amp=0.42, steps=list(range(0, 16, 2)), octs=[24, 12, 24, 19]),
                lead=dict(inst="horn", amp=0.2, bars=range(8, 16), octave=-12, rhythm=[(0, 6), (6, 2), (8, 6), (16, 4), (20, 4), (24, 8)]),
                drums=dict(taiko=[(0, 1.0), (6, 0.7), (10, 0.8)], kick=[(0, 1.0), (8, 0.8)], tom=[(12, 0.5), (14, 0.6)], shaker=[(s_, 0.1) for s_ in range(0, 16, 2)])),
 "boss_hiisi2": dict(bpm=128, steps=16, bars=16, seed=52, chords=[(33, [57, 60, 64]), (29, [57, 60, 65]), (31, [55, 59, 62]), (28, [56, 59, 64])], chord_bars=2,
                scale=[57, 59, 60, 62, 64, 65, 67, 69, 72],
                pad=("string", 0.04), drone=0.06, pluck=dict(mode="ostinato", amp=0.4, steps=list(range(16)), octs=[24, 12, 19, 12]),
                lead=dict(inst="horn", amp=0.24, bars=range(0, 16), octave=-12, rhythm=[(0, 4), (4, 2), (6, 2), (8, 6), (16, 4), (20, 2), (22, 2), (24, 8)]),
                stabs=dict(amp=0.16, steps=[0, 3, 6]),
                drums=dict(taiko=[(0, 1.0), (3, 0.6), (6, 0.8), (10, 0.9), (13, 0.6)], kick=[(0, 1.0), (4, 0.8), (8, 0.9), (12, 0.8)], tom=[(12, 0.6), (14, 0.7), (15, 0.5)], shaker=[(s_, 0.1 if s_ % 2 else 0.14) for s_ in range(16)])),
 # Iku-Turso: Bb phrygian in 7/8 (2+2+3), deep gong swells, low reed, toms
 "boss_turso":  dict(bpm=100, steps=14, bars=16, seed=61, chords=[(34, [58, 61, 65]), (35, [59, 63, 66]), (34, [58, 61, 65]), (32, [56, 60, 63])], chord_bars=2,
                scale=[58, 59, 61, 63, 65, 66, 68, 70, 71],
                pad=("choir", 0.05), drone=0.08, pluck=dict(mode="ostinato", amp=0.36, steps=[0, 2, 4, 6, 8, 10, 12], octs=[12, 12, 19, 12, 13, 12, 7]),
                lead=dict(inst="reed", amp=0.2, bars=range(4, 16), octave=-12, rhythm=[(0, 8), (8, 6), (14, 4), (18, 10)]),
                swell=0.2, drums=dict(tom=[(0, 1.0), (4, 0.7), (8, 0.9)], taiko=[(0, 0.8)], shaker=[(s_, 0.07) for s_ in range(0, 14, 2)])),
 "boss_turso2": dict(bpm=112, steps=14, bars=16, seed=62, chords=[(34, [58, 61, 65]), (35, [59, 63, 66]), (34, [58, 61, 65]), (32, [56, 60, 63])], chord_bars=2,
                scale=[58, 59, 61, 63, 65, 66, 68, 70, 71],
                pad=("choir", 0.06), drone=0.085, pluck=dict(mode="ostinato", amp=0.34, steps=list(range(14)), octs=[12, 24, 19, 24, 13, 24, 12]),
                lead=dict(inst="reed", amp=0.22, bars=range(0, 16), octave=-12, rhythm=[(0, 4), (4, 4), (8, 6), (14, 4), (18, 4), (22, 6)]),
                bell=dict(amp=0.12, steps=[0, 8]), swell=0.22,
                drums=dict(tom=[(0, 1.0), (2, 0.5), (4, 0.8), (8, 1.0), (11, 0.6)], kick=[(0, 1.0), (4, 0.8), (8, 0.9)], taiko=[(0, 0.9), (8, 0.6)], shaker=[(s_, 0.09) for s_ in range(14)])),
 # Tuonen Tytti: D harmonic minor dark waltz in 6/8, choir lead voice, tolling bells, kantele tremolo
 "boss_tytti":  dict(bpm=120, steps=12, bars=24, seed=71, chords=[(38, [62, 65, 69]), (34, [62, 65, 70]), (31, [62, 67, 70]), (33, [61, 64, 69])], chord_bars=2,
                scale=[62, 64, 65, 67, 69, 70, 73, 74, 76, 77],
                pad=("choir", 0.06), drone=0.05, pluck=dict(mode="arp", amp=0.36, steps=[0, 2, 4, 6, 8, 10], octave=12),
                lead=dict(inst="voice", amp=0.24, bars=range(4, 16), rhythm=[(0, 6), (6, 6), (12, 4), (16, 2), (18, 6)]),
                bell=dict(amp=0.16, steps=[0]), drums=dict(taiko=[(0, 0.9), (6, 0.6)], kick=[(0, 0.8)], shaker=[(s_, 0.07) for s_ in range(0, 12, 2)])),
 "boss_tytti2": dict(bpm=132, steps=12, bars=24, seed=72, chords=[(38, [62, 65, 69]), (34, [62, 65, 70]), (31, [62, 67, 70]), (33, [61, 64, 69])], chord_bars=2,
                scale=[62, 64, 65, 67, 69, 70, 73, 74, 76, 77],
                pad=("choir", 0.07), drone=0.06, pluck=dict(mode="tremolo", amp=0.3, octave=12),
                lead=dict(inst="voice", amp=0.26, bars=range(0, 16), double=True, rhythm=[(0, 4), (4, 2), (6, 6), (12, 4), (16, 2), (18, 6)]),
                stabs=dict(amp=0.12, steps=[0, 6]), bell=dict(amp=0.16, steps=[0, 6]),
                drums=dict(taiko=[(0, 1.0), (3, 0.6), (6, 0.8), (9, 0.6)], kick=[(0, 1.0), (6, 0.9)], tom=[(10, 0.5), (11, 0.6)], shaker=[(s_, 0.08) for s_ in range(12)])),
}
TRACK_ORDER = ["title", "forest", "swamp", "river", "boss_hiisi", "boss_hiisi2", "boss_turso", "boss_turso2", "boss_tytti", "boss_tytti2"]

def compose(name):
    sp = SONGS[name]; rnd = random.Random(sp["seed"])
    steps = sp.get("steps", 16); st = int(RATE * 60.0 / sp["bpm"] / 4); bar_n = st * steps
    bars = sp["bars"]; total = bar_n * bars; tail = int(RATE * 2.5); buf = [0.0] * (total + tail)
    chords = sp["chords"]; cb = sp.get("chord_bars", 2); scale = sp["scale"]
    cache = {}
    def C(key, fn):
        if key not in cache: cache[key] = fn()
        return cache[key]
    def pl(note, dur=1.6):
        def mk():
            p = pluck(midi(note), dur, 0.65, 0.9955, seed=note)
            if sp["pluck"].get("echo"): p = _echo(p, st * 3, st * 6)
            return p
        return C(("pl", note, dur), mk)
    def sustain(kind, notes, n):
        def mk():
            acc = [0.0] * n; tb = _tab(kind)
            for nt in notes:
                for det in (0.9965, 1.0035): _mixin(acc, _osc(tb, midi(nt), n, det, rnd.random() * 1024), 0, 1.0)
            return _fade(acc, int(RATE * 0.9), int(RATE * 1.2))
        return C(("sus", kind, tuple(notes), n), mk)
    def drone(root, n):
        def mk():
            f = midi(root - 12 if root > 40 else root); tb = _tab("drone")
            d = _osc(tb, f, n); d2 = _osc(tb, f * 1.5, n, 1.002)
            return _fade([a * 0.8 + b * 0.25 for a, b in zip(d, d2)], int(RATE * 0.8), int(RATE * 1.2))
        return C(("dr", root, n), mk)
    DR = {"kick": C("kick", _kick), "taiko": C("taiko", _taiko), "shaker": C("shaker", _shaker), "tom": C("tom", _tom)}
    # lead phrases: A A' B A'' over 2-bar cells
    ld = sp.get("lead"); phrases = []
    if ld:
        def phrase(start):
            idx = start; out = []
            for (s_, ln) in ld["rhythm"]:
                idx = max(0, min(len(scale) - 1, idx + rnd.choice([-2, -1, -1, 0, 1, 1, 2])))
                out.append((s_, ln, scale[idx]))
            return out
        A = phrase(len(scale) // 2); B = phrase(len(scale) // 2 + 2)
        A2 = A[:-1] + [(A[-1][0], A[-1][1], scale[0] + (12 if scale[0] < 60 else 0))]
        phrases = [A, A2, B, A2]
    motif = None
    for b in range(bars):
        pos = b * bar_n; root, pad = chords[(b // cb) % len(chords)]
        if b % cb == 0:
            n = bar_n * cb + int(RATE * 1.2)
            if sp.get("pad"): _mixin(buf, sustain(sp["pad"][0], pad, n), pos, sp["pad"][1])
            _mixin(buf, drone(root, n), pos, sp["drone"])
            if sp.get("dis") and (b // cb) % 2 == 1: _mixin(buf, sustain("choir", [pad[0] + 1], n), pos, sp["pad"][1] * 0.5)
        # kantele
        pk = sp["pluck"]; mode = pk["mode"]; amp = pk["amp"]
        if mode == "arp":
            tones = [n_ + pk.get("octave", 0) for n_ in pad] + [pad[0] + 12 + pk.get("octave", 0)]
            seq = tones + tones[-2:0:-1]
            for j, s_ in enumerate(pk["steps"]): _mixin(buf, pl(seq[(j + b) % len(seq)]), pos + s_ * st, amp * (1.0 if j == 0 else 0.75))
        elif mode == "ostinato":
            for j, s_ in enumerate(pk["steps"]):
                o = pk["octs"][j % len(pk["octs"])]; _mixin(buf, pl(root + o, 0.7), pos + s_ * st, amp * (1.0 if s_ == 0 else 0.7))
        elif mode == "tremolo":
            for s_ in range(steps):
                n_ = pad[(s_ // 3) % len(pad)] + pk.get("octave", 0); _mixin(buf, pl(n_, 0.5), pos + s_ * st, amp * (0.9 if s_ % 3 == 0 else 0.55))
        elif mode == "sparse":
            for beat in range(steps // 4):
                if rnd.random() < pk["prob"]: _mixin(buf, pl(rnd.choice(scale)), pos + beat * 4 * st + rnd.choice([0, 0, 2]) * st, amp * (0.6 + 0.4 * rnd.random()))
        else:   # motif, as in v1.0
            if b % 4 == 0 or motif is None:
                motif = []; idx = rnd.randrange(2, len(scale) - 2)
                for s_ in [0, 3, 6, 8, 11, 14]:
                    if s_ < steps and rnd.random() < pk["density"]:
                        idx = max(0, min(len(scale) - 1, idx + rnd.choice([-2, -1, -1, 0, 1, 1, 2]))); motif.append((s_, scale[idx] + pk.get("octave", 0)))
            for (s_, n_) in motif: _mixin(buf, pl(n_), pos + s_ * st, amp * (0.8 + 0.3 * rnd.random()))
        # lead (2-bar cells)
        if ld and b in ld["bars"] and b % 2 == 0:
            ph = phrases[(b // 2) % len(phrases)]
            for (s_, ln, n_) in ph:
                n_ += ld.get("octave", 0); d = ln * st / RATE + 0.08
                v = C(("ld", ld["inst"], n_, ln), lambda: _lead_note(ld["inst"], midi(n_), d, n_))
                _mixin(buf, v, pos + s_ * st, ld["amp"])
                if ld.get("double"): _mixin(buf, C(("ld", ld["inst"], n_ - 12, ln), lambda: _lead_note(ld["inst"], midi(n_ - 12), d, n_ + 1)), pos + s_ * st, ld["amp"] * 0.6)
        if sp.get("stabs"):
            for s_ in sp["stabs"]["steps"]:
                for n_ in (root + 24, root + 31):
                    _mixin(buf, C(("stab", n_), lambda: _lead_note("horn", midi(n_), st * 2 / RATE + 0.05, n_)), pos + s_ * st, sp["stabs"]["amp"])
        if sp.get("bell"):
            for s_ in sp["bell"]["steps"]: _mixin(buf, C(("bell", root), lambda: _bell(midi(root + 36))), pos + s_ * st, sp["bell"]["amp"])
        if sp.get("drops"):
            for k in range(rnd.randint(0, 3)): _mixin(buf, C("drop", lambda: _echo(_drop(), st * 3, st * 6, 0.4, 0.2)), pos + rnd.randrange(steps) * st, sp["drops"] * (0.4 + 0.6 * rnd.random()))
        if sp.get("swell") and b % 4 == 0: _mixin(buf, C("swell", _swell), pos, sp["swell"])
        for inst, pat in sp.get("drums", {}).items():
            for s_, v in pat: _mixin(buf, DR[inst], pos + s_ * st, 0.4 * v)
        time.sleep(0.002)              # let the game thread run (background build)
    for i in range(tail): buf[i] += buf[total + i]
    buf = buf[:total]; cache.clear()
    rms = (sum(v * v for v in buf[::5]) / max(1, len(buf[::5]))) ** 0.5 or 1.0   # equal loudness between pieces
    g = (0.15 if name.startswith("boss") else 0.125) / rms
    return [math.tanh(v * g / 0.8) * 0.8 for v in buf]

def render_track(name):
    return render_classic(name) if name in TRACKS else compose(name)

CACHE_VERSION = 5       # bump whenever a synthesis rule or the mixer format changes
def music_cache_dir():
    return os.environ.get("TUONELA_MUSIC_CACHE") or os.path.join(os.path.dirname(settings_path()), "tuonela_music_v%d" % CACHE_VERSION)
def _cache_path(name):
    if name not in TRACK_ORDER: raise ValueError("unknown music track")
    return os.path.join(music_cache_dir(), "%s_%d_%d.raw" % (name, RATE, CH))
def load_cached_track(name):
    """Disk cache: validated 16-bit mixer-native PCM, atomic writes below."""
    path = _cache_path(name)
    try:
        size = os.path.getsize(path)
        if size < RATE * CH * 2 or size > RATE * CH * 2 * 100 or size % (CH * 2): return None
        with open(path, "rb") as f: data = f.read()
        return pygame.mixer.Sound(buffer=data)
    except (OSError, pygame.error, ValueError, MemoryError): return None
class MusicPlayer:
    """Disk-cached process-isolated synthesis. Audio conversion is moved off the combat frame path."""
    LIKELY={"title":[],"forest":[],"swamp":[],"river":[],
            "boss_hiisi":["boss_hiisi2"],"boss_turso":["boss_turso2"],"boss_tytti":["boss_tytti2"],
            "pohjola":["louhi"],"louhi":["louhi2"],"louhi2":["louhi3"]}
    def __init__(s):
        s.tracks={};s.building={};s.want=None;s.cur=None;s.process=sys.platform!="win32" and not os.environ.get("TUONELA_THREAD_MUSIC")
        s.loading={};s.audio_worker=[];s.cache_hits=0;s.cache_misses=0;s.generating=False
    def start(s):return 0
    def _ordered(s):
        if not s.want:return []
        return [s.want]+[n for n in s.LIKELY.get(s.want,[]) if n!=s.want]
    def _queue(s):
        if not s.want or os.environ.get("TUONELA_NO_MUSIC"):return
        # Two current/likely tasks only. No boot all-track synthesis.
        for name in s._ordered():
            if len(s.building)>=2:break
            if name in s.tracks or name in s.building or name not in TRACK_ORDER:continue
            s.building[name]=True;s.cache_misses+=1
            if os.path.isfile(_cache_path(name)):
                s.start_audio_load(name);s.building.pop(name,None)
            elif s.process:
                try:
                    import multiprocessing as mp
                    proc=mp.get_context("fork").Process(target=_cache_worker,args=(name,_cache_path(name)),daemon=True)
                    s.building[name]=proc;proc.start()
                except Exception:
                    s.building.pop(name,None);s.process=False
            else:
                th=threading.Thread(target=s._thread_build,args=(name,),daemon=True);s.building[name]=th;th.start()
    def _thread_build(s,name):
        _cache_worker(name,_cache_path(name));s.building[name]=True
    def begin_music_load(s,name=None):
        if name:s.request(name)
        s._queue()
    def start_audio_load(s,name):
        if name in s.loading or name in s.tracks:return
        slot=[name,None];s.loading[name]=slot
        th=threading.Thread(target=s._load_slot,args=(slot,),daemon=True);s.audio_worker.append((name,th));th.start()
    def _load_slot(s,slot):
        try:
            data=open(_cache_path(slot[0]),"rb").read()
            if len(data)<RATE*CH*2*2 or len(data)>RATE*CH*2*100 or len(data)%(CH*2):raise ValueError("bad length")
            slot[1]=pygame.mixer.Sound(buffer=data)
        except (OSError,pygame.error,ValueError):
            slot[1]=None
    def invalidate_bad_cache(s,name):
        try:os.unlink(_cache_path(name))
        except OSError:pass
    def update_failed(s,name):
        s.invalidate_bad_cache(name)
        if name not in s.building:
            if s.process:
                try:
                    import multiprocessing as mp
                    p=mp.get_context("fork").Process(target=_cache_worker,args=(name,_cache_path(name)),daemon=True)
                    s.building[name]=p;p.start()
                except Exception:s.building.pop(name,None);s.process=False
            if not s.process and name not in s.building:
                p=threading.Thread(target=s._thread_build,args=(name,),daemon=True);s.building[name]=p;p.start()
    def request(s,name):s.want=name
    def volume(s):return .6*SETTINGS["music_vol"]/10
    def update(s):
        for name,th in list(s.audio_worker):
            if th.is_alive():continue
            slot=s.loading.pop(name,None)
            if slot and slot[1] is not None:s.tracks[name]=slot[1];s.cache_hits+=1
            elif slot is not None:s.update_failed(name)
            s.audio_worker.remove((name,th))
        keep=set(s._ordered())
        if s.cur:keep.add(s.cur)
        for n in list(s.tracks):
            if n not in keep:s.tracks.pop(n,None)
        for n,proc in list(s.building.items()):
            if proc is True or not hasattr(proc,"is_alive"):continue
            if not proc.is_alive():s.building[n]=True
        s.generating=False
        for n,val in list(s.building.items()):
            if val is not True:s.generating=True;continue
            s.building.pop(n,None)
            if n in keep:s.start_audio_load(n)
        try:
            if not SETTINGS["music"]:
                if s.cur in s.tracks:s.tracks[s.cur].stop();s.cur=None
            elif s.want and s.want!=s.cur and s.want in s.tracks:
                if s.cur in s.tracks:s.tracks[s.cur].fadeout(250)
                snd=s.tracks[s.want];snd.set_volume(s.volume());snd.play(loops=-1,fade_ms=350);s.cur=s.want
            elif s.cur in s.tracks:s.tracks[s.cur].set_volume(s.volume())
        except (pygame.error,OSError):pass
        s._queue()
def _cache_worker(name, path):
    """Separate process, so Python synthesis cannot hold the game's GIL."""
    try:
        raw = _to_sound(render_track(name), 0.9).get_raw()
        tmp = path + ".%d.tmp" % os.getpid()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "wb") as f: f.write(raw)
        os.replace(tmp, path)
    except BaseException:           # cache is optional; never take down the game
        try: os.unlink(path + ".%d.tmp" % os.getpid())
        except OSError: pass

def compose_louhi(name):
    """Original Pohjola theme: low dissonant bow, frame drum and broken kantele."""
    phase=int(name[-1]) if name[-1].isdigit() else 1
    tempo=58+14*phase;beats=32;loop=beats*60/tempo
    total=int(loop*RATE);buf=[0.0]*(total+int(RATE*2));cache={};tail=int(RATE*2)
    bd=tone(105,38,.32,.55,"sine");snare=tone(850,240,.11,.25,"noise",lp=.35);hat=tone(8000,4200,.025,.1,"noise")
    def bow(freq,phase):
        n=int(RATE*.7);out=[0.0]*n;ph=ph2=0
        for i in range(n):
            ph+=freq/RATE;ph2+=freq*(1.009+.003*phase)/RATE
            env=min(1,i/(RATE*.12))*max(0,1-i/n)**2
            out[i]=(math.sin(ph*math.tau)+.7*math.sin(ph2*math.tau)+.22*math.sin(ph*math.tau*2.003))*env
        return out
    def add(key,fn):
        if key not in cache:cache[key]=fn()
        return cache[key]
    for b in range(beats*2):
        st=60.0/tempo/2;pos=int(b*st*RATE)
        base=(38 if b%4==0 else 35) if b%2==0 else 37
        _mixin(buf,add(('bow',base,phase),lambda:bow(midi(base),phase)),pos,.13+.018*phase)
        if b%4==0:_mixin(buf,add(('swell',),_swell),pos,.045+.008*phase)
        if b%2==0:_mixin(buf,bd,pos,.45+.025*phase)
        if b%8 in (3,5):_mixin(buf,snare,pos,.17+.014*phase)
        if phase>1:_mixin(buf,hat,pos,.09*phase)
        if b%4==2:
            note=[63,62,64,61][(b//4)%4]
            geom=add(('pl',note),lambda:pluck(midi(note),.8,.4,seed=note))
            _mixin(buf,geom,pos,.24)
        time.sleep(.001)
    for i in range(tail):buf[i]+=buf[total+i]
    buf=buf[:total];cache.clear();rms=(sum(v*v for v in buf[::5])/max(1,len(buf[::5])))**.5 or 1
    return [math.tanh(v*.12/rms/.8)*.8 for v in buf]
_original_render=render_track
def render_track(name):
    if name in ("louhi","louhi2","louhi3"):return compose_louhi(name)
    return _original_render(name)
TRACK_ORDER+=("pohjola","louhi","louhi2","louhi3")
for _n in ("louhi","louhi2","louhi3"):TRACKS.setdefault(_n,{});TRACKS[_n].setdefault("key",0);TRACKS[_n].setdefault("tempo",58+14*(int(_n[-1]) if _n[-1].isdigit() else 1));TRACKS[_n].setdefault("meter",8)
TRACKS["pohjola"]={"key":0,"tempo":42,"meter":8}
_orig_louhi_render=render_track
def render_track(name):
    if name=="pohjola":
        _result=[]
        for i in range(RATE*17):
            v=math.sin(2*math.pi*midi(36)*i/RATE)*.014+math.sin(2*math.pi*midi(43)*i/RATE)*.012
            _result.append(v*(.4+.6*math.sin(math.pi*i/(RATE*17))))
        return _result
    return _orig_louhi_render(name)
MusicPlayer.LIKELY["pohjola"]=["louhi"]
MUSIC=MusicPlayer()
MUSIC_SCHEME={"title":True}
