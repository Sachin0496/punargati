"""Unit tests for kinematics, rep counting, clinical tests and plan parsing.

Run:  python -m unittest discover -s tests -v
Synthetic keypoint sequences make these deterministic and model-free.
"""

import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("PUNARGATI_DATA", tempfile.mkdtemp(prefix="pg-test-"))
os.environ.setdefault("PUNARGATI_LLM_URL", "http://127.0.0.1:9/v1")  # guaranteed-closed port: tests never need an LLM

from punargati import kinematics as K  # noqa: E402
from punargati.assessments import Assessment, chair_stand_norm, sls_norm  # noqa: E402
from punargati.exercises import LIBRARY, RepCounter  # noqa: E402
from punargati.plan import parse_rules  # noqa: E402
from punargati.pose import KP, init_crop, next_crop, render_crop  # noqa: E402


def skeleton(knee_flex=0.0, shoulder=0.0, elbow_flex=0.0, side_view=True, lift_left_ankle=0.0,
             trunk_lean=0.0, score=0.9):
    """Build a plausible 17-keypoint pose (pixels) with the requested joint angles."""
    k = np.zeros((17, 3), np.float32)
    k[:, 2] = score
    hip = np.array([640.0, 400.0])
    torso = 220.0
    lean = math.radians(trunk_lean)
    sh = hip + torso * np.array([math.sin(lean), -math.cos(lean)])
    half = 8.0 if side_view else 70.0
    thigh, shin, upper, fore = 200.0, 190.0, 150.0, 130.0
    for s, sign in (("left", -1), ("right", 1)):
        h = hip + np.array([sign * half * 0.8, 0])
        k[KP[f"{s}_hip"], :2] = h
        # thigh straight down; shin bent forward by knee_flex
        knee = h + np.array([0, thigh])
        a = math.radians(knee_flex)
        ankle = knee + shin * np.array([-math.sin(a), math.cos(a)])
        k[KP[f"{s}_knee"], :2] = knee
        k[KP[f"{s}_ankle"], :2] = ankle
        shp = sh + np.array([sign * half, 0])
        k[KP[f"{s}_shoulder"], :2] = shp
        b = math.radians(shoulder)
        elb = shp + upper * np.array([math.sin(b), math.cos(b)])
        c = math.radians(shoulder + elbow_flex)
        wr = elb + fore * np.array([math.sin(c), math.cos(c)])
        k[KP[f"{s}_elbow"], :2] = elb
        k[KP[f"{s}_wrist"], :2] = wr
    if lift_left_ankle:
        k[KP["left_ankle"], 1] -= lift_left_ankle
    k[KP["nose"], :2] = sh + np.array([0, -60])
    return k


