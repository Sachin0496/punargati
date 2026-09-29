"""Exercise library, rep segmentation and form rules.

Each exercise is a declarative spec: which kinematic signal drives it, its
rest / movement / target thresholds (with hysteresis), required camera view,
and form rules that fire while a rep is in progress. ``RepCounter`` turns a
noisy angle stream into clean repetitions with ROM, tempo and a quality score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

from .kinematics import Frame

nan = float("nan")


def _side(key: str) -> Callable[[Frame, str], float]:
    return lambda f, s: f.get(f"{key}_{s}")


def _mean_sides(key: str) -> Callable[[Frame, str], float]:
    def fn(f: Frame, s: str) -> float:
        vals = [v for v in (f.get(f"{key}_l"), f.get(f"{key}_r")) if not math.isnan(v)]
        return sum(vals) / len(vals) if vals else nan
    return fn


def _ext_from_90(key: str, both: bool) -> Callable[[Frame, str], float]:
    base = _mean_sides(key) if both else _side(key)
    return lambda f, s: 90.0 - base(f, s)


class RiseMetric:
    """Self-calibrating 0-100 "how far up" signal for sit-to-stand, from shoulder height.

    Tracks the seated (min) and standing (max) shoulder heights seen so far, so it
    needs no per-user setup and works from the front or the side. A median of 5
    frames rejects single-frame keypoint glitches before they can move the range.
    """

    MIN_SPAN = 0.22   # standing must be >=22% taller than seated before counting

    def __init__(self):
        self.buf: list[float] = []
        self.lo = self.hi = None

    def __call__(self, f: Frame, s: str) -> float:
        v = f.get("stand_height_px")
        if math.isnan(v):
            return nan
        self.buf.append(v)
        if len(self.buf) > 5:
            self.buf.pop(0)
        v = sorted(self.buf)[len(self.buf) // 2]
        self.lo = v if self.lo is None else min(self.lo, v)
        self.hi = v if self.hi is None else max(self.hi, v)
        span = self.hi - self.lo
        if span < self.MIN_SPAN * self.lo:
            # Range not established yet: express progress against a typical 1.4x rise.
            return max(0.0, min(100.0, 100 * (v - self.lo) / (0.4 * self.lo)))
        return max(0.0, min(100.0, 100 * (v - self.lo) / span))


@dataclass
class Rule:
    """A form check evaluated every frame while a rep is in progress."""

    cue: str
    check: Callable[[Frame, str], bool]
    views: tuple = ("front", "side", "oblique", "unknown")
    frames: int = 4  # must persist this many consecutive frames


@dataclass
class Exercise:
    id: str
    name: str
    region: str
    sides: str                 # 'both' = bilateral movement, 'each' = count each side
    view: str                  # 'side' | 'front' | 'any'
    metric: Callable[[Frame, str], float]
    rest: float                # metric below this => at rest
    enter: float               # metric above this => a movement has started
    target: float              # full-quality peak
    rom_label: str
    rom: Callable[[float], float] = lambda peak: peak
    rules: list = field(default_factory=list)
    min_rep_s: float = 0.6
    ideal_rep_s: float = 2.0
    steps: tuple = ()
    purpose: str = ""
    metric_factory: Callable | None = None  # stateful metric, fresh per session

    def public(self) -> dict:
        return {
            "id": self.id, "name": self.name, "region": self.region, "sides": self.sides,
            "view": self.view, "target": self.target, "rest": self.rest, "enter": self.enter,
            "rom_label": self.rom_label, "steps": list(self.steps), "purpose": self.purpose,
        }


def _gt(key: str, thr: float, sided: bool = False):
    if sided:
        return lambda f, s: f.get(f"{key}_{s}") > thr
    return lambda f, s: f.get(key) > thr


def _lt(key: str, thr: float):
    return lambda f, s: f.get(key) < thr


LIBRARY: dict[str, Exercise] = {e.id: e for e in [
    Exercise(
        id="squat", name="Mini squat", region="knee", sides="both", view="any",
        metric=_mean_sides("knee_flex"), rest=20, enter=40, target=75,
        rom_label="Knee flexion", ideal_rep_s=2.5,
        rules=[
            Rule("chest_up", _gt("trunk_lean", 50), views=("side", "oblique")),
            Rule("knees_out", lambda f, s: f.get("knee_gap_ratio") < 0.7 and _mean_sides("knee_flex")(f, s) > 35,
                 views=("front",)),
        ],
        steps=("Stand with feet hip-width apart, hands forward for balance",
               "Bend knees and push hips back as if sitting on a chair",
               "Go only as low as is comfortable, then stand tall"),
        purpose="Quadriceps and gluteal strength after knee injury or replacement; fall prevention.",
    ),
    Exercise(
        id="sit_to_stand", name="Sit to stand", region="functional", sides="both", view="any",
        metric=lambda f, s: nan, metric_factory=RiseMetric, rest=30, enter=70, target=90,
        rom_label="Rise (% of full stand)", ideal_rep_s=3.0,
        rules=[],
        steps=("Sit on a firm chair, feet flat, arms crossed on chest",
               "Lean slightly forward and stand up fully",
               "Sit back down slowly with control"),
        purpose="Functional leg strength; the movement behind independent daily living.",
    ),
    Exercise(
        id="knee_extension", name="Seated knee extension", region="knee", sides="each", view="side",
        metric=_ext_from_90("knee_flex", both=False), rest=20, enter=45, target=80,
        rom_label="Knee flexion at full extension (0 = straight)", rom=lambda peak: max(0.0, 90.0 - peak),
        rules=[Rule("sit_tall", _gt("trunk_lean", 30))],
        steps=("Sit tall on a chair, side-on to the laptop",
               "Straighten one knee fully, tighten the thigh, hold 2 seconds",
               "Lower slowly. Repeat, then switch legs"),
        purpose="Regain full knee extension after knee replacement, ACL repair or arthritis flare.",
    ),
    Exercise(
        id="shoulder_flexion", name="Shoulder forward raise", region="shoulder", sides="each", view="side",
        metric=_side("shoulder"), rest=30, enter=65, target=150,
        rom_label="Shoulder flexion", ideal_rep_s=2.5,
        rules=[
            Rule("straight_elbow", _gt("elbow_flex", 35, sided=True)),
            Rule("no_lean_back", _gt("trunk_lean", 15)),
        ],
        steps=("Stand side-on to the laptop, arm by your side",
               "Raise the arm forward and up, thumb leading, elbow straight",
               "Lift as high as comfortable, then lower slowly"),
        purpose="Frozen shoulder (common with diabetes), rotator-cuff and post-fracture rehab.",
    ),
    Exercise(
        id="shoulder_abduction", name="Shoulder side raise", region="shoulder", sides="each", view="front",
        metric=_side("shoulder"), rest=30, enter=65, target=150,
        rom_label="Shoulder abduction", ideal_rep_s=2.5,
        rules=[
            Rule("straight_elbow", _gt("elbow_flex", 35, sided=True)),
            Rule("no_shrug", _gt("shoulder_tilt", 12), views=("front",)),
            Rule("stand_tall", _gt("trunk_lean", 12)),
        ],
        steps=("Face the laptop, arms by your sides",
               "Raise one arm out to the side, palm forward, elbow straight",
               "Keep the shoulder relaxed (no shrugging), lower slowly"),
        purpose="Frozen shoulder and impingement rehab; tracks abduction range over weeks.",
    ),
    Exercise(
        id="elbow_curl", name="Elbow bend (curl)", region="elbow", sides="each", view="any",
        metric=_side("elbow_flex"), rest=35, enter=75, target=120,
        rom_label="Elbow flexion",
        rules=[Rule("elbow_close", _gt("shoulder", 40, sided=True))],
        steps=("Stand or sit tall with the upper arm by your side",
               "Bend the elbow bringing the hand to the shoulder",
               "Lower fully. A water bottle works as a light weight"),
        purpose="Elbow stiffness after fracture or immobilisation; general arm strength.",
    ),
    Exercise(
        id="hip_abduction", name="Standing side leg raise", region="hip", sides="each", view="front",
        metric=_side("hip_abd"), rest=8, enter=16, target=28,
        rom_label="Hip abduction",
        rules=[Rule("stand_tall", _gt("trunk_lean", 12))],
        steps=("Face the laptop holding a chair for balance",
               "Lift one leg out to the side, toes pointing forward",
               "Keep your body upright, lower slowly"),
        purpose="Hip stability after hip replacement; reduces fall risk in older adults.",
    ),
    Exercise(
        id="marching", name="Standing march", region="hip", sides="each", view="any",
        metric=_side("hip_flex"), rest=20, enter=45, target=70,
        rom_label="Hip flexion", ideal_rep_s=1.5, min_rep_s=0.4,
        rules=[Rule("stand_tall", _gt("trunk_lean", 15))],
        steps=("Stand tall, holding a chair if needed",
               "Lift one knee towards hip height, then lower",
               "Alternate legs at a steady pace"),
        purpose="Balance, hip-flexor strength and gait retraining.",
    ),
]}

SIDE_NAMES = {"l": "left", "r": "right", "b": "both"}


@dataclass
class Rep:
    side: str
    peak: float
    rom: float
    duration: float
    quality: int
    faults: list
    t_end: float

    def as_dict(self) -> dict:
        return {"side": self.side, "peak": round(self.peak, 1), "rom": round(self.rom, 1),
                "duration": round(self.duration, 2), "quality": self.quality,
                "faults": self.faults, "t": round(self.t_end, 2)}


class _SideMachine:
    def __init__(self):
        self.state = "rest"
        self.peak = nan
        self.t_start = 0.0
        self.t_rest = None
        self.faults: set[str] = set()
        self.streak: dict[str, int] = {}


class RepCounter:
    """Hysteresis state machine per side; emits Rep objects and coaching cues."""

    TIMEOUT_S = 20.0

    def __init__(self, ex: Exercise, side: str = "auto"):
        self.ex = ex
        self.sides = ["b"] if ex.sides == "both" else (["l", "r"] if side in ("auto", "both") else [side[0]])
        self.m = {s: _SideMachine() for s in self.sides}
        self.metric = ex.metric_factory() if ex.metric_factory else ex.metric
        self.reps: list[Rep] = []
        self.value: dict[str, float] = {s: nan for s in self.sides}

    def counts(self) -> dict:
        c = {s: 0 for s in self.sides}
        for r in self.reps:
            c[r.side] = c.get(r.side, 0) + 1
        return c

    def update(self, f: Frame) -> list[dict]:
        events: list[dict] = []
        for s in self.sides:
            v = self.metric(f, s)
            self.value[s] = v
            m = self.m[s]
            if math.isnan(v):
                continue
            if m.state == "rest":
                if v < self.ex.rest:
                    m.t_rest = f.t
                elif v > self.ex.enter:
                    m.state = "moving"
                    m.peak = v
                    m.t_start = m.t_rest if m.t_rest is not None else f.t
                    m.faults, m.streak = set(), {}
                continue
            # moving
            m.peak = max(m.peak, v)
            for rule in self.ex.rules:
                if f.view not in rule.views:
                    continue
                if rule.check(f, s):
                    m.streak[rule.cue] = m.streak.get(rule.cue, 0) + 1
                    if m.streak[rule.cue] == rule.frames:
                        m.faults.add(rule.cue)
                        events.append({"type": "cue", "cue": rule.cue, "side": s})
                else:
                    m.streak[rule.cue] = 0
            if f.t - m.t_start > self.TIMEOUT_S:
                m.state, m.t_rest = "rest", None
                continue
            if v < self.ex.rest:
                m.state = "rest"
                m.t_rest = f.t
                dur = f.t - m.t_start
                if dur < self.ex.min_rep_s:
                    continue
                rep = self._score(s, m, dur, f.t)
                self.reps.append(rep)
                events.append({"type": "rep", "rep": rep.as_dict(), "count": self.counts()})
                if rep.peak < self.ex.target * 0.85 and rep.quality < 80:
                    events.append({"type": "cue", "cue": "go_further", "side": s})
                elif dur < self.ex.ideal_rep_s * 0.45:
                    events.append({"type": "cue", "cue": "slow_down", "side": s})
                elif rep.quality >= 90:
                    events.append({"type": "cue", "cue": "great_rep", "side": s})
        return events

    def _score(self, s: str, m: _SideMachine, dur: float, t: float) -> Rep:
        span = max(1e-6, self.ex.target - self.ex.rest)
        rom_frac = max(0.0, min(1.0, (m.peak - self.ex.rest) / span))
        tempo = 1.0 if dur >= self.ex.ideal_rep_s * 0.45 else 0.85
        q = 100 * rom_frac * tempo * max(0.4, 1 - 0.2 * len(m.faults))
        return Rep(side=s, peak=m.peak, rom=self.ex.rom(m.peak), duration=dur,
                   quality=int(round(q)), faults=sorted(m.faults), t_end=t)

    def phase(self) -> dict:
        return {s: self.m[s].state for s in self.sides}

    def summary(self) -> dict:
        reps = self.reps
        by_side = {}
        for s in self.sides:
            rs = [r for r in reps if r.side == s]
            if not rs:
                continue
            by_side[SIDE_NAMES[s]] = {
                "reps": len(rs),
                "best_rom": round(max(r.rom for r in rs) if self.ex.id != "knee_extension"
                                  else min(r.rom for r in rs), 1),
                "avg_rom": round(sum(r.rom for r in rs) / len(rs), 1),
                "avg_quality": round(sum(r.quality for r in rs) / len(rs)),
                "avg_tempo_s": round(sum(r.duration for r in rs) / len(rs), 2),
            }
        faults: dict[str, int] = {}
        for r in reps:
            for c in r.faults:
                faults[c] = faults.get(c, 0) + 1
        return {
            "exercise": self.ex.id, "name": self.ex.name, "rom_label": self.ex.rom_label,
            "reps": len(reps), "by_side": by_side, "faults": faults,
            "avg_quality": round(sum(r.quality for r in reps) / len(reps)) if reps else 0,
            "rep_log": [r.as_dict() for r in reps],
        }
