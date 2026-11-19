# Short synthesized blips. Music is built once, never inside the frame.
import array
import math
import os

import pygame

_SFX = {}
_MUSIC = None
_READY = False
_SFX_VOL = 0.8
_MUSIC_VOL = 0.6


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


def _noise(dur, vol=0.12, slide=0.4):
    rate = 22050
    n = max(1, int(rate * dur))
    buf = array.array("h")
    hold = 0
    v = 0.0
    for i in range(n):
        if hold <= 0:
            hold = 40 + (i * 17) % 50
            v = 1.0 if ((i * 13) % 7) < 3 else -1.0
        hold -= 1
        t = i / n
        env = (1.0 - t) * (0.35 + 0.65 * t)
        sample = int(max(-1.0, min(1.0, v * vol * env)) * 32767)
        buf.append(sample)
        buf.append(sample)
    return buf


def _mix(into, buf, at):
    end = min(len(into), at + len(buf))
    for i in range(at, end):
        into[i] = max(-32767, min(32767, into[i] + buf[i - at]))


def prepare_audio():
    if os.environ.get("SAUNAKISA_NO_SFX"):
        return
    try:
        pygame.mixer.pre_init(22050, -16, 2, 512)
    except Exception:
        pass


def start_audio():
    global _READY, _MUSIC
    if os.environ.get("SAUNAKISA_NO_SFX"):
        return
    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init(22050, -16, 2, 512)
        _SFX["loyly"] = pygame.mixer.Sound(buffer=_noise(0.28, 0.16).tobytes())
        _SFX["faint"] = pygame.mixer.Sound(buffer=_tone(160, 0.22, 0.22, "sine", -0.55).tobytes())
        _SFX["dip"] = pygame.mixer.Sound(buffer=_tone(520, 0.1, 0.16, "sine", -0.3).tobytes())
        _SFX["drink"] = pygame.mixer.Sound(buffer=_tone(740, 0.09, 0.16, "tri", 0.35).tobytes())
        _SFX["go"] = pygame.mixer.Sound(buffer=_tone(440, 0.12, 0.18, "sq", 0.25).tobytes())
        _SFX["win"] = pygame.mixer.Sound(buffer=_tone(523, 0.26, 0.18, "tri", 0.12).tobytes())
        _SFX["join"] = pygame.mixer.Sound(buffer=_tone(620, 0.07, 0.14, "sq", 0.2).tobytes())
        if not os.environ.get("SAUNAKISA_NO_MUSIC"):
            _MUSIC = pygame.mixer.Sound(buffer=_music().tobytes())
            _MUSIC.play(loops=-1)
        apply_volume(int(_SFX_VOL * 10), int(_MUSIC_VOL * 10))
        _READY = True
    except Exception:
        _READY = False


def apply_volume(sfx_vol, music_vol):
    global _SFX_VOL, _MUSIC_VOL
    try:
        sfx_vol = int(sfx_vol)
        music_vol = int(music_vol)
    except (TypeError, ValueError):
        return
    _SFX_VOL = max(0, min(10, sfx_vol)) / 10.0
    _MUSIC_VOL = max(0, min(10, music_vol)) / 10.0
    for sound in _SFX.values():
        try:
            sound.set_volume(_SFX_VOL)
        except Exception:
            pass
    if _MUSIC is not None:
        try:
            _MUSIC.set_volume(_MUSIC_VOL)
        except Exception:
            pass


def _music():
    rate = 22050
    seconds = 8
    n = rate * seconds
    buf = array.array("h", [0]) * (n * 2)

    def midi(m):
        return 440.0 * (2.0 ** ((m - 69) / 12.0))

    step = int(rate * 0.5)
    melody = (67, 65, 62, 60, 62, 65, 67, 62, 60, 58, 60, 62, 65, 62, 60, 67)
    for i, m in enumerate(melody):
        tone = _tone(midi(m), 0.42, 0.045, "sine", 0.0)
        _mix(buf, tone, i * step * 2)
    for i, m in enumerate((48, 48, 46, 43, 41, 43, 46, 48)):
        tone = _tone(midi(m), 0.7, 0.04, "tri", 0.0)
        _mix(buf, tone, i * step * 4)
    return buf


def sfx(name):
    if not _READY or os.environ.get("SAUNAKISA_AUTOPLAY") or _SFX_VOL <= 0:
        return
    sound = _SFX.get(name)
    if sound is not None:
        try:
            sound.play()
        except Exception:
            pass
