"""The live coaching engine: frame in -> pose -> kinematics -> reps/tests -> cues out."""

from __future__ import annotations

import math
import os
import threading
import time

import numpy as np

from . import store
from .assessments import TESTS, Assessment
from .exercises import LIBRARY, RepCounter
from .kinematics import KeypointSmoother, compute
from .pose import Crop, PoseEstimator, WholeBody, init_crop, next_crop

CUE_COOLDOWN_S = 4.0


class CpuMeter:
    """Process CPU utilisation as a share of the whole machine (Task-Manager style)."""

    def __init__(self):
        self.t = time.perf_counter()
        self.c = self._cpu()
        self.value = 0.0

    @staticmethod
    def _cpu() -> float:
        t = os.times()
        return t.user + t.system

    def sample(self) -> float:
        now, c = time.perf_counter(), self._cpu()
        dt = now - self.t
        if dt >= 1.0:
            self.value = 100.0 * (c - self.c) / dt / (os.cpu_count() or 1)
            self.t, self.c = now, c
        return round(self.value, 1)


class Engine:
    def __init__(self, target: str = "npu", perf_mode: str = "burst"):
        self.lock = threading.RLock()
        self.perf_mode = perf_mode
        self.pose = PoseEstimator(target, perf_mode)
        self.smoother = KeypointSmoother()
        self.cpu = CpuMeter()
        self.activity = None          # RepCounter | Assessment | None
        self.kind = None
        self.started = None
        self.t_first = None
        self.last_cue: dict[str, float] = {}
        self.missing_since = None
        self.view_bad_since = None
        self.frames = 0
        self.fps_t = time.perf_counter()
        self.fps_n = 0
        self.fps = 0.0
        self.last_t = None
        self.target_reps = 10
        self.wholebody: WholeBody | None = None
        self.precision = False

    # -- compute unit ---------------------------------------------------------
    def set_target(self, target: str) -> dict:
        with self.lock:
            self.pose.load(target, self.perf_mode)
            if self.wholebody is not None:
                try:
                    self.wholebody = WholeBody(self.pose.session.target, self.perf_mode)
                except Exception:
                    self.wholebody, self.precision = None, False
        return self.pose.session.describe()

    def set_precision(self, on: bool) -> dict:
        """Cascade RTMPose-WholeBody after MoveNet (loaded lazily on the same unit)."""
        with self.lock:
            if on and self.wholebody is None:
                self.wholebody = WholeBody(self.pose.session.target, self.perf_mode)
            self.precision = bool(on)
            self.smoother.reset()
        return self.precision_status()

    def precision_status(self) -> dict:
        wb = self.wholebody
        return {"on": self.precision, "model": wb.session.describe() if wb else None}

    # -- activity lifecycle ---------------------------------------------------
    def start(self, kind: str, item_id: str, side: str = "auto", target_reps: int = 10) -> dict:
        with self.lock:
            if kind == "exercise":
                if LIBRARY[item_id].needs == "wholebody" and not self.precision:
                    self.set_precision(True)   # feet need RTMPose; raises if unavailable
                self.activity = RepCounter(LIBRARY[item_id], side)
            elif kind == "assessment":
                self.activity = Assessment(item_id, store.get_profile())
            else:
                raise ValueError(kind)
            self.kind = kind
            self.target_reps = int(target_reps or 10)
            self.started = time.strftime("%Y-%m-%dT%H:%M:%S")
            self.t_first = None
            self.last_cue.clear()
            self.missing_since = self.view_bad_since = None
            self.smoother.reset()
        return {"ok": True, "kind": kind, "id": item_id, "precision": self.precision}

    def stop(self, save: bool = True) -> dict | None:
        with self.lock:
            act, kind = self.activity, self.kind
            self.activity = self.kind = None
        if act is None:
            return None
        s = self.pose.session.describe()
        rec = {
            "kind": kind, "started": self.started, "ended": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "compute": {"target": s["target"], "label": s["label"], "p50_ms": s.get("p50_ms")},
            "profile": {k: store.get_profile().get(k) for k in ("age", "sex", "condition", "affected_side")},
        }
        if kind == "exercise":
            summ = act.summary()
            if summ["reps"] == 0:
                return {"saved": False, **rec, "summary": summ}
            rec.update({"item": act.ex.id, "name": act.ex.name, "summary": summ,
                        "target_reps": self.target_reps})
        else:
            if act.result is None:
                return {"saved": False, **rec, "status": act.status(self.last_t or 0.0)}
            rec.update({"item": act.id, "name": act.spec["name"], "result": act.result})
        if save:
            rec["id"] = store.save_session(rec)
            rec["saved"] = True
        return rec

    # -- per-frame ------------------------------------------------------------
    def _cue(self, cue: str, t: float, side: str | None = None) -> dict | None:
        key = f"{cue}:{side}"
        if t - self.last_cue.get(key, -1e9) < CUE_COOLDOWN_S:
            return None
        self.last_cue[key] = t
        return {"type": "cue", "cue": cue, "side": side}

    def process(self, rgba: bytes, crop: Crop, w: int, h: int, t: float) -> dict:
        with self.lock:
            return self._process(rgba, crop, w, h, t)

    def _process(self, rgba: bytes, crop: Crop, w: int, h: int, t: float) -> dict:
        t0 = time.perf_counter()
        raw = self.pose.infer_crop(rgba, crop)
        infer_ms = self.pose.session.stats().get("last_ms")
        full = np.zeros((23, 3), np.float32)      # 17 body + 6 feet (feet only in precision mode)
        full[:17] = raw
        wb_ms = None
        if self.precision and self.wholebody is not None:
            wb = self.wholebody.infer(rgba, crop, raw)
            wb_ms = self.wholebody.session.stats().get("last_ms")
            if wb is not None:
                better = wb[:17, 2] >= 0.3
                full[:17][better] = wb[:17][better]
                full[17:23] = wb[17:23]
        if self.last_t is not None and t < self.last_t:  # video looped / seeked back
            self.smoother.reset()
        self.last_t = t
        scale = max(w, h)
        kps = self.smoother(full, t, scale)
        conf = float(np.mean(raw[:, 2]))
        nxt = next_crop(raw, w, h) if conf > 0.15 else init_crop(w, h)
        f = compute(kps, t)

        events: list[dict] = []
        act = self.activity
        activity = None
        if act is not None:
            raw_ev = act.update(f)
            for e in raw_ev:
                if e["type"] == "cue":
                    c = self._cue(e["cue"], t, e.get("side"))
                    if c:
                        events.append(c)
                else:
                    events.append(e)
            events += self._guard(f, t)
            activity = self._activity_state(f, t)

        self.fps_n += 1
        now = time.perf_counter()
        if now - self.fps_t >= 1.0:
            self.fps = self.fps_n / (now - self.fps_t)
            self.fps_n, self.fps_t = 0, now
        s = self.pose.session
        st = s.stats()
        return {
            "kps": [[round(float(x), 1), round(float(y), 1), round(float(c), 3)] for x, y, c in kps],
            "crop": nxt.as_dict(),
            "view": f.view,
            "confidence": round(conf, 3),
            "angles": {k: (None if math.isnan(v) else round(v, 1)) for k, v in f.angles.items()},
            "activity": activity,
            "events": events,
            "perf": {
                "target": s.target, "label": s.label, "infer_ms": infer_ms, "wb_ms": wb_ms,
                "precision": self.precision,
                "p50_ms": st.get("p50_ms"), "p95_ms": st.get("p95_ms"),
                "engine_ms": round((time.perf_counter() - t0) * 1000, 2),
                "fps": round(self.fps, 1), "cpu": self.cpu.sample(),
                "full_offload": s.full_offload,
            },
        }

    def _needed_ok(self, f) -> bool:
        act = self.activity
        if isinstance(act, RepCounter):
            return any(not math.isnan(v) for v in act.value.values())
        return f.body_px > 0

    def _required_view(self) -> str:
        act = self.activity
        if isinstance(act, RepCounter):
            return act.ex.view
        return TESTS[act.id]["view"] if act else "any"

    def _guard(self, f, t) -> list[dict]:
        out = []
        if not self._needed_ok(f):
            self.missing_since = self.missing_since or t
            if t - self.missing_since > 1.5:
                c = self._cue("step_back", t)
                if c:
                    out.append(c)
        else:
            self.missing_since = None
        need = self._required_view()
        bad = (need == "side" and f.view == "front") or (need == "front" and f.view == "side")
        if bad:
            self.view_bad_since = self.view_bad_since or t
            if t - self.view_bad_since > 2.0:
                c = self._cue("turn_side" if need == "side" else "face_camera", t)
                if c:
                    out.append(c)
        else:
            self.view_bad_since = None
        return out

    def _activity_state(self, f, t) -> dict:
        act = self.activity
        if isinstance(act, RepCounter):
            last = act.reps[-1].as_dict() if act.reps else None
            return {
                "kind": "exercise", "id": act.ex.id, "name": act.ex.name,
                "counts": act.counts(), "total": len(act.reps), "target_reps": self.target_reps,
                "phase": act.phase(),
                "value": {k: (None if math.isnan(v) else round(v, 1)) for k, v in act.value.items()},
                "rest": act.ex.rest, "enter": act.ex.enter, "goal": act.ex.target,
                "last_rep": last,
            }
        return {"kind": "assessment", **act.status(t)}
