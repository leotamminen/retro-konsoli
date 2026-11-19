"""Pipe RGB frames to ffmpeg. The game stays at native pixels; ffmpeg scales."""
import subprocess
from pathlib import Path

import pygame


class Recorder:
    def __init__(self, path, width, height, fps=30, out_w=960, out_h=540):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.width = width
        self.height = height
        self.frames = 0
        self.log_path = self.path.with_suffix(".ffmpeg.log")
        self._log = open(self.log_path, "w", encoding="utf-8")
        scale = "scale=%d:%d:flags=neighbor" % (out_w, out_h)
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", "%dx%d" % (width, height),
            "-r", str(fps),
            "-i", "pipe:0",
            "-vf", scale,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "23", "-preset", "veryfast",
            "-movflags", "+faststart",
            "-an", str(self.path),
        ]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self._log)

    def write(self, surface):
        if surface.get_width() != self.width or surface.get_height() != self.height:
            raise RuntimeError("frame is %s, recorder expects %dx%d" % (surface.get_size(), self.width, self.height))
        try:
            self.proc.stdin.write(pygame.image.tobytes(surface, "RGB"))
        except BrokenPipeError:
            self._fail()
        self.frames += 1

    def close(self):
        if self.frames == 0 and self.proc.stdin and not self.proc.stdin.closed:
            self.proc.stdin.write(b"\x00" * (self.width * self.height * 3))
            self.frames = 1
        if self.proc.stdin and not self.proc.stdin.closed:
            try:
                self.proc.stdin.close()
            except BrokenPipeError:
                pass
        code = self.proc.wait()
        self._log.close()
        if code != 0:
            self._fail()
        return self.frames

    def _fail(self):
        text = self.log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
        raise RuntimeError("ffmpeg failed for %s\n%s" % (self.path, text))


def cut_clip(source, dest, start, duration):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(source),
        "-ss", "%.2f" % start,
        "-t", "%.2f" % duration,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "22", "-preset", "veryfast",
        "-movflags", "+faststart",
        "-an", str(dest),
    ]
    subprocess.run(cmd, check=True)