class Kinematics(unittest.TestCase):
    def test_angle_basic(self):
        self.assertAlmostEqual(K.angle((0, 1), (0, 0), (1, 0)), 90.0, places=4)
        self.assertAlmostEqual(K.angle((0, 1), (0, 0), (0, -1)), 180.0, places=4)
        self.assertTrue(math.isnan(K.angle((0, 0), (0, 0), (1, 0))))

    def test_knee_and_shoulder_recovered(self):
        for kf in (0, 30, 60, 90):
            f = K.compute(skeleton(knee_flex=kf), 0.0)
            self.assertAlmostEqual(f.get("knee_flex_l"), kf, delta=0.5)
        for sa in (10, 90, 170):
            f = K.compute(skeleton(shoulder=sa), 0.0)
            self.assertAlmostEqual(f.get("shoulder_r"), sa, delta=0.5)

    def test_elbow_and_trunk(self):
        f = K.compute(skeleton(elbow_flex=100, trunk_lean=20), 0.0)
        self.assertAlmostEqual(f.get("elbow_flex_l"), 100, delta=0.5)
        self.assertAlmostEqual(f.get("trunk_lean"), 20, delta=1.0)

    def test_low_confidence_is_nan(self):
        f = K.compute(skeleton(score=0.1), 0.0)
        self.assertTrue(math.isnan(f.get("knee_flex_l")))

    def test_foot_pitch_from_wholebody_feet(self):
        k = np.zeros((23, 3), np.float32)
        k[:17] = skeleton()
        for heel, toe, ankle in ((19, 17, 15), (22, 20, 16)):
            k[heel] = [k[ankle, 0] - 10, k[ankle, 1] + 10, 0.9]
            k[toe] = [k[ankle, 0] + 60, k[ankle, 1] + 10, 0.9]
        self.assertAlmostEqual(K.compute(k, 0).get("foot_pitch_l"), 0.0, delta=0.5)
        k[19, 1] -= 35  # heel lifted
        self.assertAlmostEqual(K.compute(k, 0).get("foot_pitch_l"), math.degrees(math.atan2(35, 70)), delta=0.5)
        self.assertTrue(math.isnan(K.compute(skeleton(), 0).get("foot_pitch_l")))  # no feet without precision

    def test_view_detection(self):
        self.assertEqual(K.compute(skeleton(side_view=True), 0).view, "side")
        self.assertEqual(K.compute(skeleton(side_view=False), 0).view, "front")

    def test_one_euro_smooths_jitter(self):
        f = K.OneEuro()
        rng = np.random.default_rng(0)
        out = [f(np.array([0.5 + rng.normal(0, 0.01)]), i / 30)[0] for i in range(120)]
        self.assertLess(np.std(out[30:]), 0.006)


def run(ex_id, angles, key="knee_flex", fps=30, **kw):
    rc = RepCounter(LIBRARY[ex_id], kw.pop("side", "auto"))
    events = []
    for i, a in enumerate(angles):
        f = K.compute(skeleton(**{key: a}, **kw), i / fps)
        events += rc.update(f)
    return rc, events


def wave(lo, hi, reps, secs_per_rep=2.0, fps=30, hold=0.5):
    out = [lo] * int(hold * fps)
    n = int(secs_per_rep * fps)
    for _ in range(reps):
        out += [lo + (hi - lo) * (1 - math.cos(2 * math.pi * i / n)) / 2 for i in range(n)]
        out += [lo] * int(hold * fps)
    return out


class Reps(unittest.TestCase):
    def test_squat_counts_and_rom(self):
        rc, ev = run("squat", wave(5, 90, 5))
        self.assertEqual(len(rc.reps), 5)
        self.assertAlmostEqual(rc.reps[0].peak, 90, delta=1.5)
        self.assertTrue(all(r.quality == 100 for r in rc.reps))

    def test_jitter_below_threshold_not_counted(self):
        noise = [10 + 12 * math.sin(i) for i in range(300)]  # never crosses 'enter'
        rc, _ = run("squat", noise)
        self.assertEqual(len(rc.reps), 0)

    def test_too_fast_rep_rejected(self):
        rc, _ = run("squat", wave(5, 80, 3, secs_per_rep=0.3))
        self.assertEqual(len(rc.reps), 0)

    def test_partial_rep_gets_cue_and_lower_quality(self):
        rc, ev = run("squat", wave(5, 50, 2))
        self.assertEqual(len(rc.reps), 2)
        self.assertLess(rc.reps[0].quality, 70)
        self.assertIn("go_further", [e.get("cue") for e in ev])

    def test_shoulder_each_side_and_form_fault(self):
        rc, ev = run("shoulder_flexion", wave(10, 160, 3), key="shoulder", elbow_flex=60)
        c = rc.counts()
        self.assertEqual(c["l"], 3)
        self.assertEqual(c["r"], 3)
        self.assertIn("straight_elbow", [e.get("cue") for e in ev])
        self.assertTrue(all("straight_elbow" in r.faults for r in rc.reps))

    def test_knee_extension_reports_extension_deficit(self):
        # seated: knee_flex 90 at rest -> 5 at full extension
        rc, _ = run("knee_extension", wave(90, 5, 2), side="left")
        self.assertEqual(len(rc.reps), 2)
        self.assertAlmostEqual(rc.reps[0].rom, 5, delta=1.5)

    def test_summary_shape(self):
        rc, _ = run("squat", wave(5, 90, 2))
        s = rc.summary()
        self.assertEqual(s["reps"], 2)
        self.assertIn("both", s["by_side"])


