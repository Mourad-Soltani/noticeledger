"""Static server with a health route. Signature: Mourad.Soltani"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def make_handler(directory: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path == "/health":
                payload = Path(directory, "health.json")
                body = payload.read_bytes() if payload.exists() else b'{"status":"ok","author":"Mourad.Soltani"}'
                self._send(200, "application/json", body)
                return
            rel = "index.html" if path in {"", "/"} else path.lstrip("/")
            target = (directory / rel).resolve()
            if directory.resolve() not in target.parents and target != directory.resolve():
                self._send(403, "text/plain", b"forbidden")
                return
            if not target.is_file():
                self._send(404, "text/plain", b"not found")
                return
            kind = "text/html" if target.suffix == ".html" else "application/octet-stream"
            if target.suffix == ".json":
                kind = "application/json"
            if target.suffix == ".xml":
                kind = "application/rss+xml"
            self._send(200, kind, target.read_bytes())

        def log_message(self, fmt: str, *args) -> None:
            return

        def _send(self, code: int, content_type: str, body: bytes) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def serve(directory: str, port: int) -> None:
    root = Path(directory)
    server = ThreadingHTTPServer(("0.0.0.0", port), make_handler(root))
    print(json.dumps({"serving": str(root), "port": port, "author": "Mourad.Soltani"}))
    server.serve_forever()
