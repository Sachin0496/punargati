"""NPU vs GPU vs CPU benchmark for the pose model — the numbers behind "why the NPU".

    python -m punargati.bench [--seconds 10] [--markdown]

For each compute unit it measures (1) raw inference latency and (2) the cost
of *sustained* 30 fps coaching: process CPU load and, on Windows laptops
running on battery, the system discharge rate reported by the battery driver.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time

import numpy as np

from . import runtime, store
from .models import ASSETS, PREFERRED, PREFERRED_WHOLEBODY


def _battery_mw() -> float | None:
    """Instantaneous discharge rate (mW) from WMI BatteryStatus; None if unavailable/charging."""
    if platform.system() != "Windows":
        return None
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance -Namespace root/wmi -ClassName BatteryStatus | "
             "Select-Object -First 1 DischargeRate,PowerOnline | ConvertTo-Json"],
            capture_output=True, text=True, timeout=8, creationflags=0x08000000)
        d = json.loads(out.stdout or "{}")
        if d.get("PowerOnline"):
            return None
        rate = d.get("DischargeRate")
        return float(rate) if rate else None
    except Exception:
        return None


def _feeds(sess: runtime.Session) -> dict:
    i = sess.inputs[0]
    shape = [d if isinstance(d, int) else 1 for d in i.shape]
    if i.type == "tensor(uint16)":
        return {i.name: np.random.randint(0, 65535, size=shape, dtype=np.uint16)}
    return {i.name: np.random.rand(*shape).astype(np.float32)}


def bench_target(target: str, seconds: float = 10.0, iters: int = 300, power: bool = True,
                 perf_mode: str = "burst", family: str = "MoveNet") -> dict:
    asset = ASSETS[(PREFERRED if family == "MoveNet" else PREFERRED_WHOLEBODY)[target]]
    sess = runtime.load(f"{family} ({asset.precision})", asset.onnx_path, target, perf_mode)
    feeds = _feeds(sess)
    for _ in range(20):
        sess.run(feeds)
    lat = []
    for _ in range(iters):
        t = time.perf_counter()
        sess.run(feeds)
        lat.append((time.perf_counter() - t) * 1000)
    lat.sort()

    # Sustained 30 fps: what it costs to coach a whole session on this unit.
    period = 1 / 30
    c0, w0 = sum(os.times()[:2]), time.perf_counter()
    watts = []
    next_power = w0
    n = 0
    while time.perf_counter() - w0 < seconds:
        t = time.perf_counter()
        sess.run(feeds)
        n += 1
        if power and t >= next_power:
            mw = _battery_mw()
            if mw:
                watts.append(mw / 1000)
            next_power = t + 2.0
        sleep = period - (time.perf_counter() - t)
        if sleep > 0:
            time.sleep(sleep)
    wall = time.perf_counter() - w0
    cpu = 100 * (sum(os.times()[:2]) - c0) / wall / (os.cpu_count() or 1)
    pick = lambda q: round(lat[min(len(lat) - 1, int(q * len(lat)))], 3)  # noqa: E731
    label = sess.label + (f" · {perf_mode.replace('_', ' ')}" if target == "npu" else "")
    return {
        "model": family, "target": target, "label": label, "precision": asset.precision, "perf_mode": perf_mode,
        "full_offload": sess.full_offload, "load_s": round(sess.compile_s, 2),
        "p50_ms": pick(0.5), "p90_ms": pick(0.9), "p99_ms": pick(0.99),
        "max_fps": round(1000 / max(1e-6, pick(0.5))),
        "sustained_fps": round(n / wall, 1), "cpu_percent_at_30fps": round(cpu, 1),
        "battery_watts_at_30fps": round(sum(watts) / len(watts), 2) if watts else None,
    }


def run(seconds: float = 10.0, targets: list[str] | None = None) -> dict:
    targets = targets or runtime.available_targets()
    res = {"machine": runtime.machine_info(), "when": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "model": "MoveNet + RTMPose-Body2d (Qualcomm AI Hub v0.63.0)", "results": []}
    idle = _battery_mw()
    res["idle_battery_watts"] = round(idle / 1000, 2) if idle else None
    runs = []
    for t in targets:
        # On the NPU also measure a power-saving HTP clock policy: at 30 fps the NPU idles
        # ~97% of each frame, so a lower clock can cut power while staying real-time.
        runs += [("MoveNet", t, "burst"), ("MoveNet", t, "power_saver")] if t == "npu" else [("MoveNet", t, "burst")]
    if any(ASSETS[k].present() for k in PREFERRED_WHOLEBODY.values()):
        runs += [("RTMPose", t, "burst") for t in targets]   # precision-mode cascade model
    for fam, t, mode in runs:
        try:
            res["results"].append(bench_target(t, seconds, perf_mode=mode, family=fam))
        except Exception as e:
            res["results"].append({"model": fam, "target": t, "perf_mode": mode, "error": str(e)[:300]})
    store.save_bench(res)
    return res


def markdown(res: dict) -> str:
    rows = ["| Model | Compute unit | Precision | p50 latency | p99 latency | Max FPS | CPU load @30 fps | Battery draw @30 fps |",
            "|---|---|---|---:|---:|---:|---:|---:|"]
    for r in res["results"]:
        if "error" in r:
            rows.append(f"| {r.get('model', '')} | {r['target']} | — | error: {r['error'][:60]} | | | | |")
            continue
        w = f"{r['battery_watts_at_30fps']} W" if r["battery_watts_at_30fps"] else "n/a"
        rows.append(f"| {r['model']} | {r['label']} | {r['precision']} | {r['p50_ms']} ms | {r['p99_ms']} ms | "
                    f"{r['max_fps']} | {r['cpu_percent_at_30fps']}% | {w} |")
    m = res["machine"]
    return (f"Machine: {m['processor']} · {m['os']} · Python {m['python']} ({m['python_arch']}) · "
            f"onnxruntime {m['onnxruntime']} · onnxruntime-qnn {m['onnxruntime_qnn']}\n\n" + "\n".join(rows))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--targets", nargs="*")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--write-docs", action="store_true",
                    help="replace the 'Measured on this device' section of docs/BENCHMARKS.md")
    a = ap.parse_args(argv)
    res = run(a.seconds, a.targets)
    print(markdown(res) if a.markdown or a.write_docs else json.dumps(res, indent=2))
    if a.write_docs:
        write_docs(res)
    return 0


BEGIN, END = "<!-- bench:begin -->", "<!-- bench:end -->"


def write_docs(res: dict) -> None:
    from .models import REPO_ROOT
    doc = REPO_ROOT / "docs" / "BENCHMARKS.md"
    text = doc.read_text(encoding="utf-8")
    block = f"{BEGIN}\n_Measured {res['when'].replace('T', ' ')} with `python -m punargati.bench --write-docs`._\n\n{markdown(res)}\n{END}"
    if BEGIN in text and END in text:
        text = text[:text.index(BEGIN)] + block + text[text.index(END) + len(END):]
    else:
        text += "\n" + block + "\n"
    doc.write_text(text, encoding="utf-8")
    print(f"\nwrote {doc}")


if __name__ == "__main__":
    sys.exit(main())
