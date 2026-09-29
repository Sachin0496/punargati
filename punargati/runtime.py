"""ONNX Runtime session factory for the three Snapdragon compute units.

    npu  -> QNN EP, HTP backend (Hexagon NPU)      onnxruntime-qnn >= 2.x plugin EP
    gpu  -> QNN EP, GPU backend (Adreno GPU)
    cpu  -> ORT CPU EP (Oryon cores / any machine)

``onnxruntime-qnn`` 2.x is a *plugin* execution provider: it is registered at
runtime with ``ort.register_execution_provider_library`` and attached to a
session through ``SessionOptions.add_provider_for_devices``. On machines
without it (a dev Mac, an x64 laptop) everything transparently runs on CPU,
which is what lets judges try the app anywhere while the Snapdragon build
runs on the NPU.

The first NPU session compiles the graph for the HTP; the compiled QNN
context is cached next to the model (``*.npu_ctx.onnx`` + ``.bin``) so later
launches skip compilation.
"""

from __future__ import annotations

import logging
import os
import platform
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import onnxruntime as ort

log = logging.getLogger("punargati.runtime")

try:  # Snapdragon-only dependency
    import onnxruntime_qnn as qnn_ep  # type: ignore
except Exception:  # pragma: no cover - absent on non-Snapdragon machines
    qnn_ep = None

QNN = "QNNExecutionProvider"
_qnn_lock = threading.Lock()
_qnn_registered = False

TARGET_LABEL = {
    "npu": "Hexagon NPU (QNN HTP)",
    "gpu": "Adreno GPU (QNN GPU)",
    "cpu": "CPU (ORT CPU EP)",
}


def machine_info() -> dict:
    arch = os.environ.get("PROCESSOR_ARCHITECTURE") or platform.machine()
    return {
        "os": f"{platform.system()} {platform.release()}",
        "python_arch": arch,  # PROCESSOR_ARCHITECTURE is honest under x64 emulation
        "python": platform.python_version(),
        "processor": platform.processor() or platform.machine(),
        "onnxruntime": ort.__version__,
        "onnxruntime_qnn": getattr(qnn_ep, "__version__", None) or ("1.x (built into onnxruntime)" if _legacy() else None),
        "emulated": arch.upper() in ("AMD64", "X86") and "ARM" in (platform.processor() or "").upper(),
    }


def _register_qnn() -> bool:
    global _qnn_registered
    if qnn_ep is None:
        return False
    with _qnn_lock:
        if not _qnn_registered:
            try:
                ort.register_execution_provider_library(QNN, qnn_ep.get_library_path())
                _qnn_registered = True
            except Exception as e:  # e.g. x64 Python under emulation loading an ARM64 DLL
                log.warning("QNN EP registration failed: %s", e)
                return False
    return True


def _legacy() -> bool:
    """onnxruntime-qnn 1.x: a full ORT build with the QNN EP compiled in (no plugin)."""
    try:
        return qnn_ep is None and QNN in ort.get_available_providers()
    except Exception:
        return False


def _qnn_devices(kind: str) -> list:
    try:
        devices = [d for d in ort.get_ep_devices() if d.ep_name == QNN]
    except Exception:  # ORT < 1.22 has no device API
        return []
    want = {"npu": "NPU", "gpu": "GPU"}[kind]
    typed = []
    for d in devices:
        try:
            if want in str(d.device.type).upper():
                typed.append(d)
        except Exception:
            pass
    return typed or devices


def available_targets() -> list[str]:
    targets = []
    if _register_qnn() and _qnn_devices("npu"):
        targets.append("npu")
        if os.path.isfile(qnn_ep.get_qnn_gpu_path()):
            targets.append("gpu")
    elif _legacy():
        targets += ["npu", "gpu"]
    targets.append("cpu")
    return targets


@dataclass
class Session:
    """A loaded model on one compute unit plus its live latency stats."""

    name: str
    target: str
    model_path: Path
    sess: ort.InferenceSession
    full_offload: bool | None = None   # True = every op on the accelerator
    compile_s: float = 0.0
    from_cache: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _lat: list = field(default_factory=list, repr=False)

    @property
    def label(self) -> str:
        return TARGET_LABEL[self.target]

    @property
    def inputs(self):
        return self.sess.get_inputs()

    def run(self, feeds: dict) -> list[np.ndarray]:
        t = time.perf_counter()
        with self._lock:
            out = self.sess.run(None, feeds)
        ms = (time.perf_counter() - t) * 1000
        self._lat.append(ms)
        if len(self._lat) > 600:
            del self._lat[:300]
        return out

    def stats(self) -> dict:
        lat = sorted(self._lat[-300:])
        if not lat:
            return {"n": 0}
        pick = lambda q: round(lat[min(len(lat) - 1, int(q * len(lat)))], 2)  # noqa: E731
        return {"n": len(lat), "p50_ms": pick(0.5), "p95_ms": pick(0.95), "last_ms": round(self._lat[-1], 2)}

    def describe(self) -> dict:
        return {
            "model": self.name, "target": self.target, "label": self.label,
            "full_offload": self.full_offload, "compile_s": round(self.compile_s, 2),
            "from_cache": self.from_cache, "providers": self.sess.get_providers(),
            **self.stats(),
        }


