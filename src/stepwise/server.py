"""Small bounded same-origin HTTP service; no request bodies in access logs."""

from __future__ import annotations

import hmac
import json
import os
import re
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import psycopg

from stepwise.core import canonical
from stepwise.store import Conflict, Store, configured
from stepwise.workflow import advance, diff, fork, replay

WEB = Path(__file__).resolve().parents[2] / "apps/web/dist"


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 32

    def __init__(self, addr: tuple[str, int], store: Store, token: str = "") -> None:
        super().__init__(addr, Handler)
        self.store, self.token = store, token


class Handler(BaseHTTPRequestHandler):
    server: Server

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, fmt: str, *args) -> None:
        pass  # No raw URL/query, token, payload, or exception data in logs.

    def send(self, code: int, data: bytes, content_type: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; "
            "script-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(data)

    def dispatch(self, post: bool) -> None:
        try:
            path = urlsplit(self.path).path
            if not path.startswith("/api/"):
                if post:
                    raise KeyError()
                candidate = (WEB / path.lstrip("/")).resolve()
                if not candidate.is_relative_to(WEB.resolve()):
                    raise KeyError()
                if not candidate.is_file():
                    candidate = WEB / "index.html"
                suffix = candidate.suffix
                mime = {
                    ".html": "text/html; charset=utf-8",
                    ".js": "text/javascript",
                    ".css": "text/css",
                    ".svg": "image/svg+xml",
                }.get(suffix)
                if not mime:
                    raise KeyError()
                self.send(200, candidate.read_bytes(), mime)
                return
            if (
                path != "/api/health"
                and self.server.token
                and not hmac.compare_digest(
                    self.headers.get("Authorization", ""), "Bearer " + self.server.token
                )
            ):
                self.send(401, b'{"error":"authentication required"}')
                return
            origin = self.headers.get("Origin")
            if origin and urlsplit(origin).netloc != self.headers.get("Host"):
                self.send(403, b'{"error":"origin rejected"}')
                return
            data = {}
            if post:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 65536:
                    self.send(413, b'{"error":"body limit"}')
                    return
                data = json.loads(self.rfile.read(length))
                canonical(data)
                if not isinstance(data, dict):
                    raise ValueError()
            result = self.route(path, post, data)
            self.send(200, canonical(result).encode())
            print(
                json.dumps(
                    {"event": "http", "status": 200, "operation": "write" if post else "read"}
                ),
                flush=True,
            )
        except Conflict:
            self.send(409, b'{"error":"revision or sequence conflict"}')
        except (ValueError, TypeError, IndexError, RecursionError):
            self.send(400, b'{"error":"invalid request"}')
        except (KeyError, FileNotFoundError):
            self.send(404, b'{"error":"not found"}')
        except psycopg.Error:
            self.send(503, b'{"error":"trace store unavailable"}')
        except Exception:
            self.send(500, b'{"error":"internal error"}')

    def route(self, path: str, post: bool, data: dict) -> dict | list:
        store = self.server.store
        if path == "/api/health" and not post:
            with store.connection() as conn:
                conn.execute("SELECT 1")
            return {"status": "ready"}
        if path == "/api/runs":
            if post:
                return {
                    "id": store.create(
                        data.get("label", "Untitled"),
                        data.get("mode", "demo"),
                        data.get("breakpoint"),
                    )
                }
            return store.list()
        match = re.fullmatch(
            r"/api/runs/([0-9a-f-]{36})(?:/(events|advance|fork|replay|diff))?", path
        )
        if not match:
            raise KeyError()
        rid, action = match.groups()
        uuid.UUID(rid)
        if not post and action is None:
            return store.read(rid)
        if not post:
            raise KeyError()
        if action == "events":
            return store.append(rid, data["seq"], data["event"])
        if action == "advance":
            return advance(store, rid, data["revision"], data.get("resume", False))
        if action == "fork":
            return {"id": fork(store, rid, data["seq"], data["output"])}
        if action == "replay":
            return replay(store.read(rid))
        if action == "diff":
            uuid.UUID(data["other"])
            return {"changes": diff(store.read(rid), store.read(data["other"]))}
        raise KeyError()

    def do_GET(self) -> None:
        self.dispatch(False)

    def do_POST(self) -> None:
        self.dispatch(True)


def main() -> None:
    store = configured()
    store.migrate()
    host, port = os.getenv("HOST", "127.0.0.1"), int(os.getenv("PORT", "8091"))
    token = os.getenv("STEPWISE_TOKEN", "")
    if host not in ("127.0.0.1", "localhost") and len(token) < 24:
        raise ValueError("non-loopback binding requires STEPWISE_TOKEN of at least 24 characters")
    server = Server((host, port), store, token)
    print(json.dumps({"event": "ready", "url": f"http://{host}:{server.server_port}"}), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
