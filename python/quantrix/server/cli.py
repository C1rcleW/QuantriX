"""CLI entry point for Quantrix.

Usage:
    quantrix dev     — Start development server
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(prog="quantrix", description="Quantrix CLI")
    subparsers = parser.add_subparsers(dest="command")

    # dev command
    dev_parser = subparsers.add_parser("dev", help="Start development server")
    dev_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    dev_parser.add_argument("--port", type=int, default=8532, help="Port to listen on")

    args = parser.parse_args()

    if args.command == "dev":
        import uvicorn

        uvicorn.run(
            "quantrix.server.app:app",
            host=args.host,
            port=args.port,
            reload=True,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
