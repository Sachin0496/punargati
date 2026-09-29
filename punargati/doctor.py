"""Environment check: is this Python native ARM64, is the Hexagon NPU reachable, does MoveNet run on it?

    python -m punargati.doctor
"""

from __future__ import annotations

import platform
import sys
import time

import numpy as np
import onnxruntime as ort

from . import runtime
from .models import ASSETS, PREFERRED, status


def line(ok, msg):
    print(f"  [{'ok' if ok is True else ('!!' if ok is False else '--')}] {msg}")


def main() -> int:
    print("\nPunarGati doctor\n")
    m = runtime.machine_info()
    arm = m["python_arch"].upper() in ("ARM64", "AARCH64", "ARM")
    line(True, f"OS {m['os']} · Python {m['python']} · process arch {m['python_arch']}")
    if platform.system() == "Windows" and not arm:
        line(False, "This Python runs under x64 emulation. The NPU plugin needs a native ARM64 Python:\n"
                    "       winget install --id Python.Python.3.12 --architecture arm64   then re-run scripts\\setup.ps1")
    line(True, f"onnxruntime {ort.__version__}")
    line(runtime.qnn_ep is not None or None,
         f"onnxruntime-qnn {m['onnxruntime_qnn'] or 'not installed (fine off-Snapdragon: CPU fallback)'}")
    for s in status():
        line(s["present"], f"model {s['key']} ({s['source']})")

    targets = runtime.available_targets()
    line("npu" in targets or None, f"compute units found: {', '.join(t.upper() for t in targets)}")
    if runtime.qnn_ep is not None:
        try:
            for d in ort.get_ep_devices():
                print(f"       ep device: {d.ep_name} · {getattr(d.device, 'type', '?')} · vendor {getattr(d.device, 'vendor', '?')}")
        except Exception as e:
            print(f"       (could not list EP devices: {e})")

    ok_npu = None
    for t in targets:
        asset = ASSETS[PREFERRED[t]]
        try:
            sess = runtime.load(f"MoveNet ({asset.precision})", asset.onnx_path, t)
            i = sess.inputs[0]
            x = (np.random.randint(0, 65535, size=(1, 3, 192, 192), dtype=np.uint16)
                 if i.type == "tensor(uint16)" else np.random.rand(1, 3, 192, 192).astype(np.float32))
            for _ in range(10):
                sess.run({i.name: x})
            t0 = time.perf_counter()
            for _ in range(100):
                sess.run({i.name: x})
            ms = (time.perf_counter() - t0) * 10
            full = " · 100% of ops on accelerator" if sess.full_offload else ""
            line(True, f"{sess.label}: {ms:.2f} ms/inference (load {sess.compile_s:.1f}s"
                       f"{', from QNN context cache' if sess.from_cache else ''}){full}")
            if t == "npu":
                ok_npu = True
        except Exception as e:
            line(False, f"{t}: {str(e)[:300]}")
            if t == "npu":
                ok_npu = False
    print()
    if ok_npu:
        print("  Ready: pose tracking will run on the Hexagon NPU.  Start with:  scripts\\run.ps1\n")
        return 0
    if platform.system() == "Windows" and platform.machine().upper() == "ARM64":
        print("  NPU not available — the app will still run on CPU. See docs/WINDOWS_ARM64_SETUP.md › Troubleshooting.\n")
        return 1
    print("  Not a Snapdragon/QNN machine: running on CPU (expected on this PC).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
