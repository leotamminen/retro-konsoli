"""One headless session: real frames in, mp4 and a report out."""
import json
import time
import traceback
from pathlib import Path

from highlights import Event, choose_highlights
from record import Recorder, cut_clip


def run_session(adapter, players, rounds, seed, out_dir, max_seconds=0):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    adapter.start(players, seed, rounds)
    video = out_dir / "full.mp4"
    recorder = Recorder(video, adapter.width, adapter.height, fps=adapter.video_fps)
    events = []
    frame = 0
    frame_times = []
    last_spike = -9999
    max_frames = adapter.sim_fps * 60 * 4
    crashed = None
    try:
        while frame < max_frames and not adapter.finished():
            if max_seconds and frame >= adapter.sim_fps * max_seconds:
                break
            adapter.write_inputs()
            t0 = time.perf_counter()
            try:
                adapter.tick()
                adapter.draw()
            except Exception:
                crashed = traceback.format_exc()
                events.append(Event(
                    frame / float(adapter.sim_fps), frame, "anomaly",
                    "Game raised an exception:\n%s" % crashed, 100, True,
                ))
                break
            dt = time.perf_counter() - t0
            frame_times.append(dt)
            if frame > adapter.sim_fps and len(frame_times) >= 30:
                sample = sorted(frame_times[-120:])
                median = sample[len(sample) // 2]
                if dt > 0.050 and dt > median * 8 and frame - last_spike > adapter.sim_fps * 2:
                    last_spike = frame
                    events.append(Event(
                        frame / float(adapter.sim_fps), frame, "anomaly",
                        "Frame took %.0f ms (recent median %.1f ms)" % (dt * 1000, median * 1000),
                        90, True,
                    ))
            events.extend(adapter.collect(frame))
            if frame % (adapter.sim_fps // adapter.video_fps) == 0:
                recorder.write(adapter.surface())
            frame += 1
            if frame % (adapter.sim_fps * 15) == 0:
                print("  %.0fs  state=%s" % (frame / adapter.sim_fps, adapter.game.state), flush=True)
        if frame >= max_frames and not adapter.finished():
            events.append(Event(
                frame / float(adapter.sim_fps), frame, "anomaly",
                "Stopped after 4 minutes because the round never finished",
                100, True,
            ))
    finally:
        recorder.close()
        adapter.close()

    video_len = recorder.frames / float(adapter.video_fps) if recorder.frames else 0.0
    clips = choose_highlights(events, video_len, limit=5)
    clip_dir = out_dir / "clips"
    written = []
    for i, clip in enumerate(clips, 1):
        slug = "%02d-%s" % (i, clip.title.replace(" ", "-"))
        dest = clip_dir / ("%s.mp4" % slug)
        cut_clip(video, dest, clip.start, clip.duration)
        written.append((clip, dest))

    log_path = out_dir / "events.jsonl"
    with log_path.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps({
                "t": round(event.t, 3),
                "frame": event.frame,
                "kind": event.kind,
                "summary": event.summary,
                "anomaly": event.anomaly,
            }, ensure_ascii=False) + "\n")

    report = out_dir / "report.md"
    report.write_text(_report(adapter, players, rounds, seed, video, video_len, events, written, crashed), encoding="utf-8")
    print("wrote %s (%d frames, %.1fs)" % (video, recorder.frames, video_len))
    print("wrote %s" % report)
    return {
        "video": video,
        "report": report,
        "clips": written,
        "events": events,
        "seconds": video_len,
        "crashed": crashed,
    }


def _report(adapter, players, rounds, seed, video, video_len, events, clips, crashed):
    counts = {}
    for event in events:
        counts[event.kind] = counts.get(event.kind, 0) + 1
    anomalies = [e for e in events if e.anomaly or e.kind == "anomaly"]
    lines = [
        "# %s playtest" % adapter.name,
        "",
        "- Players: %d" % players,
        "- Rounds requested: %d" % rounds,
        "- Seed: %d" % seed,
        "- Video: `%s` (%.1f s, %d fps scaled to 960x540)" % (video.name, video_len, adapter.video_fps),
        "",
        "## What the run did",
        "",
    ]
    for kind in ("fall", "return", "out", "pickup", "effect", "bump", "round_end", "ghost", "anomaly"):
        if counts.get(kind):
            lines.append("- %s: %d" % (kind, counts[kind]))
    if not counts:
        lines.append("- No gameplay events were recorded.")
    lines.extend(["", "## Anomalies", ""])
    if anomalies:
        for event in anomalies:
            lines.append("- %.1fs — %s" % (event.t, event.summary.splitlines()[0]))
    else:
        lines.append("None. No crash, no non-finite position, no one stuck while holding right, no frame over 50 ms.")
    if crashed:
        lines.extend(["", "### Traceback", "", "```", crashed.rstrip(), "```"])
    lines.extend(["", "## Highlight clips", ""])
    if not clips:
        lines.append("No clip was cut (the video was too short, or nothing happened).")
    for clip, path in clips:
        lines.append("### `%s`" % path.name)
        lines.append("")
        lines.append("- Time: %.1fs–%.1fs" % (clip.start, clip.end))
        lines.append("- Why this clip: %s" % clip.summary)
        extra = [e for e in clip.events if e.summary != clip.summary]
        if extra:
            lines.append("- Also in this window:")
            for event in extra:
                if event.kind == "bump":
                    continue
                lines.append("  - %.1fs %s" % (event.t, event.summary))
        lines.append("")
    lines.extend(["## Notable moments", ""])
    shown = 0
    for event in events:
        if event.kind == "bump":
            continue
        lines.append("- %.1fs %s — %s" % (event.t, event.kind, event.summary.splitlines()[0]))
        shown += 1
        if shown >= 40:
            lines.append("- … further moments are in `events.jsonl`.")
            break
    if shown == 0:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)
