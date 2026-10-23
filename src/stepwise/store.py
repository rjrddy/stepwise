"""Postgres is authoritative. Run-row locking serializes append and continuation."""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from stepwise.core import redact, validate_event

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
 id uuid PRIMARY KEY, label text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 mode text NOT NULL, status text NOT NULL DEFAULT 'open', parent uuid REFERENCES runs(id),
 breakpoint integer, revision integer NOT NULL DEFAULT 0,
 CHECK (status IN ('open','paused','done','failed'))
);
CREATE TABLE IF NOT EXISTS events (
 run_id uuid NOT NULL REFERENCES runs(id), seq integer NOT NULL CHECK(seq>=0),
 body jsonb NOT NULL, PRIMARY KEY(run_id,seq)
);
CREATE INDEX IF NOT EXISTS runs_created ON runs(created_at DESC);
"""


class Conflict(ValueError):
    pass


class Store:
    def __init__(self, url: str, secrets: tuple[str, ...] = ()) -> None:
        self.url = url
        self.secrets = secrets

    @contextmanager
    def connection(self):
        with psycopg.connect(self.url, row_factory=dict_row, connect_timeout=3,
                             options="-c statement_timeout=5000 -c lock_timeout=2000") as conn:
            yield conn

    def migrate(self) -> None:
        with self.connection() as conn:
            conn.execute(SCHEMA)

    def create(self, label: str, mode: str = "sdk", breakpoint: int | None = None,
               parent: str | None = None) -> str:
        if not isinstance(label, str) or not 1 <= len(label) <= 120:
            raise ValueError("label length")
        if mode not in ("sdk", "demo"):
            raise ValueError("invalid mode")
        if breakpoint is not None and (type(breakpoint) is not int or not 0 <= breakpoint < 5):
            raise ValueError("invalid breakpoint")
        rid = str(uuid.uuid4())
        with self.connection() as conn:
            conn.execute("INSERT INTO runs(id,label,mode,breakpoint,parent) VALUES(%s,%s,%s,%s,%s)",
                         (rid, redact(label, self.secrets), mode, breakpoint, parent))
        return rid

    def list(self) -> list[dict]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT 100").fetchall()
        return [self.public(row) for row in rows]

    @staticmethod
    def public(row: dict) -> dict:
        return {k: str(v) if k in ("id", "parent", "created_at") and v is not None else v
                for k, v in row.items()}

    @staticmethod
    def read_locked(conn, rid: str, lock: bool = False) -> dict:
        row = conn.execute("SELECT * FROM runs WHERE id=%s" + (" FOR UPDATE" if lock else ""),
                           (rid,)).fetchone()
        if row is None:
            raise KeyError("run not found")
        events = conn.execute("SELECT body FROM events WHERE run_id=%s ORDER BY seq", (rid,))
        return {**Store.public(row), "events": [e["body"] for e in events]}

    def read(self, rid: str) -> dict:
        with self.connection() as conn:
            # Lock also on read: no mixed metadata/events view during a concurrent append.
            return self.read_locked(conn, rid, True)

    def insert(self, conn, rid: str, seq: int, event: dict) -> None:
        validate_event(event)
        public = redact(event, self.secrets)
        conn.execute("INSERT INTO events(run_id,seq,body) VALUES(%s,%s,%s)",
                     (rid, seq, Jsonb(public)))

    def append(self, rid: str, seq: int, event: dict) -> dict:
        if type(seq) is not int or not 0 <= seq < 1000:
            raise ValueError("invalid sequence")
        with self.connection() as conn:
            run = self.read_locked(conn, rid, True)
            if run["mode"] != "sdk" or run["status"] != "open":
                raise Conflict("run does not accept SDK events")
            public = redact(event, self.secrets)
            if seq < len(run["events"]) and run["events"][seq] == public:
                return {"seq": seq, "duplicate": True}
            if seq != len(run["events"]):
                raise Conflict("sequence conflict")
            self.insert(conn, rid, seq, public)
            conn.execute("UPDATE runs SET revision=revision+1 WHERE id=%s", (rid,))
        return {"seq": seq, "duplicate": False}


def configured() -> Store:
    return Store(os.environ["DATABASE_URL"],
                 tuple(filter(None, os.getenv("STEPWISE_SECRETS", "").split("|"))))
