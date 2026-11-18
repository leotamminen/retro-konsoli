# Short synthesized blips. Music is built once, never inside the frame.
import array
import math
import os

import pygame

_SFX = {}
_READY = False


def _tone(freq, dur, vol=0.25, wave="sq", slide=0.0):
    rate = 22050
    n = max(1, int(rate * dur))
    buf = array.array("h")
    ph = 0.0
    for i in range(n):
        t = i / n
        f = freq * (1.0 + slide * t)
        ph += f / rate
        if wave == "sq":
            v = 1.0 if (ph % 1.0) < 0.5 else -1.0
        elif wave == "tri":
            v = 4.0 * abs((ph % 1.0) - 0.5) - 1.0
        else:
            v = math.sin(ph * 6.283185)
        env = 1.0 - t
        sample = int(max(-1.0, min(1.0, v * vol * env)) * 32767)
        buf.append(sample)
        buf.append(sample)
    return buf


def _mix(into, buf, at):
    end = min(len(into), at + len(buf))
    for i in range(at, end):
        into[i] = max(-32767, min(32767, into[i] + buf[i - at]))


def prepare_audio():
    if os.environ.get("KULTAKIRI_NO_SFX"):
        return
    try:
        pygame.mixer.pre_init(22050, -16, 2, 512)
    except Exception:
        pass


def start_audio():
    global _READY
    if os.environ.get("KULTAKIRI_NO_SFX"):
        return
    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init(22050, -16, 2, 512)
        _SFX["jump"] = pygame.mixer.Sound(buffer=_tone(520, 0.09, 0.18, "sq", 0.6).tobytes())
        _SFX["coin"] = pygame.mixer.Sound(buffer=_tone(880, 0.08, 0.2, "sq", 0.4).tobytes())
        _SFX["power"] = pygame.mixer.Sound(buffer=_tone(660, 0.16, 0.2, "tri", 0.5).tobytes())
        _SFX["hit"] = pygame.mixer.Sound(buffer=_tone(180, 0.12, 0.22, "sq", -0.4).tobytes())
        _SFX["ghost"] = pygame.mixer.Sound(buffer=_tone(360, 0.22, 0.16, "sine", 0.8).tobytes())
        _SFX["revive"] = pygame.mixer.Sound(buffer=_tone(480, 0.14, 0.2, "tri", 0.7).tobytes())
        _SFX["out"] = pygame.mixer.Sound(buffer=_tone(140, 0.2, 0.2, "sine", -0.5).tobytes())
        _SFX["go"] = pygame.mixer.Sound(buffer=_tone(440, 0.12, 0.2, "sq", 0.2).tobytes())
        _SFX["win"] = pygame.mixer.Sound(buffer=_tone(523, 0.28, 0.2, "tri", 0.15).tobytes())
        if not os.environ.get("KULTAKIRI_NO_MUSIC"):
            pygame.mixer.Sound(buffer=_music().tobytes()).play(loops=-1)
        _READY = True
    except Exception:
        _READY = False


def _music():
    rate = 22050
    seconds = 4
    n = rate * seconds
    buf = array.array("h", [0]) * (n * 2)
    scale = (60, 62, 64, 67, 69, 72, 74, 76)
    step = int(rate * 0.28)

    def midi(m):
        return 440.0 * (2.0 ** ((m - 69) / 12.0))

    for i, m in enumerate((60, 64, 67, 64, 69, 67, 64, 62) * 2):
        tone = _tone(midi(m), 0.26, 0.06, "tri", 0.0)
        _mix(buf, tone, i * step * 2)
    bass_step = step * 2
    for i, m in enumerate((48, 48, 43, 48) * 4):
        tone = _tone(midi(m), 0.34, 0.05, "sine", 0.0)
        _mix(buf, tone, i * bass_step * 2)
    return buf


def sfx(name):
    if not _READY or os.environ.get("KULTAKIRI_AUTOPLAY"):
        return
    sound = _SFX.get(name)
    if sound is not None:
        try:
            sound.play()
        except Exception:
            pass
