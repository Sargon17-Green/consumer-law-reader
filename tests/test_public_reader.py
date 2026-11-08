from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

spec = importlib.util.spec_from_file_location("public_reader", Path(__file__).resolve().parents[1] / "scripts/verify_public_reader.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PublicReaderTests(unittest.TestCase):
    def test_real_http_bytes_are_required_and_failures_are_saved(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/correct")
                    self.end_headers()
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"exact public reader bytes" if self.path == "/correct" else b"stale CDN bytes")

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = "http://127.0.0.1:" + str(server.server_port)
            digest = hashlib.sha256(b"exact public reader bytes").hexdigest()
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "report.json"
                expected = {"schema": 1, "sourceCommit": "a" * 40,
                            "checks": [{"url": base + "/correct", "sha256": digest}]}
                self.assertTrue(module.verify(expected, output, timeout=0)["passed"])
                for path in ["/stale", "/redirect"]:
                    expected["checks"][0]["url"] = base + path
                    with self.assertRaises(RuntimeError):
                        module.verify(expected, output, timeout=0)
                    report = json.loads(output.read_text())
                    self.assertFalse(report["passed"])
                    self.assertTrue(report["errors"])
                    self.assertFalse(report["verified"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
