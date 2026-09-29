"""Joint-angle kinematics from 2D keypoints.

All angles are computed in frame *pixels* (isotropic), never in normalised
coordinates, so a 16:9 webcam doesn't distort them. Conventions follow clinical
goniometry: 0 deg = anatomical neutral, increasing with flexion/abduction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .pose import KP

VIS = 0.3  # keypoint score needed to trust a joint


class OneEuro:
    """One-Euro filter (Casiez et al., CHI 2012) for jitter-free, low-lag keypoints."""

    def __init__(self, min_cutoff: float = 1.2, beta: float = 4.0, d_cutoff: float = 1.0):
        self.min_cutoff, self.beta, self.d_cutoff = min_cutoff, beta, d_cutoff
        self.x = self.dx = self.t = None

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, x: np.ndarray, t: float) -> np.ndarray:
        if self.x is None or t <= self.t:
            self.x, self.dx, self.t = x.copy(), np.zeros_like(x), t
            return x
        dt = t - self.t
        dx = (x - self.x) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        self.dx = a_d * dx + (1 - a_d) * self.dx
        cutoff = self.min_cutoff + self.beta * np.abs(self.dx)
        a = 1.0 / (1.0 + 1.0 / (2 * math.pi * cutoff * dt))
        self.x = a * x + (1 - a) * self.x
        self.t = t
        return self.x.copy()


class KeypointSmoother:
    """Filters (x, y) in units of body scale so the filter is camera-distance invariant."""

    def __init__(self):
        self.f = OneEuro()
        self.last: np.ndarray | None = None

    def __call__(self, kps: np.ndarray, t: float, scale: float) -> np.ndarray:
        out = kps.copy()
        xy = kps[:, :2] / max(scale, 1.0)
        if self.last is not None:
            weak = kps[:, 2] < VIS  # hold low-confidence points instead of letting them jump
            xy[weak] = self.last[weak]
        sm = self.f(xy, t)
        self.last = sm
        out[:, :2] = sm * max(scale, 1.0)
        return out

    def reset(self):
        self.f = OneEuro()
        self.last = None


def angle(a, b, c) -> float:
    """Interior angle ABC in degrees (0..180)."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    n = math.hypot(*ba) * math.hypot(*bc)
    if n < 1e-6:
        return float("nan")
    cos = max(-1.0, min(1.0, (ba[0] * bc[0] + ba[1] * bc[1]) / n))
    return math.degrees(math.acos(cos))


def tilt_from_vertical(top, bottom) -> float:
    """Angle of the segment bottom->top from image-vertical, degrees (0 = upright)."""
    dx, dy = top[0] - bottom[0], bottom[1] - top[1]
    return abs(math.degrees(math.atan2(dx, dy)))


@dataclass
class Frame:
    """Kinematic snapshot of one frame."""

    kps: np.ndarray             # (17, 3) x, y, score (smoothed, pixels)
    t: float
    view: str                   # 'front' | 'side' | 'unknown'
    body_px: float              # shoulder-to-ankle height in px (scale reference)
    angles: dict                # e.g. {'knee_flex_l': 12.0, ...}; NaN when not visible
    visible: dict               # joint -> bool

    def get(self, key: str) -> float:
        return self.angles.get(key, float("nan"))


def _pt(kps, name):
    return kps[KP[name], :2]


def _ok(kps, *names) -> bool:
    return all(kps[KP[n], 2] >= VIS for n in names)


def body_scale(kps: np.ndarray) -> float:
    """Rough standing height (px) from the visible chain; used for thresholds."""
    best = 0.0
    for s in ("left", "right"):
        chain = [f"{s}_shoulder", f"{s}_hip", f"{s}_knee", f"{s}_ankle"]
        seg = 0.0
        for a, b in zip(chain, chain[1:]):
            if _ok(kps, a, b):
                seg += float(np.hypot(*(_pt(kps, a) - _pt(kps, b))))
        best = max(best, seg)
    if best == 0.0:
        v = kps[kps[:, 2] >= VIS]
        if len(v) >= 2:
            best = float(np.ptp(v[:, 1]))
    return best


def detect_view(kps: np.ndarray) -> str:
    if not _ok(kps, "left_shoulder", "right_shoulder"):
        return "unknown"
    sw = float(np.hypot(*(_pt(kps, "left_shoulder") - _pt(kps, "right_shoulder"))))
    hips = [h for h in ("left_hip", "right_hip") if _ok(kps, h)]
    if not hips:
        return "unknown"
    sh_mid = (_pt(kps, "left_shoulder") + _pt(kps, "right_shoulder")) / 2
    hip_mid = np.mean([_pt(kps, h) for h in hips], axis=0)
    torso = float(np.hypot(*(sh_mid - hip_mid)))
    if torso < 1:
        return "unknown"
    r = sw / torso
    return "front" if r > 0.45 else ("side" if r < 0.3 else "oblique")


