"""Local JSON storage. Everything stays in ./data on this PC — no cloud, no account."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path

from .models import REPO_ROOT

DATA = Path(os.environ.get("PUNARGATI_DATA", REPO_ROOT / "data"))
_lock = threading.Lock()

DEFAULT_PROFILE = {
    "name": "", "age": None, "sex": "", "language": "en",
    "condition": "", "affected_side": "", "physio_name": "", "notes": "",
}


def _read(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def get_profile() -> dict:
    return {**DEFAULT_PROFILE, **_read(DATA / "profile.json", {})}


def set_profile(p: dict) -> dict:
    cur = get_profile()
    cur.update({k: v for k, v in p.items() if k in DEFAULT_PROFILE})
    with _lock:
        _write(DATA / "profile.json", cur)
    return cur


def get_plan() -> dict:
    return _read(DATA / "plan.json", {"items": [], "source": None, "updated": None})


def set_plan(plan: dict) -> dict:
    plan = {**plan, "updated": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with _lock:
        _write(DATA / "plan.json", plan)
    return plan


def save_session(rec: dict) -> str:
    sid = rec.get("id") or time.strftime("%Y%m%d-%H%M%S")
    rec["id"] = sid
    with _lock:
        _write(DATA / "sessions" / f"{sid}.json", rec)
    return sid


def list_sessions(limit: int = 500) -> list[dict]:
    d = DATA / "sessions"
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob("*.json"))[-limit:]:
        rec = _read(p, None)
        if rec:
            out.append(rec)
    return out


def get_session(sid: str) -> dict | None:
    if not re.fullmatch(r"[\w\-]+", sid or ""):
        return None
    return _read(DATA / "sessions" / f"{sid}.json", None)


def save_bench(rec: dict) -> None:
    with _lock:
        _write(DATA / "bench" / f"{time.strftime('%Y%m%d-%H%M%S')}.json", rec)


def latest_bench() -> dict | None:
    d = DATA / "bench"
    files = sorted(d.glob("*.json")) if d.is_dir() else []
    return _read(files[-1], None) if files else None
