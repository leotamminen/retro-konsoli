"""Window math for highlight clips. No pygame, no game."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from highlights import Event, choose_highlights, window


class HighlightTests(unittest.TestCase):
    def test_window_stays_inside_the_video_and_between_5_and_10_seconds(self):
        start, end = window(1.0, 80.0)
        self.assertGreaterEqual(start, 0.0)
        self.assertLessEqual(end, 80.0)
        self.assertGreaterEqual(end - start, 5.0)
        self.assertLessEqual(end - start, 10.0)
        start, end = window(78.0, 80.0)
        self.assertAlmostEqual(end, 80.0)
        self.assertGreaterEqual(end - start, 5.0)
        self.assertLessEqual(end - start, 10.0)

    def test_anomalies_win_and_clips_do_not_overlap(self):
        events = [
            Event(10, 600, "bump", "bump", 28),
            Event(12, 720, "pickup", "picked up speed", 52),
            Event(30, 1800, "anomaly", "stuck", 100, True),
            Event(31, 1860, "fall", "fell", 72),
            Event(50, 3000, "round_end", "ended", 70),
        ]
        clips = choose_highlights(events, 60.0, limit=5)
        self.assertTrue(any(c.title == "anomaly" for c in clips))
        for i, clip in enumerate(clips):
            self.assertGreaterEqual(clip.duration, 5.0)
            self.assertLessEqual(clip.duration, 10.0)
            for other in clips[i + 1:]:
                self.assertFalse(clip.start < other.end and other.start < clip.end)


if __name__ == "__main__":
    unittest.main()
