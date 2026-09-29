"""Run a recorded video through the exact live pipeline (needs ffmpeg on PATH).

    python -m punargati.offline clip.mp4 --exercise squat [--target npu] [--trace out.csv]

Used for regression tests and for validating rep counts against a physio's
manual count on the same clip.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

import numpy as np

from .engine import Engine
from .pose import init_crop, render_crop


def frames(path: str, fps: float = 30.0, width: int = 960):
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "json", path], capture_output=True, text=True, check=True)
    st = json.loads(probe.stdout)["streams"][0]
    w = width
    h = int(round(st["height"] * width / st["width"] / 2) * 2)
    p = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = 0
    while True:
        buf = p.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            break
        yield n / fps, np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        n += 1
    p.wait()


def run(path: str, kind: str, item: str, target: str = "cpu", trace: str | None = None, engine=None) -> dict:
    eng = engine or Engine(target)
    eng.start(kind, item)
    crop = None
    rows = []
    events = []
    for t, fr in frames(path):
        h, w = fr.shape[:2]
        crop = crop or init_crop(w, h)
        rgba = np.dstack([render_crop(fr, crop), np.full((192, 192), 255, np.uint8)])
        out = eng.process(rgba.tobytes(), crop, w, h, t)
        c = out["crop"]
        crop = type(crop)(c["x"], c["y"], c["size"])
        events += [dict(e, t=round(t, 2)) for e in out["events"]]
        a = out["activity"] or {}
        rows.append((t, json.dumps(a.get("value")), out["view"], out["confidence"]))
    if trace:
        with open(trace, "w") as fh:
            fh.write("t,value,view,conf\n")
            for r in rows:
                fh.write(f"{r[0]:.3f},\"{r[1]}\",{r[2]},{r[3]}\n")
    rec = eng.stop(save=False)
    return {"events": events, "record": rec, "perf": eng.pose.session.describe()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--exercise")
    ap.add_argument("--test")
    ap.add_argument("--target", default="cpu")
    ap.add_argument("--trace")
    a = ap.parse_args(argv)
    kind, item = ("exercise", a.exercise) if a.exercise else ("assessment", a.test)
    res = run(a.video, kind, item, a.target, a.trace)
    for e in res["events"]:
        print(e)
    print(json.dumps(res["record"], indent=2)[:3000])
    print(res["perf"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
