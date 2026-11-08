"""Renders every music track and writes short WAV previews to music_previews/ (+ timing and size report)."""
import os, sys, time, wave, array
from lib import *
OUT = os.path.join(ROOT, "music_previews", "1.3" if os.environ.get("TP_13") else "1.2"); os.makedirs(OUT, exist_ok=True)
secs = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
names = sys.argv[2:] or G["TRACK_ORDER"]
tot = 0
for i, n in enumerate(names):
    t0 = time.time(); fl = G["render_track"](n); dt = time.time() - t0
    loop_s = len(fl) / G["RATE"]; tot += len(fl) * 4      # in-game: 16-bit stereo
    k = int(min(len(fl), secs * G["RATE"])); fade = int(G["RATE"] * 1.0)
    a = array.array("h", (int(max(-1, min(1, v * (min(1.0, (k - j) / fade)))) * 30000) for j, v in enumerate(fl[:k])))
    fn = os.path.join(OUT, "%02d_%s.wav" % (i + 1, n))
    with wave.open(fn, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(G["RATE"]); w.writeframes(a.tobytes())
    pk = max(abs(v) for v in fl); rms = (sum(v * v for v in fl[::7]) / len(fl[::7])) ** 0.5
    print("%-12s bpm %3d  loop %5.1f s  render %5.2f s  peak %.2f rms %.3f -> %s" % (n, (G["SONGS"].get(n) or {}).get("bpm",G["TRACKS"][n].get("tempo",0)), loop_s, dt, pk, rms, os.path.basename(fn)))
print("in-game memory for all tracks: %.1f MB" % (tot / 1e6))
