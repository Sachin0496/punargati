"""MoveNet pose estimation with MoveNet's crop-tracking.

The browser renders the *crop region* the tracker asks for into a 192x192
canvas and ships raw RGBA pixels; this module turns them into model input
(handling the w8a16 build's uint16 quantized I/O), runs the model on the
selected compute unit, maps keypoints back to full-frame pixels and proposes
the next crop. Tracking the crop keeps the person large in the model's view,
which is what makes a 192px model accurate enough for goniometry.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import runtime
from .models import ASSETS, PREFERRED, PREFERRED_WHOLEBODY

KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]
KP = {n: i for i, n in enumerate(KEYPOINTS)}
EDGES = [
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6),
]
INPUT = 192
MIN_SCORE = 0.2
TORSO_EXPANSION = 1.9
BODY_EXPANSION = 1.2


@dataclass
class Crop:
    """Square crop in source-frame pixels (may extend past the frame edges)."""

    x: float
    y: float
    size: float

    def as_dict(self) -> dict:
        return {"x": round(float(self.x), 1), "y": round(float(self.y), 1), "size": round(float(self.size), 1)}


def init_crop(w: int, h: int) -> Crop:
    size = float(max(w, h))
    return Crop((w - size) / 2, (h - size) / 2, size)


def next_crop(kps: np.ndarray, w: int, h: int) -> Crop:
    """MoveNet's determine_crop_region, in pixel space.

    ``kps`` is (17, 3) of (x, y, score) in frame pixels.
    """
    sc = kps[:, 2]
    torso = [KP["left_shoulder"], KP["right_shoulder"], KP["left_hip"], KP["right_hip"]]
    if not (sc[KP["left_hip"]] > MIN_SCORE or sc[KP["right_hip"]] > MIN_SCORE) or \
       not (sc[KP["left_shoulder"]] > MIN_SCORE or sc[KP["right_shoulder"]] > MIN_SCORE):
        return init_crop(w, h)
    hips = [i for i in (KP["left_hip"], KP["right_hip"]) if sc[i] > MIN_SCORE]
    cx = float(np.mean(kps[hips, 0]))
    cy = float(np.mean(kps[hips, 1]))
    torso_r = max(max(abs(cx - kps[i, 0]), abs(cy - kps[i, 1])) for i in torso if sc[i] > MIN_SCORE)
    vis = sc > MIN_SCORE
    body_r = float(np.max(np.maximum(np.abs(cx - kps[vis, 0]), np.abs(cy - kps[vis, 1]))))
    half = max(torso_r * TORSO_EXPANSION, body_r * BODY_EXPANSION)
    half = min(half, max(cx, w - cx, cy, h - cy))
    if half > max(w, h) / 2:
        return init_crop(w, h)
    half = max(half, 48.0)
    return Crop(cx - half, cy - half, 2 * half)


class PoseEstimator:
    def __init__(self, target: str = "npu", perf_mode: str = "burst"):
        self.session: runtime.Session | None = None
        self.load(target, perf_mode)

    def load(self, target: str, perf_mode: str = "burst") -> None:
        order = {"npu": ["npu", "gpu", "cpu"], "gpu": ["gpu", "cpu"], "cpu": ["cpu"]}[target]
        errors = []
        for t in order:
            asset = ASSETS[PREFERRED[t]]
            try:
                sess = runtime.load(f"MoveNet ({asset.precision})", asset.onnx_path, t, perf_mode)
            except Exception as e:  # keep trying lower tiers; the UI shows what we landed on
                errors.append(f"{t}: {e}")
                continue
            self.session = sess
            self.asset = asset
            self._setup_quant(asset.metadata())
            self.load_errors = errors
            return
        raise RuntimeError("no compute target could load MoveNet: " + "; ".join(errors))

    def _setup_quant(self, meta: dict) -> None:
        spec = meta.get("model_files", {}).get(self.asset.onnx_file, {})
        i = spec.get("inputs", {}).get("image", {}).get("quantization_parameters")
        o = spec.get("outputs", {}).get("kpt_with_conf", {}).get("quantization_parameters")
        self.in_q = (i["scale"], i["zero_point"]) if i else None
        self.out_q = (o["scale"], o["zero_point"]) if o else None
        inp = self.session.inputs[0]
        self.input_name = inp.name
        self.input_dtype = np.uint16 if inp.type == "tensor(uint16)" else np.float32

    def infer(self, rgb: np.ndarray) -> np.ndarray:
        """``rgb``: (192, 192, 3) uint8. Returns (17, 3) of (y, x, score) in [0, 1] crop units."""
        x = rgb.astype(np.float32).transpose(2, 0, 1)[None] / 255.0
        if self.in_q:
            s, zp = self.in_q
            x = np.clip(np.rint(x / s + zp), 0, 65535).astype(self.input_dtype)
        out = self.session.run({self.input_name: x})[0]
        if self.out_q:
            s, zp = self.out_q
            out = (out.astype(np.float32) - zp) * s
        return out.reshape(17, 3).astype(np.float32)

    def infer_crop(self, rgba: bytes | np.ndarray, crop: Crop) -> np.ndarray:
        """Run on a browser-rendered square crop (any N×N; 192 is native).

        Returns (17, 3) (x, y, score) in frame pixels.
        """
        rgb = as_rgb(rgba)
        if rgb.shape[0] != INPUT:
            idx = ((np.arange(INPUT) + 0.5) * rgb.shape[0] / INPUT).astype(int)
            rgb = rgb[np.ix_(idx, idx)]
        yxs = self.infer(rgb)
        out = np.empty_like(yxs)
        out[:, 0] = crop.x + yxs[:, 1] * crop.size
        out[:, 1] = crop.y + yxs[:, 0] * crop.size
        out[:, 2] = yxs[:, 2]
        return out


def as_rgb(rgba) -> np.ndarray:
    a = np.frombuffer(rgba, dtype=np.uint8) if isinstance(rgba, (bytes, bytearray, memoryview)) else np.asarray(rgba)
    if a.ndim == 3:
        return a[:, :, :3]
    n = int(round((a.size / 4) ** 0.5))
    return a.reshape(n, n, 4)[:, :, :3]


def _load_first(order, table, label, perf_mode):
    errors = []
    for t in order:
        asset = ASSETS[table[t]]
        if not asset.present():
            errors.append(f"{t}: {asset.key} not downloaded (python -m punargati.models download)")
            continue
        try:
            return runtime.load(f"{label} ({asset.precision})", asset.onnx_path, t, perf_mode), asset, errors
        except Exception as e:
            errors.append(f"{t}: {e}")
    raise RuntimeError(f"no compute target could load {label}: " + "; ".join(errors))


# COCO-WholeBody indices used beyond the 17 body joints.
FEET = {"left_big_toe": 17, "left_small_toe": 18, "left_heel": 19,
        "right_big_toe": 20, "right_small_toe": 21, "right_heel": 22}
W_IN, H_IN = 192, 256   # RTMPose input (portrait)


class WholeBody:
    """RTMPose-Body2d (133 keypoints) cascaded after MoveNet — "precision mode".

    MoveNet (always on) supplies the person box; RTMPose re-estimates the body at
    higher accuracy and adds feet, which enables ankle exercises. Both run on the NPU.
    """

    def __init__(self, target: str = "npu", perf_mode: str = "burst"):
        order = {"npu": ["npu", "gpu", "cpu"], "gpu": ["gpu", "cpu"], "cpu": ["cpu"]}[target]
        self.session, self.asset, self.load_errors = _load_first(order, PREFERRED_WHOLEBODY, "RTMPose", perf_mode)
        spec = self.asset.metadata().get("model_files", {}).get(self.asset.onnx_file, {})
        q = lambda d: (d["scale"], d["zero_point"]) if d else None  # noqa: E731
        self.in_q = q(spec.get("inputs", {}).get("image", {}).get("quantization_parameters"))
        outs = spec.get("outputs", {})
        self.out_q = [q(outs.get(n, {}).get("quantization_parameters")) for n in ("pred_x", "pred_y")]
        inp = self.session.inputs[0]
        self.input_name = inp.name
        self.quantized = inp.type == "tensor(uint16)"

    @staticmethod
    def person_box(body: np.ndarray, min_score: float = 0.3):
        v = body[body[:, 2] >= min_score]
        if len(v) < 5:
            return None
        x0, y0 = v[:, 0].min(), v[:, 1].min()
        x1, y1 = v[:, 0].max(), v[:, 1].max()
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        bw, bh = (x1 - x0) * 1.25, (y1 - y0) * 1.25
        bw, bh = (bh * 0.75, bh) if bw / max(bh, 1e-6) < 0.75 else (bw, bw / 0.75)
        return cx - bw / 2, cy - bh / 2, bw, bh

    def infer(self, rgba, crop: Crop, body: np.ndarray) -> np.ndarray | None:
        """Returns (133, 3) (x, y, score) in frame pixels, or None without a person box."""
        box = self.person_box(body)
        if box is None:
            return None
        bx, by, bw, bh = box
        img = as_rgb(rgba)
        n = img.shape[0]
        # frame px -> crop-image px (nearest), black outside the crop
        u = np.floor((bx + (np.arange(W_IN) + 0.5) * bw / W_IN - crop.x) / crop.size * n).astype(int)
        v = np.floor((by + (np.arange(H_IN) + 0.5) * bh / H_IN - crop.y) / crop.size * n).astype(int)
        patch = np.zeros((H_IN, W_IN, 3), np.uint8)
        vu, vv = (u >= 0) & (u < n), (v >= 0) & (v < n)
        patch[np.ix_(vv, vu)] = img[np.ix_(v[vv], u[vu])]
        x = patch.astype(np.float32).transpose(2, 0, 1)[None]  # 0..255 RGB, model normalises inside
        if self.quantized and self.in_q:
            sc, zp = self.in_q
            x = np.clip(np.rint(x / sc + zp), 0, 65535).astype(np.uint16)
        px, py = self.session.run({self.input_name: x})
        outs = []
        for o, q in zip((px, py), self.out_q):
            o = o[0].astype(np.float32)
            if q and self.quantized:
                o = (o - q[1]) * q[0]
            outs.append(o)
        px, py = outs
        xs, ys = px.argmax(1) / 2.0, py.argmax(1) / 2.0     # SimCC split ratio 2
        score = np.minimum(px.max(1), py.max(1))
        out = np.empty((px.shape[0], 3), np.float32)
        out[:, 0] = bx + (xs + 0.5) / W_IN * bw
        out[:, 1] = by + (ys + 0.5) / H_IN * bh
        out[:, 2] = np.clip(score, 0, 1)
        return out


def render_crop(frame: np.ndarray, crop: Crop, size: int = INPUT) -> np.ndarray:
    """Server-side equivalent of the browser's canvas crop (for offline eval/tests).

    ``frame``: (H, W, 3) uint8. Nearest-neighbour sampling; out-of-frame is black.
    """
    h, w = frame.shape[:2]
    idx = (np.arange(size) + 0.5) * (crop.size / size)
    xs = np.floor(crop.x + idx).astype(int)
    ys = np.floor(crop.y + idx).astype(int)
    out = np.zeros((size, size, 3), dtype=np.uint8)
    vx = (xs >= 0) & (xs < w)
    vy = (ys >= 0) & (ys < h)
    out[np.ix_(vy, vx)] = frame[np.ix_(ys[vy], xs[vx])]
    return out
