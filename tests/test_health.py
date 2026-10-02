"""Health and compiler tests. Signature: Mourad.Soltani"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from pathlib import Path

from noticeledger.compiler import build, check_windows, load_ledger
from noticeledger.server import make_handler
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "vendors.yaml"


class HealthTests(unittest.TestCase):
    def test_example_window_passes(self):
        ledger = load_ledger(EXAMPLE)
        findings = check_windows(ledger)
        self.assertTrue(all(item.ok for item in findings))
        self.assertEqual(len(findings), 3)

    def test_short_window_is_flagged(self):
        ledger = load_ledger(EXAMPLE)
        ledger["vendors"][0]["effective_on"] = "2026-01-10"
        findings = check_windows(ledger)
        self.assertFalse(findings[0].ok)

    def test_build_and_health_endpoint(self):
        out = ROOT / "dist-test"
        health = build(EXAMPLE, out)
        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["author"], "Mourad.Soltani")
        self.assertIn("Stripe", (out / "index.html").read_text(encoding="utf-8"))
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(out))
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health") as response:
                body = json.loads(response.read().decode())
            self.assertEqual(response.status, 200)
            self.assertEqual(body["status"], "ok")
            self.assertEqual(body["product"], "NoticeLedger")
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
