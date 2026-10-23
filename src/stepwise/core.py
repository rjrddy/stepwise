"""JSON call tapes. Replay never invokes a provider or tool."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from collections.abc import Callable
from typing import Any

JSON = Any
MASK = "[REDACTED]"
SENSITIVE = re.compile(r"password|secret|token|authorization|api.?key|cookie", re.I)
BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]+={0,2}")


class Divergence(ValueError):
    """Call order, inputs, result kind or tape consumption did not match."""


class RecordedError(RuntimeError):
    """Replays a captured failure without executing the original callable."""


def canonical(value: JSON) -> str:
    """Strict finite JSON only; no application objects or implicit string conversions."""
    def check(item: JSON, depth: int = 0) -> None:
        if depth > 24:
            raise ValueError("JSON nesting limit")
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("non-finite number")
        if isinstance(item, dict):
            if not all(isinstance(k, str) for k in item):
                raise ValueError("JSON keys must be strings")
            for child in item.values():
                check(child, depth + 1)
        elif isinstance(item, list):
            for child in item:
                check(child, depth + 1)
        elif item is not None and not isinstance(item, (str, bool, int, float)):
            raise ValueError("JSON values only")
    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def redact(value: JSON, secrets: tuple[str, ...] = ()) -> JSON:
    canonical(value)
    if isinstance(value, dict):
        return {k: MASK if SENSITIVE.search(k) else redact(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in sorted(filter(None, secrets), key=len, reverse=True):
            value = value.replace(secret, MASK)
        return BEARER.sub("Bearer " + MASK, value)
    return value


def digest(events: list[dict]) -> str:
    return hashlib.sha256(canonical(events).encode()).hexdigest()


def validate_event(event: dict) -> None:
    if set(event) != {"kind", "name", "input", "output", "error"}:
        raise ValueError("invalid event fields")
    if event["kind"] not in ("tool", "model"):
        raise ValueError("invalid call kind")
    if not isinstance(event["name"], str) or not re.fullmatch(r"[\w.-]{1,80}", event["name"]):
        raise ValueError("invalid call name")
    if event["error"] is not None and not isinstance(event["error"], str):
        raise ValueError("error must be string or null")
    if event["error"] is not None and event["output"] is not None:
        raise ValueError("failed event cannot have output")
    if len(canonical(event).encode()) > 60_000:
        raise ValueError("event too large")


class Tape:
    """A synchronous, single-worker SDK. Wrap model and tool callables explicitly."""

    def __init__(self, sink: Callable[[dict], None] | None = None, *,
                 replay: list[dict] | None = None, secrets: tuple[str, ...] = ()) -> None:
        self.sink = sink
        self.source = copy.deepcopy(replay)
        self.secrets = secrets
        self.events: list[dict] = []
        self.cursor = 0

    def call(self, kind: str, name: str, payload: JSON, fn: Callable[[JSON], JSON]) -> JSON:
        public = redact(payload, self.secrets)
        if self.source is not None:
            if self.cursor >= len(self.source):
                raise Divergence("tape exhausted")
            event = self.source[self.cursor]
            if (kind, name, canonical(public)) != (
                event["kind"], event["name"], canonical(event["input"])
            ):
                raise Divergence(f"call mismatch at frame {self.cursor}")
            self.cursor += 1
            self.events.append(copy.deepcopy(event))
            if event["error"] is not None:
                raise RecordedError(event["error"])
            return copy.deepcopy(event["output"])
        event = {"kind": kind, "name": name, "input": public, "output": None, "error": None}
        try:
            result = fn(payload)
            event["output"] = redact(result, self.secrets)
        except Exception as exc:
            event["error"] = redact(f"{type(exc).__name__}: {exc}", self.secrets)
            validate_event(event)
            if self.sink:
                self.sink(event)
            self.events.append(copy.deepcopy(event))
            raise
        validate_event(event)
        if self.sink:
            self.sink(event)  # fail closed: persistence failure is not hidden
        self.events.append(copy.deepcopy(event))
        return result

    def finish(self) -> None:
        if self.source is not None and self.cursor != len(self.source):
            raise Divergence("unconsumed frames")
