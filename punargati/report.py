"""Progress aggregation and the printable report a patient hands to their physiotherapist."""

from __future__ import annotations

import html
import time

from . import store
from .assessments import TESTS
from .exercises import LIBRARY


def progress(sessions: list[dict] | None = None) -> dict:
    sessions = sessions if sessions is not None else store.list_sessions()
    series: dict[str, dict] = {}
    days: dict[str, dict] = {}
    for s in sessions:
        day = s["started"][:10]
        d = days.setdefault(day, {"date": day, "reps": 0, "sessions": 0, "quality": []})
        d["sessions"] += 1
        if s.get("kind") == "exercise":
            summ = s["summary"]
            d["reps"] += summ["reps"]
            d["quality"].append(summ["avg_quality"])
            for side, v in summ["by_side"].items():
                key = f"{s['item']}:{side}"
                ser = series.setdefault(key, {"item": s["item"], "name": s["name"], "side": side,
                                              "label": summ["rom_label"], "kind": "exercise", "points": []})
                ser["points"].append({"t": s["started"], "value": v["best_rom"], "quality": v["avg_quality"]})
        elif s.get("result"):
            r = s["result"]
            ser = series.setdefault(s["item"], {"item": s["item"], "name": s["name"], "side": None,
                                                "label": r.get("unit"), "kind": "assessment", "points": []})
            ser["points"].append({"t": s["started"], "value": r.get("score"), "flag": r.get("flag")})
    for d in days.values():
        q = d.pop("quality")
        d["avg_quality"] = round(sum(q) / len(q)) if q else None
    ordered = sorted(days)
    streak = 0
    if ordered:
        import datetime as dt
        cur = dt.date.fromisoformat(ordered[-1])
        have = set(ordered)
        while cur.isoformat() in have:
            streak += 1
            cur -= dt.timedelta(days=1)
    return {"series": list(series.values()), "days": [days[k] for k in ordered],
            "total_sessions": len(sessions), "total_reps": sum(d["reps"] for d in days.values()),
            "streak_days": streak}


def _spark(points: list[dict], w: int = 260, h: int = 60) -> str:
    vals = [p["value"] for p in points if isinstance(p.get("value"), (int, float))]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    xs = [i * (w - 10) / (len(vals) - 1) + 5 for i in range(len(vals))]
    ys = [h - 8 - (v - lo) / span * (h - 16) for v in vals]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5"/>' for x, y in zip(xs, ys))
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" class="spark">'
            f'<path d="{path}" fill="none" stroke="#0f766e" stroke-width="2"/>'
            f'<g fill="#0f766e">{dots}</g></svg>')


