"""Integration test: real HTTP server + real MoveNet (CPU) + real engine."""

import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("PUNARGATI_DATA", tempfile.mkdtemp(prefix="pg-test-"))
os.environ.setdefault("PUNARGATI_LLM_URL", "http://127.0.0.1:9/v1")

from punargati import server  # noqa: E402


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server.Handler.app = server.App("cpu")
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        server.Handler.allowed_hosts = {f"127.0.0.1:{cls.port}"}
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def req(self, method, path, body=None, host=None, raw=False):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        headers = {"Host": host or f"127.0.0.1:{self.port}"}
        data = body if isinstance(body, (bytes, bytearray)) else (json.dumps(body).encode() if body is not None else None)
        c.request(method, path, body=data, headers=headers)
        r = c.getresponse()
        out = r.read()
        c.close()
        return r.status, (out if raw else json.loads(out))

    def test_library_and_system(self):
        s, lib = self.req("GET", "/api/library")
        self.assertEqual(s, 200)
        self.assertGreaterEqual(len(lib["exercises"]), 8)
        s, sysinfo = self.req("GET", "/api/system")
        self.assertEqual(sysinfo["pose"]["target"], "cpu")

    def test_rejects_foreign_host(self):
        s, _ = self.req("GET", "/api/library", host="evil.example:80", raw=True)
        self.assertEqual(s, 403)

    def test_frame_roundtrip(self):
        s, _ = self.req("POST", "/api/start", {"kind": "exercise", "id": "squat"})
        self.assertEqual(s, 200)
        px = bytes(192 * 192 * 4)
        for i in range(5):
            s, out = self.req("POST", f"/api/frame?x=0&y=-280&size=1280&w=1280&h=720&t={i / 30}", px)
            self.assertEqual(s, 200, out)
        self.assertEqual(len(out["kps"]), 23)  # 17 body + 6 feet (feet filled in precision mode)
        self.assertIn("perf", out)
        self.assertEqual(out["activity"]["id"], "squat")
        s, rec = self.req("POST", "/api/stop", {})
        self.assertFalse(rec["saved"])  # no reps on a black frame: nothing to save

    @unittest.skipUnless(any(server.ASSETS[k].present() for k in ("rtmpose-w8a16", "rtmpose-float")),
                         "RTMPose not downloaded")
    def test_precision_mode_and_heel_raise(self):
        s, st = self.req("POST", "/api/start", {"kind": "exercise", "id": "heel_raise"})
        self.assertEqual(s, 200, st)
        self.assertTrue(st["precision"])  # feet exercise switches the RTMPose cascade on
        px = bytes(288 * 288 * 4)
        s, out = self.req("POST", "/api/frame?x=0&y=-280&size=1280&w=1280&h=720&t=0.1", px)
        self.assertEqual(s, 200, out)
        self.assertTrue(out["perf"]["precision"])
        self.req("POST", "/api/stop", {})
        s, st = self.req("POST", "/api/precision", {"on": False})
        self.assertFalse(st["on"])

    def test_bad_frame_size(self):
        s, out = self.req("POST", "/api/frame?x=0&y=0&size=10&w=10&h=10&t=0", b"123")
        self.assertEqual(s, 400)

    def test_static_and_traversal(self):
        s, body = self.req("GET", "/", raw=True)
        self.assertEqual(s, 200)
        self.assertIn(b"PunarGati", body)
        s, _ = self.req("GET", "/../punargati/server.py", raw=True)
        self.assertEqual(s, 404)


if __name__ == "__main__":
    unittest.main()