def _qnn_options(target: str, perf_mode: str) -> dict:
    htp = qnn_ep.get_qnn_htp_path() if qnn_ep else "QnnHtp.dll"   # 1.x resolves next to ORT
    gpu = qnn_ep.get_qnn_gpu_path() if qnn_ep else "QnnGpu.dll"
    if target == "npu":
        return {
            "backend_path": htp,
            "htp_performance_mode": perf_mode,
            "htp_graph_finalization_optimization_mode": "3",
        }
    return {"backend_path": gpu}


def _qnn_session(model: Path, target: str, perf_mode: str, strict: bool, cache: Path | None):
    so = ort.SessionOptions()
    so.log_severity_level = 3
    if strict:
        # Fail loudly instead of silently running unsupported ops on the CPU;
        # lets us *prove* full NPU offload rather than assume it.
        so.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    if cache is not None:
        so.add_session_config_entry("ep.context_enable", "1")
        so.add_session_config_entry("ep.context_file_path", str(cache))
    if _qnn_registered:
        so.add_provider_for_devices(_qnn_devices(target), _qnn_options(target, perf_mode))
        return ort.InferenceSession(str(model), sess_options=so)
    return ort.InferenceSession(str(model), sess_options=so,
                                providers=[(QNN, _qnn_options(target, perf_mode)), "CPUExecutionProvider"])


def _warm(sess: ort.InferenceSession) -> None:
    feeds = {}
    for i in sess.get_inputs():
        shape = [d if isinstance(d, int) else 1 for d in i.shape]
        dtype = {"tensor(uint16)": np.uint16, "tensor(uint8)": np.uint8}.get(i.type, np.float32)
        feeds[i.name] = np.zeros(shape, dtype=dtype)
    sess.run(None, feeds)


def _clear_cache(cache: Path) -> None:
    for p in cache.parent.glob(cache.name.replace(".onnx", "") + "*"):
        p.unlink(missing_ok=True)


def load(name: str, model_path: Path, target: str, perf_mode: str = "burst") -> Session:
    """Load ``model_path`` on ``target`` ('npu' | 'gpu' | 'cpu').

    Raises if the target is unavailable; callers fall back explicitly so the
    UI can always show *which* unit is really doing the work.
    """
    model_path = Path(model_path)
    t0 = time.perf_counter()
    if target == "cpu":
        so = ort.SessionOptions()
        so.log_severity_level = 3
        so.intra_op_num_threads = max(1, min(4, (os.cpu_count() or 4) // 2))
        sess = ort.InferenceSession(str(model_path), sess_options=so, providers=["CPUExecutionProvider"])
        _warm(sess)
        return Session(name, "cpu", model_path, sess, full_offload=None,
                       compile_s=time.perf_counter() - t0)

    plugin = _register_qnn() and bool(_qnn_devices(target))
    if not plugin and not _legacy():
        if qnn_ep is None:
            raise RuntimeError("onnxruntime-qnn is not installed (or not loadable in this Python)")
        raise RuntimeError(f"no QNN device found for target '{target}' (NPU driver missing?)")

    cache = model_path.with_name(f"{model_path.stem}.{target}_ctx.onnx")
    attempts: list[tuple[str, dict]] = []
    if cache.is_file():
        attempts.append(("cached", {"model": cache, "strict": False, "cache": None}))
    attempts += [
        ("strict+cache", {"model": model_path, "strict": True, "cache": cache}),
        ("strict", {"model": model_path, "strict": True, "cache": None}),
        ("fallback", {"model": model_path, "strict": False, "cache": None}),
    ]
    errors = []
    for how, a in attempts:
        try:
            if how == "strict+cache":
                _clear_cache(cache)
            sess = _qnn_session(a["model"], target, perf_mode, a["strict"], a["cache"])
            _warm(sess)
            full = True if a["strict"] else (True if how == "cached" else None)
            log.info("%s on %s via %s (%.1fs)", name, target, how, time.perf_counter() - t0)
            return Session(name, target, model_path, sess, full_offload=full,
                           compile_s=time.perf_counter() - t0, from_cache=(how == "cached"))
        except Exception as e:
            errors.append(f"{how}: {e}")
            log.warning("%s on %s via %s failed: %s", name, target, how, e)
            if how in ("cached", "strict+cache"):
                _clear_cache(cache)  # stale/partial context (e.g. after a QAIRT upgrade)
    raise RuntimeError(f"could not load {name} on {target}: " + " | ".join(errors))
