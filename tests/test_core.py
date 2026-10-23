from __future__ import annotations

import json
import random
from concurrent.futures import ThreadPoolExecutor

import pytest

from stepwise.core import Divergence, RecordedError, Tape, canonical, digest, redact
from stepwise.store import Conflict, configured
from stepwise.workflow import advance, diff, fork, replay


@pytest.fixture
def store():
    value = configured()
    value.secrets = ("SYNTHETIC-NEVER-PERSIST-KEY",)
    value.migrate()
    return value


def complete(store, rid):
    while (run := store.read(rid))["status"] != "done":
        advance(store, rid, run["revision"], resume=True)
    return store.read(rid)


def test_capture_replay_property():
    rng = random.Random(7301)
    for _ in range(200):
        tape = Tape()
        values = [{"x": rng.randrange(10000), "label": "synthetic"} for _ in range(rng.randrange(1, 20))]
        for item in values:
            tape.call("tool", "lookup", item, lambda p: {"v": p["x"] + rng.random()})
        restored = Tape(replay=tape.events)
        for item, event in zip(values, tape.events, strict=True):
            assert restored.call("tool", "lookup", item, lambda _: pytest.fail("side effect")) == event["output"]
        restored.finish()
        assert canonical(tape.events) == canonical(restored.events)
        assert digest(tape.events) == digest(restored.events)


def test_divergence_and_aliasing():
    tape = Tape()
    tape.call("model", "plan", {"x": 1}, lambda _: {"a": [1]})
    replayed = Tape(replay=tape.events)
    with pytest.raises(Divergence, match="mismatch"):
        replayed.call("tool", "plan", {"x": 1}, lambda _: None)
    with pytest.raises(Divergence, match="unconsumed"):
        replayed.finish()
    result = replayed.call("model", "plan", {"x": 1}, lambda _: None)
    result["a"].append(2)
    assert tape.events[0]["output"] == {"a": [1]}
    with pytest.raises(Divergence, match="exhausted"):
        replayed.call("model", "plan", {}, lambda _: None)


def test_redaction_failure_and_sink():
    key = "SYNTHETIC-NEVER-PERSIST-KEY"
    tape = Tape(secrets=(key,))
    with pytest.raises(ValueError):
        tape.call("tool", "failure", {"nested": [{"api_key": key}], "q": key},
                  lambda _: (_ for _ in ()).throw(ValueError("Bearer " + key)))
    assert key not in canonical(tape.events)
    with pytest.raises(RecordedError):
        Tape(replay=tape.events, secrets=(key,)).call(
            "tool", "failure", {"nested": [{"api_key": key}], "q": key}, lambda _: None)
    broken = Tape(lambda _: (_ for _ in ()).throw(ConnectionError("store down")))
    with pytest.raises(ConnectionError):
        broken.call("tool", "ok", {}, lambda _: 1)
    assert broken.events == []


def test_json_validation():
    for value in [float("nan"), float("inf"), object(), {1: "x"}]:
        with pytest.raises(ValueError):
            canonical(value)
    nested = 1
    for _ in range(26):
        nested = [nested]
    with pytest.raises(ValueError):
        canonical(nested)
    assert redact({"Authorization": "anything", "text": "Bearer abc.def"}) == {
        "Authorization": "[REDACTED]", "text": "Bearer [REDACTED]"}


def test_breakpoint_fork_replay_and_restart(store):
    rid = store.create("Synthetic seeded unit bug", "demo", 2)
    advance(store, rid, 0)
    advance(store, rid, 1)
    paused = advance(store, rid, 2)
    assert paused["status"] == "paused" and len(paused["events"]) == 2
    assert advance(store, rid, 3)["revision"] == 3
    with pytest.raises(Conflict):
        advance(store, rid, 2, True)
    original = complete(store, rid)
    assert original["events"][-1]["output"]["message"] == "Reject"
    child = fork(store, rid, 2, {"amount_usd": 42, "divisor": 100})
    repaired = complete(store, child)
    assert repaired["events"][-1]["output"]["message"] == "Approve"
    assert [d["seq"] for d in diff(original, repaired)] == [2, 3, 4]
    assert store.read(rid) == original
    assert replay(original)["exact"] and replay(repaired)["exact"]
    # A new Store instance proves continuation is independent of Python process memory.
    assert configured().read(child)["events"] == repaired["events"]
    with pytest.raises(ValueError):
        fork(store, rid, 0, {})


def test_append_concurrency_idempotency_and_transaction_rollback(store):
    rid = store.create("concurrent SDK")
    event = {"kind": "tool", "name": "a", "input": {}, "output": 1, "error": None}
    with ThreadPoolExecutor(max_workers=8) as pool:
        receipts = list(pool.map(lambda _: store.append(rid, 0, event), range(24)))
    assert sum(not r["duplicate"] for r in receipts) == 1
    assert len(store.read(rid)["events"]) == 1
    with pytest.raises(Conflict):
        store.append(rid, 0, {**event, "output": 2})
    with pytest.raises(RuntimeError):
        with store.connection() as conn:
            store.insert(conn, rid, 1, event)
            raise RuntimeError("injected crash before commit")
    assert len(store.read(rid)["events"]) == 1
    with pytest.raises(ValueError):
        store.append(rid, 1, {**event, "kind": "unsafe"})


def test_continuation_concurrent_single_winner(store):
    rid = store.create("race", "demo")
    def attempt(_):
        try:
            advance(store, rid, 0)
            return True
        except Conflict:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(16))) == 1
    assert len(store.read(rid)["events"]) == 1


def test_server_redaction_at_rest(store):
    rid = store.create("server-side redaction")
    key = store.secrets[0]
    event = {"kind": "model", "name": "ask", "input": {"text": key},
             "output": {"password": "unregistered synthetic value", "text": key}, "error": None}
    store.append(rid, 0, event)
    with store.connection() as conn:
        raw = conn.execute("SELECT body::text FROM events WHERE run_id=%s", (rid,)).fetchone()["body"]
    assert key not in raw and "unregistered synthetic value" not in raw
    json.loads(raw)
