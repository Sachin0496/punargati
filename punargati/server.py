"""Local web server: the browser does camera + UI, Python does all the AI.

Binds to 127.0.0.1 only and rejects foreign Host headers (DNS-rebinding
guard), so video frames and health data never leave the machine.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import threading
import time
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import bench, llm as llm_mod, plan as plan_mod, report, runtime, store
from .assessments import TESTS
from .engine import Engine
from .exercises import LIBRARY
from .models import ASSETS, REPO_ROOT, status as model_status
from .pose import INPUT, Crop

log = logging.getLogger("punargati.server")
# Windows maps extensions via the registry, which often serves .js as text/plain and
# breaks ES modules; pin the types we ship.
for _ext, _type in {".js": "text/javascript", ".css": "text/css", ".html": "text/html", ".svg": "image/svg+xml",
                    ".webm": "video/webm", ".mp4": "video/mp4", ".json": "application/json", ".png": "image/png"}.items():
    mimetypes.add_type(_type, _ext)
WEB = REPO_ROOT / "web"
FRAME_BYTES = INPUT * INPUT * 4


_seen_errors: set = set()


def _log_once(e: Exception) -> None:
    """Per-frame endpoints can fail 30x/s; print each distinct error once."""
    key = f"{type(e).__name__}:{e}"
    if key not in _seen_errors:
        _seen_errors.add(key)
        traceback.print_exc()


class App:
    def __init__(self, target: str, perf_mode: str = "burst"):
        self.target_requested = target
        self.engine = Engine(target, perf_mode)
        self.bench_lock = threading.Lock()
        self.bench_running = False

    def system(self) -> dict:
        return {
            "machine": runtime.machine_info(),
            "targets": runtime.available_targets(),
            "pose": self.engine.pose.session.describe(),
            "load_errors": getattr(self.engine.pose, "load_errors", []),
            "models": model_status(),
            "llm": llm_mod.llm.status(),
            "precision": self.engine.precision_status(),
            "wholebody_available": any(ASSETS[k].present() for k in ("rtmpose-w8a16", "rtmpose-float")),
        }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    app: App = None  # set by serve()
    allowed_hosts: set = set()

    def log_message(self, fmt, *args):  # quiet: per-frame POSTs would flood the console
        pass

    # -- helpers --------------------------------------------------------------
    def _host_ok(self) -> bool:
        return (self.headers.get("Host") or "") in self.allowed_hosts

    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _body(self) -> bytes:
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _jbody(self) -> dict:
        b = self._body()
        return json.loads(b) if b else {}

    # -- routing --------------------------------------------------------------
    def do_GET(self):
        if not self._host_ok():
            return self._send(403, b"forbidden host", "text/plain")
        url = urllib.parse.urlparse(self.path)
        p = url.path
        try:
            if p == "/api/system":
                return self._json(self.app.system())
            if p == "/api/library":
                return self._json({"exercises": [e.public() for e in LIBRARY.values()],
                                   "tests": [{"id": k, **v} for k, v in TESTS.items()]})
            if p == "/api/profile":
                return self._json(store.get_profile())
            if p == "/api/plan":
                return self._json(store.get_plan())
            if p == "/api/sessions":
                return self._json(store.list_sessions()[::-1][:100])
            if p == "/api/progress":
                return self._json(report.progress())
            if p == "/api/bench":
                return self._json(store.latest_bench() or {})
            if p == "/api/llm/status":
                return self._json(llm_mod.llm.status(refresh=True))
            if p == "/report":
                q = urllib.parse.parse_qs(url.query)
                text = None
                if q.get("ai") == ["1"]:
                    sess = store.list_sessions()
                    if sess:
                        text = llm_mod.summarize(sess[-1], sess, store.get_profile().get("language", "en"))["text"]
                return self._send(200, report.render(text).encode("utf-8"), "text/html; charset=utf-8")
            return self._static(p)
        except Exception as e:
            _log_once(e)
            return self._json({"error": str(e)}, 500)

    def _static(self, p: str):
        rel = "index.html" if p in ("/", "") else p.lstrip("/")
        f = (WEB / rel).resolve()
        if WEB.resolve() not in f.parents and f != WEB.resolve() or not f.is_file():
            return self._send(404, b"not found", "text/plain")
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript",):
            ctype += "; charset=utf-8"
        return self._send(200, f.read_bytes(), ctype)

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, b"forbidden host", "text/plain")
        url = urllib.parse.urlparse(self.path)
        p = url.path
        eng = self.app.engine
        # Always drain the body: an unread body on a keep-alive connection is parsed
        # as the start of the next request.
        body = self._body()
        self._jbody = lambda: json.loads(body) if body else {}
        try:
            if p == "/api/frame":
                q = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}
                n = int(round((len(body) / 4) ** 0.5))
                if n * n * 4 != len(body) or not 128 <= n <= 512:
                    return self._json({"error": f"expected a square RGBA crop (e.g. {FRAME_BYTES} bytes), got {len(body)}"}, 400)
                crop = Crop(float(q["x"]), float(q["y"]), float(q["size"]))
                out = eng.process(body, crop, int(q["w"]), int(q["h"]), float(q["t"]))
                return self._json(out)
            if p == "/api/start":
                b = self._jbody()
                return self._json(eng.start(b["kind"], b["id"], b.get("side", "auto"), b.get("target_reps", 10)))
            if p == "/api/stop":
                return self._json(eng.stop() or {"saved": False})
            if p == "/api/precision":
                return self._json(eng.set_precision(bool(self._jbody().get("on"))))
            if p == "/api/compute":
                return self._json(eng.set_target(self._jbody().get("target", "npu")))
            if p == "/api/profile":
                return self._json(store.set_profile(self._jbody()))
            if p == "/api/plan":
                return self._json(store.set_plan(self._jbody()))
            if p == "/api/plan/parse":
                return self._json(plan_mod.parse(self._jbody().get("text", "")))
            if p == "/api/summary":
                b = self._jbody()
                sess = store.list_sessions()
                rec = store.get_session(b["id"]) if b.get("id") else (sess[-1] if sess else None)
                if not rec:
                    return self._json({"text": "No sessions yet.", "source": "template"})
                lang = b.get("lang") or store.get_profile().get("language", "en")
                return self._json(llm_mod.summarize(rec, sess, lang))
            if p == "/api/chat":
                b = self._jbody()
                lang = b.get("lang") or store.get_profile().get("language", "en")
                return self._json(llm_mod.coach_chat(b.get("message", ""), store.list_sessions(), lang))
            if p == "/api/bench":
                return self._run_bench(self._jbody())
            return self._json({"error": "not found"}, 404)
        except KeyError as e:
            return self._json({"error": f"missing field {e}"}, 400)
        except Exception as e:
            _log_once(e)
            return self._json({"error": str(e)}, 500)

    def _run_bench(self, b: dict):
        with self.app.bench_lock:
            if self.app.bench_running:
                return self._json({"error": "benchmark already running"}, 409)
            self.app.bench_running = True
        try:
            secs = max(3.0, min(30.0, float(b.get("seconds", 8))))
            return self._json(bench.run(secs, b.get("targets")))
        finally:
            self.app.bench_running = False


def serve(host: str = "127.0.0.1", port: int = 8765, target: str = "npu", open_browser: bool = True,
          perf_mode: str = "burst"):
    app = App(target, perf_mode)
    Handler.app = app
    Handler.allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
    if host not in ("127.0.0.1", "localhost", "::1"):
        Handler.allowed_hosts.add(f"{host}:{port}")
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    pose = app.engine.pose.session.describe()
    url = f"http://127.0.0.1:{port}/"
    print("\n  PunarGati — on-device AI rehab coach")
    print(f"  pose model : {pose['model']} on {pose['label']}"
          f"{' (100% of ops on accelerator)' if pose['full_offload'] else ''}  [{pose['compile_s']} s load]")
    for err in getattr(app.engine.pose, "load_errors", []):
        print(f"  note       : {err[:160]}")
    st = llm_mod.llm.status(refresh=True)
    print(f"  local LLM  : {st['model'] + ' @ ' + st['base'] if st['available'] else 'not running (template coach active)'}")
    print(f"  open       : {url}\n")
    if open_browser:
        import webbrowser
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