class Tests(unittest.TestCase):
    def test_norms(self):
        self.assertEqual(chair_stand_norm(72, "female")["threshold"], 10)
        self.assertEqual(chair_stand_norm(66, "male")["threshold"], 12)
        self.assertIsNone(chair_stand_norm(40, "male")["threshold"])
        self.assertEqual(sls_norm(65), 27.0)

    def test_chair_stand_flow(self):
        a = Assessment("chair_stand_30s", {"age": 70, "sex": "female"})
        t = 0.0
        # seated to trigger the countdown, then 12 stand/sit cycles of 2 s in 30 s
        seq = [85] * 150 + wave(85, 0, 16, secs_per_rep=2.0, hold=0.2)
        for kf in seq:
            f = K.compute(skeleton(knee_flex=kf), t)
            a.update(f)
            t += 1 / 30
        self.assertEqual(a.state, "done")
        self.assertGreaterEqual(a.result["score"], 12)
        self.assertEqual(a.result["flag"], "ok")

    def test_single_leg_stance(self):
        a = Assessment("single_leg_stance", {"age": 68})
        t = 0.0
        frames = [0.0] * 150 + [60.0] * (30 * 8) + [0.0] * 20
        for lift in frames:
            a.update(K.compute(skeleton(lift_left_ankle=lift), t))
            t += 1 / 30
        self.assertEqual(a.state, "done")
        self.assertAlmostEqual(a.result["score"], 8.0, delta=0.5)
        self.assertEqual(a.result["flag"], "below_average")

    def test_rom_test_uses_median_filter(self):
        a = Assessment("rom_shoulder_flexion", {})
        t = 0.0
        seq = [20.0] * 150 + wave(20, 150, 3) + [20.0] * 400
        for i, v in enumerate(seq):
            k = skeleton(shoulder=v)
            if i == 400:
                k = skeleton(shoulder=179)  # single-frame glitch must not become the ROM
            a.update(K.compute(k, t))
            t += 1 / 30
        self.assertEqual(a.state, "done")
        self.assertAlmostEqual(a.result["score"], 150, delta=2)


class Crop(unittest.TestCase):
    def test_init_and_tracking(self):
        c = init_crop(1280, 720)
        self.assertEqual((c.x, c.size), (0, 1280))
        k = skeleton()
        k[:, 0] = k[:, 0] * 0.3 + 300  # a small person on the left of the frame
        k[:, 1] = k[:, 1] * 0.3 + 200
        n = next_crop(k, 1280, 720)
        self.assertLess(n.size, 600)
        self.assertLess(n.x, 400)

    def test_render_crop_pads_outside(self):
        fr = np.full((100, 200, 3), 200, np.uint8)
        out = render_crop(fr, init_crop(200, 100))
        self.assertEqual(out.shape, (192, 192, 3))
        self.assertEqual(int(out[0, 96, 0]), 0)       # letterbox padding
        self.assertEqual(int(out[96, 96, 0]), 200)    # image content


class Plan(unittest.TestCase):
    def test_common_phrasings(self):
        items = parse_rules(
            "Mini squats 3 x 10, twice a day\n"
            "Seated knee extension right leg 2 sets of 15\n"
            "Shoulder forward raise left 10 reps daily\n"
            "Arm lifts sideways L shoulder 12 times\n"
            "30 second chair stand test weekly\n"
            "Ice after exercise")
        got = [(i["id"], i["sets"], i["reps"], i["side"], i["frequency"]) for i in items]
        self.assertEqual(got, [
            ("squat", 3, 10, "auto", "2x daily"),
            ("knee_extension", 2, 15, "right", "daily"),
            ("shoulder_flexion", 1, 10, "left", "daily"),
            ("shoulder_abduction", 1, 12, "left", "daily"),
            ("chair_stand_30s", 1, None, "auto", "weekly"),
        ])


if __name__ == "__main__":
    unittest.main()
