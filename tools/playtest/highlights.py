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


def window(t, video_len, length=8.0, pre=2.5, min_len=5.0, max_len=10.0):
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


def _overlaps(a, b, gap=0.4):
    return a.start < b.end + gap and b.start < a.end + gap


def choose_highlights(events, video_len, limit=5):
    """Highest-priority moments first. Anomalies are kept. Windows do not stack."""
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
    chosen.sort(key=lambda c: c.start)
    return chosen