def render(summary_text: str | None = None) -> str:
    prof = store.get_profile()
    sessions = store.list_sessions()
    prog = progress(sessions)
    plan = store.get_plan()
    e = html.escape
    first = sessions[0]["started"][:10] if sessions else "—"
    last = sessions[-1]["started"][:10] if sessions else "—"

    rows = []
    for ser in prog["series"]:
        pts = ser["points"]
        first_v, last_v = pts[0]["value"], pts[-1]["value"]
        delta = (last_v - first_v) if isinstance(first_v, (int, float)) and isinstance(last_v, (int, float)) else None
        side = f" ({ser['side']})" if ser["side"] and ser["side"] != "both" else ""
        rows.append(
            f"<tr><td>{e(ser['name'])}{e(side)}</td><td>{e(str(ser['label']))}</td><td>{len(pts)}</td>"
            f"<td>{first_v}</td><td><b>{last_v}</b></td>"
            f"<td>{'' if delta is None else f'{delta:+.1f}'}</td><td>{_spark(pts)}</td></tr>")

    tests = [s for s in sessions if s.get("kind") == "assessment"]
    trows = "".join(
        f"<tr><td>{e(s['started'][:16].replace('T', ' '))}</td><td>{e(s['name'])}</td>"
        f"<td><b>{s['result'].get('score')}</b> {e(str(s['result'].get('unit')))}</td>"
        f"<td>{e(str(s['result'].get('flag') or ''))}</td><td>{e(s['result'].get('note') or '')}</td></tr>"
        for s in tests[-12:])

    srows = "".join(
        f"<tr><td>{e(s['started'][:16].replace('T', ' '))}</td><td>{e(s['name'])}</td>"
        f"<td>{s['summary']['reps']}</td><td>{s['summary']['avg_quality']}</td>"
        f"<td>{e(', '.join(k.replace('_', ' ') for k in s['summary']['faults']) or '—')}</td>"
        f"<td>{e(s['compute']['label'])}</td></tr>"
        for s in sessions[-20:] if s.get("kind") == "exercise")

    prow = "".join(
        f"<li>{e(LIBRARY[i['id']].name if i['id'] in LIBRARY else TESTS[i['id']]['name'])}"
        f" — {i['sets']}×{i['reps'] or ''} {e(i['side'])}, {e(i['frequency'])}</li>"
        for i in plan.get("items", []) if i["id"] in LIBRARY or i["id"] in TESTS) or "<li>No plan imported</li>"

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PunarGati progress report</title>
<style>
body{{font:14px/1.5 system-ui,Segoe UI,sans-serif;color:#0f172a;max-width:920px;margin:24px auto;padding:0 16px;background:#fff}}
h1{{font-size:22px;margin:0}} h2{{font-size:16px;margin:28px 0 8px;border-bottom:2px solid #0f766e;padding-bottom:4px}}
table{{width:100%;border-collapse:collapse;font-size:13px}} td,th{{padding:6px 8px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:middle}}
th{{background:#f1f5f9;font-weight:600}} .muted{{color:#64748b}} .kpi{{display:flex;gap:24px;margin:12px 0}}
.kpi div{{background:#f0fdfa;border:1px solid #99f6e4;border-radius:8px;padding:8px 14px}} .kpi b{{font-size:20px;display:block}}
.summary{{background:#f8fafc;border-left:4px solid #0f766e;padding:10px 14px;white-space:pre-wrap}}
.foot{{margin-top:28px;font-size:12px;color:#64748b}} @media print{{.noprint{{display:none}}}}
</style></head><body>
<button class="noprint" onclick="print()" style="float:right;padding:8px 14px">Print / Save as PDF</button>
<h1>PunarGati — home rehabilitation report</h1>
<div class="muted">Generated {time.strftime('%d %b %Y, %H:%M')} · measured on-device, no data left this PC</div>
<div class="kpi"><div><b>{e(prof.get('name') or '—')}</b>Patient</div><div><b>{e(str(prof.get('age') or '—'))}</b>Age</div>
<div><b>{e(prof.get('condition') or '—')}</b>Condition</div><div><b>{prog['total_sessions']}</b>Sessions ({first} → {last})</div>
<div><b>{prog['total_reps']}</b>Reps</div></div>
<h2>Summary</h2><div class="summary">{e(summary_text or 'No AI summary generated.')}</div>
<h2>Range of motion &amp; test trends</h2>
<table><tr><th>Exercise / test</th><th>Measure</th><th>Sessions</th><th>First</th><th>Latest</th><th>Change</th><th>Trend</th></tr>
{''.join(rows) or '<tr><td colspan=7>No sessions yet</td></tr>'}</table>
<h2>Standardised tests</h2>
<table><tr><th>When</th><th>Test</th><th>Score</th><th>Flag</th><th>Reference</th></tr>{trows or '<tr><td colspan=5>None yet</td></tr>'}</table>
<h2>Recent exercise sessions</h2>
<table><tr><th>When</th><th>Exercise</th><th>Reps</th><th>Quality</th><th>Form corrections</th><th>Computed on</th></tr>{srows or '<tr><td colspan=6>None yet</td></tr>'}</table>
<h2>Prescribed home plan</h2><ul>{prow}</ul>
<div class="foot">Angles are 2-D estimates from a single camera and can differ from a clinical goniometer, most of all when
the joint is not square to the camera; compare trends, not single readings. PunarGati is a coaching and screening aid, not a medical device; it does not diagnose.
Pose model: MoveNet via Qualcomm AI Hub, executed on the Snapdragon Hexagon NPU.</div>
</body></html>"""
