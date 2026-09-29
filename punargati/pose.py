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
from .models import ASSETS, PREFERRED

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
        """Run on a browser-rendered crop. Returns (17, 3) (x, y, score) in frame pixels."""
        a = np.frombuffer(rgba, dtype=np.uint8) if isinstance(rgba, (bytes, bytearray, memoryview)) else rgba
        rgb = a.reshape(INPUT, INPUT, -1)[:, :, :3]
        yxs = self.infer(rgb)
        out = np.empty_like(yxs)
        out[:, 0] = crop.x + yxs[:, 1] * crop.size
        out[:, 1] = crop.y + yxs[:, 0] * crop.size
        out[:, 2] = yxs[:, 2]
        return out


def render_crop(frame: np.ndarray, crop: Crop) -> np.ndarray:
    """Server-side equivalent of the browser's canvas crop (for offline eval/tests).

    ``frame``: (H, W, 3) uint8. Nearest-neighbour sampling; out-of-frame is black.
    """
    h, w = frame.shape[:2]
    idx = (np.arange(INPUT) + 0.5) * (crop.size / INPUT)
    xs = np.floor(crop.x + idx).astype(int)
    ys = np.floor(crop.y + idx).astype(int)
    out = np.zeros((INPUT, INPUT, 3), dtype=np.uint8)
    vx = (xs >= 0) & (xs < w)
    vy = (ys >= 0) & (ys < h)
    out[np.ix_(vy, vx)] = frame[np.ix_(ys[vy], xs[vx])]
    return out
