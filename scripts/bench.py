"""Real call-boundary costs and a reproducible automated diagnostic task, not a user study."""

from __future__ import annotations

import json
import platform
import statistics
import subprocess
import threading
import time
from functools import partial
from pathlib import Path

from stepwise.core import Divergence, Tape, canonical
from stepwise.sdk import Client
from stepwise.server import Server
from stepwise.store import configured
from stepwise.workflow import advance, fork, replay

OUT = Path("docs/results")


def sample(fn, count: int) -> dict:
    latencies = []
    for _ in range(count):
        start = time.perf_counter_ns()
        fn()
        latencies.append((time.perf_counter_ns() - start) / 1000)
    ordered = sorted(latencies)
    return {
        "calls": count,
        "p50_us": statistics.median(latencies),
        "p99_us": ordered[int((len(ordered) - 1) * 0.99)],
        "samples_us": latencies,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    store = configured()
    store.migrate()
    rid = store.create("Seeded conversion failure", "demo", 2)
    while (run := store.read(rid))["status"] != "done":
        advance(store, rid, run["revision"], True)
    original = store.read(rid)
    child = fork(store, rid, 2, {"amount_usd": 42, "divisor": 100})
    while (run := store.read(child))["status"] != "done":
        advance(store, child, run["revision"], True)
    replay_proofs = [replay(original), replay(store.read(child))]
    rejected = ""
    try:
        Tape(replay=original["events"]).call("tool", "wrong.order", {}, lambda _: None)
    except Divergence as exc:
        rejected = str(exc)
    assert rejected
    (OUT / "caught-failure.json").write_text(
        json.dumps({"injected": "wrong tool order", "rejected": rejected}, indent=2) + "\n"
    )
    (OUT / "replay.json").write_text(
        json.dumps(
            {"original": original, "repaired": store.read(child), "proofs": replay_proofs}, indent=2
        )
        + "\n"
    )
    server = Server(("127.0.0.1", 0), store)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    trials = []
    try:
        for _ in range(3):
            client = Client(base)
            _, persisted = client.record("overhead synthetic")
            memory = Tape()
            payload = {"sku": "SYNTH", "count": 3}
            fn = lambda p: {"answer": p["count"] * 14}  # noqa: E731
            trials.append(
                {
                    "disabled": sample(partial(fn, payload), 300),
                    "memory": sample(partial(memory.call, "tool", "lookup", payload, fn), 300),
                    "http_postgres": sample(
                        partial(persisted.call, "tool", "lookup", payload, fn), 300
                    ),
                }
            )
        node = subprocess.run(
            ["node", "scripts/bench_node.mjs"], capture_output=True, text=True, check=True
        )
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
    # Identical redacted event corpus. Compare a SQL predicate to raw JSONL parsing.
    # No pre-computed fault label, no human timings, no claims about diagnosis skill.
    corpus_id = store.create("diagnostic corpus")
    corpus = []
    event = original["events"][2]
    with store.connection() as conn:
        for index in range(1000):
            bad = index == 971
            record = {
                **event,
                "output": {"amount_usd": 4200 if bad else 42, "divisor": 1 if bad else 100},
            }
            store.insert(conn, corpus_id, index, record)
            corpus.append({"seq": index, **record})
    rawfile = OUT / "diagnosis-corpus.jsonl"
    rawfile.write_text("".join(canonical(row) + "\n" for row in corpus))

    def logs():
        for line in rawfile.read_text().splitlines():
            row = json.loads(line)
            if row["output"]["amount_usd"] != row["input"]["previous"]["price_cents"] / 100:
                assert row["seq"] == 971
                return row["seq"]
        raise AssertionError("missing fault")

    def query():
        with store.connection() as conn:
            row = conn.execute(
                """SELECT seq FROM events WHERE run_id=%s AND
              (body->'output'->>'amount_usd')::numeric <>
              (body->'input'->'previous'->>'price_cents')::numeric/100 ORDER BY seq LIMIT 1""",
                (corpus_id,),
            ).fetchone()
            assert row["seq"] == 971
            return row["seq"]

    diagnosis = {
        "kind": "automated known-predicate localization; NOT a human study",
        "events": len(corpus),
        "fault_seq": 971,
        "raw_jsonl": sample(logs, 50),
        "postgres_query": sample(query, 50),
    }
    result = {
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "postgres": subprocess.check_output(["postgres", "--version"], text=True).strip(),
        },
        "scope": "synchronous one-call write; new HTTP and DB connection per event; no LLM latency",
        "trials": trials,
        "node": json.loads(node.stdout),
        "diagnosis": diagnosis,
        "replay_exact": all(p["exact"] for p in replay_proofs),
        "replay_frames": sum(p["frames"] for p in replay_proofs),
    }
    result["summary"] = {
        key: statistics.median(t[key]["p50_us"] for t in trials)
        for key in ("disabled", "memory", "http_postgres")
    }
    (OUT / "bench.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "summary_us": result["summary"],
                "diagnosis": diagnosis,
                "replay_frames": result["replay_frames"],
            }
        )
    )


if __name__ == "__main__":
    main()