def compute(kps: np.ndarray, t: float) -> Frame:
    ang: dict[str, float] = {}
    vis: dict[str, bool] = {}
    nan = float("nan")
    for s, S in (("left", "l"), ("right", "r")):
        sh, el, wr = f"{s}_shoulder", f"{s}_elbow", f"{s}_wrist"
        hp, kn, an = f"{s}_hip", f"{s}_knee", f"{s}_ankle"

        vis[f"knee_{S}"] = _ok(kps, hp, kn, an)
        ang[f"knee_flex_{S}"] = 180 - angle(_pt(kps, hp), _pt(kps, kn), _pt(kps, an)) if vis[f"knee_{S}"] else nan

        vis[f"hip_{S}"] = _ok(kps, sh, hp, kn)
        ang[f"hip_flex_{S}"] = 180 - angle(_pt(kps, sh), _pt(kps, hp), _pt(kps, kn)) if vis[f"hip_{S}"] else nan

        vis[f"shoulder_{S}"] = _ok(kps, hp, sh, el)
        ang[f"shoulder_{S}"] = angle(_pt(kps, hp), _pt(kps, sh), _pt(kps, el)) if vis[f"shoulder_{S}"] else nan

        vis[f"elbow_{S}"] = _ok(kps, sh, el, wr)
        ang[f"elbow_flex_{S}"] = 180 - angle(_pt(kps, sh), _pt(kps, el), _pt(kps, wr)) if vis[f"elbow_{S}"] else nan

        # Frontal-plane hip abduction: thigh vs the trunk's downward axis.
        if _ok(kps, "left_shoulder", "right_shoulder", "left_hip", "right_hip", kn):
            sh_mid = (_pt(kps, "left_shoulder") + _pt(kps, "right_shoulder")) / 2
            hip_mid = (_pt(kps, "left_hip") + _pt(kps, "right_hip")) / 2
            down = hip_mid + (hip_mid - sh_mid)
            ang[f"hip_abd_{S}"] = angle(down - hip_mid + _pt(kps, hp), _pt(kps, hp), _pt(kps, kn))
        else:
            ang[f"hip_abd_{S}"] = nan

    shs = [n for n in ("left_shoulder", "right_shoulder") if _ok(kps, n)]
    hps = [n for n in ("left_hip", "right_hip") if _ok(kps, n)]
    if shs and hps:
        sh_mid = np.mean([_pt(kps, n) for n in shs], axis=0)
        hp_mid = np.mean([_pt(kps, n) for n in hps], axis=0)
        ang["trunk_lean"] = tilt_from_vertical(sh_mid, hp_mid)
    else:
        ang["trunk_lean"] = nan

    # Shoulder hiking (frontal): height difference between shoulders relative to width.
    if _ok(kps, "left_shoulder", "right_shoulder"):
        l, r = _pt(kps, "left_shoulder"), _pt(kps, "right_shoulder")
        w = max(1.0, float(abs(l[0] - r[0])))
        ang["shoulder_tilt"] = math.degrees(math.atan2(float(abs(l[1] - r[1])), w))
    else:
        ang["shoulder_tilt"] = nan

    # Knee valgus proxy (frontal): knee gap / ankle gap (<0.75 ≈ knees caving in).
    if _ok(kps, "left_knee", "right_knee", "left_ankle", "right_ankle"):
        kg = abs(float(_pt(kps, "left_knee")[0] - _pt(kps, "right_knee")[0]))
        ag = abs(float(_pt(kps, "left_ankle")[0] - _pt(kps, "right_ankle")[0]))
        ang["knee_gap_ratio"] = kg / ag if ag > 5 else nan
    else:
        ang["knee_gap_ratio"] = nan

    # Shoulder height above the feet (px). Unlike knee angle it separates sitting from
    # standing in *any* view: from the front a seated thigh points at the camera and the
    # knee looks straight, but the shoulders still drop by ~30%.
    ank = [n for n in ("left_ankle", "right_ankle") if _ok(kps, n)]
    if shs and ank:
        ang["stand_height_px"] = float(np.mean([kps[KP[n], 1] for n in ank]) - np.mean([kps[KP[n], 1] for n in shs]))
    else:
        ang["stand_height_px"] = nan

    # Foot lift (for balance tests): vertical ankle separation in body heights.
    scale = body_scale(kps)
    if _ok(kps, "left_ankle", "right_ankle") and scale > 0:
        ang["ankle_dy_l"] = float(_pt(kps, "right_ankle")[1] - _pt(kps, "left_ankle")[1]) / scale
    else:
        ang["ankle_dy_l"] = nan

    return Frame(kps=kps, t=t, view=detect_view(kps), body_px=scale, angles=ang, visible=vis)
