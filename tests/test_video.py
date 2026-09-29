"""Regression on real footage through the exact live pipeline (skipped without ffmpeg).

Ground truth was counted by hand; see tests/fixtures/CREDITS.md.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PUNARGATI_DATA", tempfile.mkdtemp(prefix="pg-test-"))
os.environ.setdefault("PUNARGATI_LLM_URL", "http://127.0.0.1:9/v1")

from punargati import offline  # noqa: E402

HAVE_FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class RealVideo(unittest.TestCase):
    def test_squat_demo_clip_two_reps(self):
        res = offline.run(str(ROOT / "web/demo/squat.webm"), "exercise", "squat")
        s = res["record"]["summary"]
        self.assertEqual(s["reps"], 2)
        self.assertGreater(s["by_side"]["both"]["best_rom"], 100)  # a deep squat

    def test_cdc_chair_stand_front_view_three_stands(self):
        clip = str(ROOT / "tests/fixtures/cdc_chair_stand_front.webm")
        res = offline.run(clip, "exercise", "sit_to_stand")
        self.assertEqual(res["record"]["summary"]["reps"], 3)
        res = offline.run(clip, "assessment", "chair_stand_30s")
        self.assertEqual(res["record"]["status"]["stands"], 3)


if __name__ == "__main__":
    unittest.main()
