"""Command line interface. Signature: Mourad.Soltani"""

from __future__ import annotations

import argparse
import json

from noticeledger.compiler import build
from noticeledger.server import serve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="noticeledger", description="NoticeLedger by Mourad.Soltani")
    sub = parser.add_subparsers(dest="cmd", required=True)

    build_cmd = sub.add_parser("build", help="compile a vendor file")
    build_cmd.add_argument("src")
    build_cmd.add_argument("--out", default="dist")

    serve_cmd = sub.add_parser("serve", help="serve a build directory")
    serve_cmd.add_argument("directory")
    serve_cmd.add_argument("--port", type=int, default=8080)

    args = parser.parse_args(argv)
    if args.cmd == "build":
        health = build(args.src, args.out)
        print(json.dumps(health))
        return 0 if health["status"] in {"ok", "attention"} else 1
    serve(args.directory, args.port)
    return 0
