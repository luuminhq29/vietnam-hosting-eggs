#!/usr/bin/env python3
"""Vietnam Hosting Egg Catalog Search CLI & Read-Only HTTP JSON API.

Supports filtering catalog.json by category, architecture, runtime version,
operating system, status, and keyword query for Vietnam Hosting Admin Dashboard.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "catalog.json"


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def filter_eggs(
    eggs: list[dict[str, Any]],
    category: str | None = None,
    arch: str | None = None,
    version: str | None = None,
    status: str | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    q = (query or "").strip().lower()
    v_q = (version or "").strip().lower()

    for egg in eggs:
        if category and egg.get("category", "").lower() != category.lower():
            continue
        if arch and arch.lower() not in [a.lower() for a in egg.get("supported_architectures", [])]:
            continue
        if status and egg.get("status", "").lower() != status.lower():
            continue
        if v_q and not any(v_q in sv.lower() for sv in egg.get("supported_versions", [])):
            continue
        if q:
            haystack = " ".join(
                [
                    egg.get("id", ""),
                    egg.get("name", ""),
                    egg.get("description", ""),
                    egg.get("category", ""),
                    " ".join(egg.get("supported_versions", [])),
                ]
            ).lower()
            if q not in haystack:
                continue
        out.append(egg)
    return out


def serve_api(host: str, port: int) -> None:
    catalog = load_catalog()

    class CatalogHandler(BaseHTTPRequestHandler):
        def _send_json(self, code: int, payload: Any) -> None:
            body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=60")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            if parsed.path == "/healthz":
                self._send_json(200, {"status": "ok", "total_eggs": catalog["total_eggs"]})
                return
            if parsed.path in ("/", "/api/v1/eggs"):
                matched = filter_eggs(
                    catalog["eggs"],
                    category=qs.get("category", [None])[0],
                    arch=qs.get("arch", [None])[0],
                    version=qs.get("version", [None])[0],
                    status=qs.get("status", [None])[0],
                    query=qs.get("q", [None])[0],
                )
                self._send_json(
                    200,
                    {
                        "provider": catalog["provider"],
                        "total": len(matched),
                        "eggs": matched,
                    },
                )
                return
            if parsed.path.startswith("/api/v1/eggs/"):
                egg_id = parsed.path.removeprefix("/api/v1/eggs/").strip("/")
                for e in catalog["eggs"]:
                    if e["id"] == egg_id:
                        self._send_json(200, e)
                        return
                self._send_json(404, {"error": f"Egg '{egg_id}' not found"})
                return
            if parsed.path == "/api/v1/categories":
                self._send_json(200, catalog["categories"])
                return
            self._send_json(404, {"error": "Endpoint not found"})

    print(f"[VNH][CATALOG-API] Serving read-only Catalog API on http://{host}:{port}/api/v1/eggs")
    HTTPServer((host, port), CatalogHandler).serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description="Search or serve Vietnam Hosting Egg Catalog API.")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--arch", choices=("amd64", "arm64"), help="Filter by CPU architecture")
    parser.add_argument("--version", help="Filter by supported version substring")
    parser.add_argument("--status", help="Filter by status (Stable, Beta, Legacy, ...)")
    parser.add_argument("--search", "-q", help="Keyword search across id, name, description, versions")
    parser.add_argument("--serve", action="store_true", help="Start local read-only HTTP JSON API server")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8090, help="HTTP port (default 8090)")
    args = parser.parse_args()

    if args.serve:
        serve_api(args.host, args.port)
        return 0

    catalog = load_catalog()
    matched = filter_eggs(
        catalog["eggs"],
        category=args.category,
        arch=args.arch,
        version=args.version,
        status=args.status,
        query=args.search,
    )
    print(json.dumps({"count": len(matched), "eggs": matched}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
