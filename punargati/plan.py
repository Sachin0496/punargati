"""Turn a physiotherapist's free-text prescription into a structured home plan.

The local LLM does the reading when available (JSON-constrained, validated
against the exercise library); a rule-based parser handles the common
"3 x 10 mini squats, right knee" phrasing either way, so importing a plan
never depends on the LLM being up.
"""

from __future__ import annotations

import json
import re

from .assessments import TESTS
from .exercises import LIBRARY
from .llm import SYSTEM, llm

SYNONYMS = [
    ("chair_stand_30s", r"(30[\s-]*s(ec(ond)?)?\s*)?chair[\s-]*stand(s)?\s*test|30[\s-]*s(ec(ond)?)?\s*chair"),
    ("single_leg_stance", r"single[\s-]*leg\s*(stance|balance|stand)|one[\s-]*leg\s*(stand|balance)|balance\s*test"),
    ("rom_shoulder_flexion", r"shoulder\s*flexion\s*(rom|range)|measure\s*shoulder"),
    ("rom_knee_flexion", r"knee\s*(flexion|bend)\s*(rom|range)|measure\s*knee"),
    ("sit_to_stand", r"sit[\s-]*to[\s-]*stand|chair\s*rise|\bsts\b|chair\s*stands?"),
    ("knee_extension", r"knee\s*extension|long[\s-]*arc\s*quad|\blaq\b|seated\s*knee|quad(ricep)?s?\s*extension"),
    ("squat", r"(mini|half|wall|partial)?[\s-]*squats?"),
    ("shoulder_flexion", r"shoulder\s*flexion|forward\s*(raise|elevation)|front\s*raise|arm\s*raise"),
    ("shoulder_abduction", r"shoulder\s*abduction|side\s*raise|lateral\s*raise|arms?\s*(lifts?|raises?)\s*(sideways|to\s*the\s*side)|sideways\s*arm"),
    ("elbow_curl", r"elbow\s*(flexion|bend)|bicep(s)?\s*curl|\bcurls?\b"),
    ("hip_abduction", r"hip\s*abduction|side\s*leg\s*raise|leg\s*raise\s*to\s*(the\s*)?side|standing\s*abduction"),
    ("marching", r"march(ing)?|knee\s*raise|hip\s*flexion"),
]
FREQ = [
    (r"thrice|three\s*times\s*(a|per)\s*day|3\s*(x|times)\s*(a|per|/)\s*day", "3x daily"),
    (r"twice\s*(a|per)\s*day|two\s*times\s*(a|per)\s*day|2\s*(x|times)\s*(a|per|/)\s*day|bd\b|bid\b", "2x daily"),
    (r"weekly|once\s*a\s*week|every\s*week", "weekly"),
    (r"alternate\s*days|every\s*other\s*day", "alternate days"),
    (r"daily|every\s*day|once\s*a\s*day|od\b", "daily"),
]


def _ident(chunk: str) -> str | None:
    for item, pat in SYNONYMS:
        if re.search(pat, chunk, re.I):
            return item
    return None


def parse_rules(text: str) -> list[dict]:
    items = []
    for raw in re.split(r"[\n;]|(?<=[a-z])\.\s+|\s+then\s+", text or "", flags=re.I):
        chunk = raw.strip(" -•*\t")
        if not chunk:
            continue
        item = _ident(chunk)
        if not item:
            continue
        sets, reps = 1, None
        m = re.search(r"(\d+)\s*[x×*]\s*(\d+)", chunk)
        if m:
            sets, reps = int(m.group(1)), int(m.group(2))
        else:
            m = re.search(r"(\d+)\s*sets?\s*(of\s*)?(\d+)?", chunk, re.I)
            if m:
                sets = int(m.group(1))
                if m.group(3):
                    reps = int(m.group(3))
            m2 = re.search(r"(\d+)\s*(reps?|repetitions|times)(?!\s*(a|per)\s*day)", chunk, re.I)
            if m2:
                reps = int(m2.group(1))
        side = "auto"
        if re.search(r"\bleft\b|\(l\)|\bl\s*(knee|shoulder|leg|arm)", chunk, re.I):
            side = "left"
        if re.search(r"\bright\b|\(r\)|\br\s*(knee|shoulder|leg|arm)", chunk, re.I):
            side = "both" if side == "left" else "right"
        freq = next((f for pat, f in FREQ if re.search(pat, chunk, re.I)), "daily")
        kind = "assessment" if item in TESTS else "exercise"
        items.append({"kind": kind, "id": item, "sets": sets if kind == "exercise" else 1,
                      "reps": (reps or 10) if kind == "exercise" else None,
                      "side": side, "frequency": freq, "note": chunk[:160]})
    return items


def _validate(items) -> list[dict]:
    out = []
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        iid = str(it.get("id", ""))
        if iid not in LIBRARY and iid not in TESTS:
            continue
        kind = "assessment" if iid in TESTS else "exercise"
        try:
            sets = max(1, min(10, int(it.get("sets") or 1)))
            reps = None if kind == "assessment" else max(1, min(50, int(it.get("reps") or 10)))
        except (TypeError, ValueError):
            continue
        side = it.get("side") if it.get("side") in ("left", "right", "both", "auto") else "auto"
        out.append({"kind": kind, "id": iid, "sets": sets, "reps": reps, "side": side,
                    "frequency": str(it.get("frequency") or "daily")[:40],
                    "note": str(it.get("note") or "")[:160]})
    return out


def parse(text: str) -> dict:
    """Rules give exact doses for the phrasings they recognise; the LLM adds anything
    they missed (unusual wording, Hinglish, abbreviations). Rules win on conflicts."""
    rules = parse_rules(text)
    catalog = ", ".join(list(LIBRARY) + list(TESTS))
    try:
        prompt = (
            "Convert this physiotherapy home-exercise prescription into JSON. Only use these ids: "
            f"{catalog}. Output {{\"items\": [{{\"id\", \"sets\", \"reps\", \"side\" (left|right|both|auto), "
            "\"frequency\", \"note\"}]}}. Use side \"auto\" unless a side is written. "
            "Skip anything that doesn't map to an id.\n\nPrescription:\n" + text
        )
        raw = llm.chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                       600, 0.0, json_mode=True)
        m = re.search(r"\{.*\}", raw, re.S)
        extra = _validate(json.loads(m.group(0)).get("items")) if m else []
        have = {i["id"] for i in rules}
        added = [i for i in extra if i["id"] not in have]
        if added or not rules:
            return {"items": rules + added, "source": "rules+llm" if rules else "llm",
                    "model": llm.status()["model"]}
        return {"items": rules, "source": "rules (LLM agreed)", "model": llm.status()["model"]}
    except Exception:
        pass
    return {"items": rules, "source": "rules"}
