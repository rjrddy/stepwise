"""Durable synthetic workflow; explicit JSON continuation, never arbitrary process rewind."""

from __future__ import annotations

import copy
import random
from typing import Any

from stepwise.core import Tape, canonical, digest, redact
from stepwise.store import Conflict, Store

NAMES = ["plan", "catalog.lookup", "quote.convert", "decision", "answer"]
KINDS = ["model", "tool", "tool", "model", "model"]


def input_at(seq: int, events: list[dict]) -> Any:
    if seq == 0:
        return {"task": "Quote a synthetic instrument in USD", "budget_usd": 50}
    return {"previous": events[-1]["output"]}


def response_at(seq: int, payload: Any) -> Any:
    """No model account: deliberately nondeterministic scripted model boundary."""
    if seq == 0:
        return {"action": "lookup", "phrasing": random.choice(["find", "search", "locate"])}
    if seq == 1:
        return {"sku": "SYNTH-OSC", "price_cents": 4200, "currency": "USD"}
    if seq == 2:
        # Seeded unit bug: cents were interpreted as dollars.
        return {"amount_usd": payload["previous"]["price_cents"], "divisor": 1}
    if seq == 3:
        value = payload["previous"]["amount_usd"]
        return {
            "approved": value <= 50,
            "amount_usd": value,
            "reason": "within budget" if value <= 50 else "over budget",
        }
    return {
        "message": "Approve" if payload["previous"]["approved"] else "Reject",
        "decision": payload["previous"],
    }


def advance(store: Store, rid: str, revision: int, resume: bool = False) -> dict:
    if type(revision) is not int or type(resume) is not bool:
        raise ValueError("invalid continuation")
    with store.connection() as conn:
        run = store.read_locked(conn, rid, True)
        if run["mode"] != "demo" or run["revision"] != revision:
            raise Conflict("stale revision or non-demo run")
        if run["status"] in ("done", "failed"):
            raise Conflict("terminal run")
        seq = len(run["events"])
        if run["status"] == "paused" and not resume:
            return run
        if run["breakpoint"] == seq and run["status"] != "paused":
            conn.execute("UPDATE runs SET status='paused',revision=revision+1 WHERE id=%s", (rid,))
        else:
            tape = Tape(secrets=store.secrets)
            tape.call(
                KINDS[seq],
                NAMES[seq],
                input_at(seq, run["events"]),
                lambda payload: response_at(seq, payload),
            )
            store.insert(conn, rid, seq, tape.events[0])
            conn.execute(
                "UPDATE runs SET status=%s,revision=revision+1 WHERE id=%s",
                ("done" if seq == 4 else "open", rid),
            )
        return store.read_locked(conn, rid)


def fork(store: Store, rid: str, seq: int, output: Any) -> str:
    if type(seq) is not int:
        raise ValueError("invalid frame")
    canonical(output)
    original = store.read(rid)
    if original["mode"] != "demo" or not 0 <= seq < len(original["events"]):
        raise ValueError("cannot edit frame")
    if original["events"][seq]["kind"] != "tool":
        raise ValueError("edit tool outputs only")
    # Validate the demo's continuation contract; generic SDK traces remain inspect/replay only.
    if seq == 1 and (
        not isinstance(output, dict)
        or type(output.get("price_cents")) is not int
        or not 0 <= output["price_cents"] <= 10**8
    ):
        raise ValueError("catalog output requires bounded integer price_cents")
    if seq == 2 and (
        not isinstance(output, dict)
        or type(output.get("amount_usd")) not in (int, float)
        or not 0 <= output["amount_usd"] <= 10**8
    ):
        raise ValueError("quote output requires bounded amount_usd")
    child = store.create("Edited · " + original["label"][:100], "demo", parent=rid)
    with store.connection() as conn:
        events = copy.deepcopy(original["events"][: seq + 1])
        events[-1]["output"] = redact(output, store.secrets)
        events[-1]["error"] = None
        for index, event in enumerate(events):
            store.insert(conn, child, index, event)
        conn.execute("UPDATE runs SET revision=%s WHERE id=%s", (len(events), child))
    return child


def replay(run: dict) -> dict:
    source = run["events"]
    tape = Tape(replay=source)
    for event in source:
        try:
            tape.call(
                event["kind"],
                event["name"],
                event["input"],
                lambda _: (_ for _ in ()).throw(AssertionError("provider invoked")),
            )
        except RuntimeError:
            if event["error"] is None:
                raise
    tape.finish()
    return {
        "exact": canonical(source) == canonical(tape.events),
        "frames": len(source),
        "recorded_sha256": digest(source),
        "replay_sha256": digest(tape.events),
        "provider_calls": 0,
    }


def diff(left: dict, right: dict) -> list[dict]:
    a, b = left["events"], right["events"]
    return [
        {"seq": i, "before": a[i] if i < len(a) else None, "after": b[i] if i < len(b) else None}
        for i in range(max(len(a), len(b)))
        if (a[i] if i < len(a) else None) != (b[i] if i < len(b) else None)
    ]
