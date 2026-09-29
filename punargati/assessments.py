"""Standardised clinical screening tests, timed and scored on-device.

* 30-Second Chair Stand  (CDC STEADI fall-risk toolkit; Jones et al. 1999)
* Single-Leg Stance      (Springer et al. 2007 norms; <5 s flags fall risk, Vellas et al. 1997)
* Active range of motion (shoulder flexion / abduction, knee flexion) vs AAOS reference values

These are *screening aids* that reproduce what a physiotherapist does with a
stopwatch and goniometer. They do not diagnose.
"""

from __future__ import annotations

import math

from .exercises import RiseMetric
from .kinematics import Frame

# CDC STEADI: a score *below* these values indicates a risk for falls.
CHAIR_STAND_BELOW_AVG = [  # (age_lo, age_hi, men, women)
    (60, 64, 14, 12), (65, 69, 12, 11), (70, 74, 12, 10), (75, 79, 11, 10),
    (80, 84, 10, 9), (85, 89, 8, 8), (90, 120, 7, 4),
]

# Springer et al. 2007, eyes open, mean seconds (approx., sexes pooled).
SLS_NORMS = [(18, 39, 43.0), (40, 49, 40.0), (50, 59, 37.0), (60, 69, 27.0), (70, 79, 15.0), (80, 120, 6.0)]

# American Academy of Orthopaedic Surgeons reference active ROM (degrees).
AAOS_ROM = {"shoulder_flexion": 180, "shoulder_abduction": 180, "knee_flexion": 135}


def chair_stand_norm(age: int | None, sex: str | None) -> dict:
    if not age or age < 60:
        return {"threshold": None, "note": "CDC norms cover ages 60+; track your own trend instead."}
    for lo, hi, m, w in CHAIR_STAND_BELOW_AVG:
        if lo <= age <= hi:
            thr = m if (sex or "").lower().startswith("m") else w
            return {"threshold": thr, "note": f"Below {thr} stands indicates fall risk for this age/sex (CDC STEADI)."}
    return {"threshold": None, "note": ""}


def sls_norm(age: int | None) -> float | None:
    if not age:
        return None
    for lo, hi, s in SLS_NORMS:
        if lo <= age <= hi:
            return s
    return None


TESTS = {
    "chair_stand_30s": {
        "name": "30-second chair stand", "duration": 30, "view": "side",
        "steps": ["Sit in the middle of a firm chair, side-on to the laptop",
                  "Cross your arms over your chest, feet flat",
                  "When the timer starts, stand up fully and sit down, as many times as you can in 30 s"],
        "measures": "Leg strength & endurance; CDC fall-risk screen for adults 60+",
    },
    "single_leg_stance": {
        "name": "Single-leg balance", "duration": 45, "view": "front",
        "steps": ["Stand facing the laptop near a wall or chair for safety",
                  "Cross your arms. Lift one foot off the floor",
                  "The timer runs until the foot touches down (max 45 s)"],
        "measures": "Static balance; under 5 s is associated with fall risk",
    },
    "rom_shoulder_flexion": {
        "name": "Shoulder flexion range", "duration": 15, "view": "side", "joint": "shoulder",
        "norm_key": "shoulder_flexion",
        "steps": ["Stand side-on to the laptop", "Raise both arms forward and up as high as you can",
                  "Hold at the top for a second; repeat 3 times"],
        "measures": "Active shoulder flexion vs 180° reference",
    },
    "rom_shoulder_abduction": {
        "name": "Shoulder abduction range", "duration": 15, "view": "front", "joint": "shoulder",
        "norm_key": "shoulder_abduction",
        "steps": ["Face the laptop", "Raise both arms out to the sides and up as high as you can",
                  "Hold at the top for a second; repeat 3 times"],
        "measures": "Active shoulder abduction vs 180° reference",
    },
    "rom_knee_flexion": {
        "name": "Knee bend range", "duration": 15, "view": "side", "joint": "knee_flex",
        "norm_key": "knee_flexion",
        "steps": ["Stand side-on holding a chair", "Bend one knee, bringing the heel towards your buttock",
                  "Hold for a second; repeat 3 times on each leg"],
        "measures": "Active knee flexion vs 135° reference (post knee-replacement goal is typically 110°+)",
    },
}


