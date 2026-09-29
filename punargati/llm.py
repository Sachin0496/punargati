"""Local LLM coach over any OpenAI-compatible server running on this PC.

Works with llama.cpp ``llama-server`` (Qwen3-4B Q4_0 from Qualcomm AI Hub's
release assets), GenieX / QAIRT NPU servers, Foundry Local, LM Studio or
Ollama. Nothing is sent off the machine: only loopback URLs are probed, and a
non-loopback URL must be opted into explicitly.

Every LLM feature has a deterministic fallback, so the app is fully usable
(and the demo can't break) with no LLM running.
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

LANG_NAMES = {"en": "English", "hi": "Hindi", "ta": "Tamil", "te": "Telugu",
              "kn": "Kannada", "mr": "Marathi", "bn": "Bengali"}

CANDIDATES = [
    "http://127.0.0.1:8080/v1",   # llama-server / GenieX default
    "http://127.0.0.1:8081/v1",   # QAIRT NPU server (Gaja-style)
    "http://127.0.0.1:1234/v1",   # LM Studio
    "http://127.0.0.1:11434/v1",  # Ollama
    "http://127.0.0.1:5272/v1",   # Foundry Local
    "http://127.0.0.1:5273/v1",
]

SYSTEM = (
    "You are PunarGati, a friendly rehabilitation coach that runs entirely on the user's own "
    "Snapdragon PC. You explain exercise data measured by on-device pose tracking. Rules: be "
    "encouraging and concrete; never diagnose; never change the physiotherapist's prescription; "
    "if the user mentions sharp pain, swelling, numbness, chest pain, dizziness or a fall, tell them "
    "to stop and contact their physiotherapist or doctor. Keep answers short and in plain language."
)


def _is_local(url: str) -> bool:
    host = urllib.parse.urlparse(url).hostname or ""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class LocalLLM:
    def __init__(self):
        self.base = os.environ.get("PUNARGATI_LLM_URL")
        self.model = os.environ.get("PUNARGATI_LLM_MODEL")
        self.allow_remote = os.environ.get("PUNARGATI_LLM_ALLOW_REMOTE") == "1"
        self._status = None
        self._checked = 0.0

    def _get(self, url: str, timeout: float = 1.5) -> dict:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())

    def status(self, refresh: bool = False) -> dict:
        if not refresh and self._status and time.time() - self._checked < 30:
            return self._status
        bases = [self.base] if self.base else CANDIDATES
        st = {"available": False, "base": None, "model": None, "local": True}
        for b in bases:
            if not b:
                continue
            if not _is_local(b) and not self.allow_remote:
                st["error"] = f"{b} is not a loopback address; set PUNARGATI_LLM_ALLOW_REMOTE=1 to allow"
                continue
            try:
                data = self._get(b.rstrip("/") + "/models")
                ids = [m.get("id") for m in data.get("data", []) if m.get("id")]
                st = {"available": True, "base": b.rstrip("/"), "model": self.model or (ids[0] if ids else "local"),
                      "models": ids[:10], "local": _is_local(b)}
                break
            except Exception:
                continue
        self._status, self._checked = st, time.time()
        return st

    def chat(self, messages: list[dict], max_tokens: int = 400, temperature: float = 0.3,
             json_mode: bool = False) -> str:
        st = self.status()
        if not st["available"]:
            raise RuntimeError("no local LLM server found")
        body = {
            "model": st["model"], "messages": messages, "max_tokens": max_tokens,
            "temperature": temperature, "stream": False,
            # Qwen3 / Gemma thinking templates burn the token budget on hidden reasoning.
            "chat_template_kwargs": {"enable_thinking": False},
            "frequency_penalty": 0.3, "repeat_penalty": 1.12,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(
            st["base"] + "/chat/completions", data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"})
        t = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            if json_mode and e.code in (400, 422):  # server without response_format support
                return self.chat(messages, max_tokens, temperature, json_mode=False)
            raise
        self.last_latency_s = round(time.perf_counter() - t, 2)
        self.last_usage = data.get("usage")
        text = data["choices"][0]["message"].get("content") or ""
        return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


llm = LocalLLM()


def degenerate(text: str) -> bool:
    """Small models sometimes loop in Indic scripts; detect repeated 3-grams."""
    w = text.split()
    if len(w) < 18:
        return False
    grams: dict = {}
    for g in zip(w, w[1:], w[2:]):
        grams[g] = grams.get(g, 0) + 1
    return max(grams.values()) >= 4


# ---------------------------------------------------------------- summaries --
def _fmt_session(rec: dict) -> str:
    if rec.get("kind") == "exercise":
        s = rec["summary"]
        unit = "%" if "%" in s["rom_label"] else "°"
        sides = "; ".join(f"{k}: {v['reps']} reps, best {s['rom_label'].lower()} {v['best_rom']}{unit}, "
                          f"quality {v['avg_quality']}/100" for k, v in s["by_side"].items())
        faults = ", ".join(f"{k.replace('_', ' ')} x{v}" for k, v in s["faults"].items()) or "none"
        return f"{rec['started'][:10]} {s['name']}: {sides}. Form corrections: {faults}."
    r = rec.get("result", {})
    return f"{rec['started'][:10]} {rec['name']}: {r.get('score')} {r.get('unit')} ({r.get('flag')})."


def template_summary(rec: dict, history: list[dict]) -> str:
    """Deterministic, data-grounded summary used when no LLM is running."""
    line = _fmt_session(rec)
    trend = ""
    same = [h for h in history if h.get("item") == rec.get("item") and h.get("id") != rec.get("id")]
    if same and rec.get("kind") == "exercise":
        prev = same[-1]["summary"]
        cur = rec["summary"]
        pb = max((v["best_rom"] for v in prev["by_side"].values()), default=0)
        cb = max((v["best_rom"] for v in cur["by_side"].values()), default=0)
        if cb and pb:
            d = round(cb - pb, 1)
            u = "%" if "%" in cur["rom_label"] else "°"
            trend = (f" Your best range changed by {d:+}{u} since {same[-1]['started'][:10]}."
                     if d else " Your range matched last time.")
    elif same and rec.get("kind") == "assessment":
        d = (rec["result"].get("score") or 0) - (same[-1]["result"].get("score") or 0)
        trend = f" That is {d:+} compared with {same[-1]['started'][:10]}."
    advice = ""
    if rec.get("kind") == "exercise":
        f = rec["summary"]["faults"]
        if f:
            top = max(f, key=f.get).replace("_", " ")
            advice = f" Focus next time: {top}."
        else:
            advice = " Form was clean — keep the same slow, controlled tempo."
    return line + trend + advice


def facts(rec: dict, history: list[dict]) -> dict:
    """Numbers the UI turns into a localized, deterministic summary (no LLM needed)."""
    same = [h for h in history if h.get("item") == rec.get("item") and h.get("id") != rec.get("id")
            and h.get("started", "") < rec.get("started", "")]
    f = {"kind": rec.get("kind"), "name": rec.get("name")}
    if rec.get("kind") == "exercise":
        s = rec["summary"]
        best = max((v["best_rom"] for v in s["by_side"].values()), default=None)
        f.update(reps=s["reps"], quality=s["avg_quality"], best=best, rom_label=s["rom_label"],
                 top_fault=max(s["faults"], key=s["faults"].get) if s["faults"] else None)
        if same and best is not None:
            pb = max((v["best_rom"] for v in same[-1]["summary"]["by_side"].values()), default=None)
            if pb is not None:
                d = round(best - pb, 1)
                # knee extension is reported as degrees short of straight: lower is better
                f["delta"] = -d if rec.get("item") == "knee_extension" else d
                f["prev_date"] = same[-1]["started"][:10]
    else:
        r = rec.get("result", {})
        f.update(score=r.get("score"), unit=r.get("unit"), flag=r.get("flag"))
        if same:
            f["delta"] = round((r.get("score") or 0) - (same[-1]["result"].get("score") or 0), 1)
            f["prev_date"] = same[-1]["started"][:10]
    return f


def summarize(rec: dict, history: list[dict], lang: str = "en") -> dict:
    """English narrative from the local LLM (template fallback) + structured facts.

    Small on-device models write fluent English but unreliable Indic prose, so by
    default the patient-language summary is composed from ``facts`` with vetted
    translations; set PUNARGATI_LLM_INDIC=1 to let a capable model write it directly.
    """
    out = {"facts": facts(rec, history), "lang": lang}
    llm_lang = lang if os.environ.get("PUNARGATI_LLM_INDIC") == "1" else "en"
    try:
        hist = "\n".join(_fmt_session(h) for h in history[-8:] if h.get("id") != rec.get("id"))
        prompt = (
            f"Today's session (measured on-device):\n{_fmt_session(rec)}\n\n"
            f"Earlier sessions:\n{hist or 'none'}\n\n"
            f"Write a 3-4 sentence summary for the patient in {LANG_NAMES.get(llm_lang, 'English')}: what went well, "
            "the trend, and one specific thing to focus on next time. Use the numbers. No headings."
        )
        text = llm.chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}], 300)
        if text and not degenerate(text):
            out.update(text=text, text_lang=llm_lang, source="llm", model=llm.status()["model"],
                       latency_s=getattr(llm, "last_latency_s", None))
            return out
    except Exception as e:
        out["note"] = str(e)[:200]
    out.update(text=template_summary(rec, history), text_lang="en", source="template")
    return out


RED_FLAGS = re.compile(
    r"\b(sharp pain|severe pain|swell|swollen|numb|tingl|chest pain|dizz|faint|fell|fall|bleed|fever|"
    r"can'?t breathe|breathless|popping sound|gave way)\b", re.I)


def coach_chat(question: str, context: list[dict], lang: str = "en") -> dict:
    if RED_FLAGS.search(question or ""):
        safety = ("Please stop exercising for now. What you describe should be checked by your "
                  "physiotherapist or doctor before you continue. If it is severe or sudden, seek "
                  "medical care immediately.")
    else:
        safety = None
    try:
        ctx = "\n".join(_fmt_session(h) for h in context[-10:]) or "no sessions yet"
        msgs = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"My recent measured sessions:\n{ctx}\n\nQuestion: {question}\n"
                                         f"Answer in {LANG_NAMES.get(lang, 'English')} in under 120 words."},
        ]
        text = llm.chat(msgs, 350)
        if safety and safety.split(".")[0].lower() not in text.lower():
            text = safety + "\n\n" + text
        return {"text": text, "source": "llm", "model": llm.status()["model"],
                "latency_s": getattr(llm, "last_latency_s", None)}
    except Exception as e:
        base = safety or ("The local AI coach isn't running, so here is your data instead:\n" +
                          ("\n".join(_fmt_session(h) for h in context[-3:]) or "No sessions recorded yet."))
        return {"text": base, "source": "template", "note": str(e)[:200]}
