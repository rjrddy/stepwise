"""Python HTTP SDK: client-side redaction plus server-side defense in depth."""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from stepwise.core import Tape, redact


class Client:
    def __init__(self, base: str, token: str = "", secrets: tuple[str, ...] = ()) -> None:
        self.base, self.token, self.secrets = base.rstrip("/"), token, secrets

    def request(self, path: str, data: Any = None) -> Any:
        body = None if data is None else json.dumps(redact(data, self.secrets)).encode()
        request = urllib.request.Request(self.base + path, data=body, headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + self.token})
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)

    def record(self, label: str) -> tuple[str, Tape]:
        rid = self.request("/api/runs", {"label": label, "mode": "sdk"})["id"]
        seq = 0

        def sink(event: dict) -> None:
            nonlocal seq
            self.request(f"/api/runs/{rid}/events", {"seq": seq, "event": event})
            seq += 1

        return rid, Tape(sink, secrets=self.secrets)

    def replay(self, rid: str) -> Tape:
        run = self.request(f"/api/runs/{rid}")
        return Tape(replay=run["events"], secrets=self.secrets)