class Assessment:
    """Server-side timeline: ready -> countdown -> running -> done."""

    COUNTDOWN = 3.0

    def __init__(self, test_id: str, profile: dict):
        self.id = test_id
        self.spec = TESTS[test_id]
        self.profile = profile or {}
        self.state = "ready"
        self.t0 = None
        self.t_run = None
        self.result: dict | None = None
        # chair stand
        self.stands = 0
        self.seated = True  # protocol starts seated; if not, the first sit just calibrates
        self.rise = RiseMetric()
        # single-leg stance
        self.lift_t = None
        self.down_frames = 0
        # rom
        self.best = {"l": 0.0, "r": 0.0}
        self.buf = {"l": [], "r": []}

    def _age(self):
        try:
            return int(self.profile.get("age") or 0) or None
        except (TypeError, ValueError):
            return None

    def update(self, f: Frame) -> list[dict]:
        ev: list[dict] = []
        if self.state == "done":
            return ev
        if self.state == "ready":
            if self._ready_pose(f):
                self.state, self.t0 = "countdown", f.t
                ev.append({"type": "cue", "cue": "test_countdown"})
            return ev
        if self.state == "countdown":
            if self.id == "chair_stand_30s":
                self.rise(f, "b")  # learn the seated height during the countdown
            if f.t - self.t0 >= self.COUNTDOWN:
                self.state, self.t_run = "running", f.t
                ev.append({"type": "cue", "cue": "test_start"})
            return ev
        elapsed = f.t - self.t_run
        if self.id == "chair_stand_30s":
            ev += self._chair(f)
        elif self.id == "single_leg_stance":
            ev += self._sls(f)
        else:
            self._rom(f)
        if self.state == "running" and elapsed >= self.spec["duration"]:
            ev += self._finish(f)
        return ev

    def _ready_pose(self, f: Frame) -> bool:
        if self.id == "chair_stand_30s":
            return not math.isnan(f.get("stand_height_px"))
        return f.body_px > 0 and not math.isnan(f.get("trunk_lean"))

    def _chair(self, f: Frame) -> list[dict]:
        # View-independent: self-calibrating shoulder height (see exercises.RiseMetric).
        # A stand counts when the rise passes 80% of the seated->standing range, and
        # the next one only after dropping back below 35% (hysteresis).
        rise = self.rise(f, "b")
        if math.isnan(rise):
            return []
        if rise < 35:
            self.seated = True
        elif self.seated and rise > 80:
            self.seated = False
            self.stands += 1
            return [{"type": "count", "count": self.stands}]
        return []

    def _sls(self, f: Frame) -> list[dict]:
        dy = f.get("ankle_dy_l")
        if math.isnan(dy):
            return []
        lifted = abs(dy) > 0.06
        if self.lift_t is None:
            if lifted:
                self.lift_t = f.t
                self.lift_side = "left" if dy > 0 else "right"
                return [{"type": "cue", "cue": "timer_running"}]
            # the 45 s budget only starts once a foot is up
            self.t_run = f.t
            return []
        if abs(dy) < 0.03:
            self.down_frames += 1
            if self.down_frames >= 5:
                return self._finish(f)
        else:
            self.down_frames = 0
        return []

    def _rom(self, f: Frame) -> None:
        joint = self.spec["joint"]
        for s in ("l", "r"):
            v = f.get(f"{joint}_{s}")
            if math.isnan(v):
                continue
            b = self.buf[s]
            b.append(v)
            if len(b) > 5:
                b.pop(0)
            if len(b) == 5:  # median of 5 rejects single-frame keypoint glitches
                self.best[s] = max(self.best[s], sorted(b)[2])

    def _finish(self, f: Frame) -> list[dict]:
        self.state = "done"
        age, sex = self._age(), self.profile.get("sex")
        if self.id == "chair_stand_30s":
            norm = chair_stand_norm(age, sex)
            thr = norm["threshold"]
            flag = None if thr is None else ("below_average" if self.stands < thr else "ok")
            self.result = {"score": self.stands, "unit": "stands", "threshold": thr,
                           "flag": flag, "note": norm["note"]}
        elif self.id == "single_leg_stance":
            secs = 0.0 if self.lift_t is None else round(f.t - self.lift_t, 1)
            ref = sls_norm(age)
            flag = "fall_risk" if secs < 5 else ("below_average" if ref and secs < ref * 0.75 else "ok")
            self.result = {"score": secs, "unit": "seconds", "reference": ref, "flag": flag,
                           "side": getattr(self, "lift_side", None),
                           "note": "Under 5 s is associated with injurious falls (Vellas 1997)."}
        else:
            ref = AAOS_ROM[self.spec["norm_key"]]
            by = {("left" if s == "l" else "right"): round(v, 1) for s, v in self.best.items() if v > 0}
            best = max(by.values()) if by else 0.0
            self.result = {"score": best, "unit": "degrees", "by_side": by, "reference": ref,
                           "percent_of_reference": round(100 * best / ref) if ref else None,
                           "flag": "limited" if best < 0.8 * ref else "ok",
                           "note": f"Reference active range {ref}° (AAOS)."}
        return [{"type": "cue", "cue": "test_end"}, {"type": "result", "result": self.result}]

    def status(self, t: float) -> dict:
        d = {"id": self.id, "name": self.spec["name"], "state": self.state, "result": self.result}
        if self.state == "countdown":
            d["countdown"] = max(0.0, round(self.COUNTDOWN - (t - self.t0), 1))
        if self.state == "running":
            if self.id == "single_leg_stance":
                d["elapsed"] = 0.0 if self.lift_t is None else round(t - self.lift_t, 1)
                d["remaining"] = round(max(0.0, self.spec["duration"] - (t - self.t_run)), 1)
            else:
                d["remaining"] = round(max(0.0, self.spec["duration"] - (t - self.t_run)), 1)
            d["stands"] = self.stands
            d["best"] = {k: round(v, 1) for k, v in self.best.items()}
        return d
