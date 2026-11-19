"""Pick short, non-overlapping clips around the events that matter."""
from dataclasses import dataclass, field


@dataclass
class Event:
    t: float
    frame: int
    kind: str
    summary: str
    priority: int = 40
    anomaly: bool = False


@dataclass
class Clip:
    start: float
    end: float
    title: str
    summary: str
    events: list = field(default_factory=list)

    @property
    def duration(self):
        return self.end - self.start


def window(t, video_len, length=5.5, pre=1.0, min_len=5.0, max_len=10.0):
    """A 5–10 s slice with the event a bit after the start."""
    length = min(max_len, max(min_len, length))
    if video_len <= min_len:
        return 0.0, video_len
    start = t - pre
    end = start + length
    if start < 0:
        end -= start
        start = 0.0
    if end > video_len:
        start -= end - video_len
        end = video_len
        start = max(0.0, start)
    if end - start > max_len:
        end = start + max_len
    return round(start, 2), round(end, 2)


def _overlaps(a, b, gap=0.05):
    return a.start < b.end + gap and b.start < a.end + gap


def _tile_short(events, video_len, limit):
    """A round that ends quickly still needs several 5 s looks at the course."""
    clips = []
    start = 3.0
    length = 5.2
    while len(clips) < min(4, limit) and start + 5.0 <= video_len + 0.05:
        end = min(video_len, start + length)
        if end - start < 5.0:
            break
        inside = [e for e in events if start - 0.05 <= e.t <= end and e.kind != "bump"]
        if not inside:
            start += 0.4
            continue
        top = max(inside, key=lambda e: (e.priority, -e.t))
        clips.append(Clip(round(start, 2), round(end, 2), top.kind, top.summary, inside))
        start = end
    return clips


def choose_highlights(events, video_len, limit=5):
    """Highest-priority moments first. Anomalies are kept. Windows do not stack."""
    if video_len <= 36:
        tiled = _tile_short(events, video_len, limit)
        if len(tiled) >= 3:
            return tiled
    ranked = sorted(events, key=lambda e: (-e.priority, e.t))
    chosen = []
    for event in ranked:
        if event.kind == "bump" and any(c.title == "bump" for c in chosen):
            continue
        start, end = window(event.t, video_len)
        if end - start < 4.5:
            continue
        clip = Clip(start, end, event.kind, event.summary, [event])
        if any(_overlaps(clip, other) for other in chosen):
            continue
        inside = [e for e in events if start <= e.t <= end]
        clip.events = sorted(inside, key=lambda e: e.t)
        chosen.append(clip)
        if len(chosen) >= limit:
            break
    # A short round can pack its events into two windows. Fill the gaps so the
    # course pieces between them still get a clip of at least 5 seconds.
    t = 0.0
    while len(chosen) < min(4, limit) and t + 5.0 <= video_len:
        end = min(video_len, t + 5.5)
        if end - t < 5.0:
            break
        clip = Clip(round(t, 2), round(end, 2), "course", "Course section", [])
        if any(_overlaps(clip, other) for other in chosen):
            t += 0.5
            continue
        inside = [e for e in events if t <= e.t <= end and e.kind != "bump"]
        if inside:
            clip.events = inside
            clip.title = inside[0].kind
            clip.summary = inside[0].summary
            chosen.append(clip)
            t = end
        else:
            t += 0.5
    chosen.sort(key=lambda c: c.start)
    return chosen
