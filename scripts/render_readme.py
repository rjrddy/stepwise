"""Render measured claims only from retained command outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
r = json.loads((root / "docs/results/bench.json").read_text())
b = json.loads((root / "docs/results/browser/review.json").read_text())
counts = re.findall(r"(\d+) passed", (root / "docs/results/gates-and-bench.txt").read_text())
summary = r["summary"]
raw = r["diagnosis"]["raw_jsonl"]["p50_us"] / 1000
sql = r["diagnosis"]["postgres_query"]["p50_us"] / 1000
content = f"""# Stepwise

Nondeterministic agent calls hide failures; Stepwise records their boundaries so you can inspect, replay and fork a synthetic workflow without overwriting its original trace.

## Result

Exact redacted replay: {r["replay_frames"]} frames across original/repaired runs; {counts[-1]} tests pass ([raw run](docs/results/gates-and-bench.txt), [hash proofs](docs/results/replay.json)).
Python median call time: disabled {summary["disabled"]:.3f} µs; memory capture {summary["memory"]:.3f} µs; synchronous HTTP/Postgres {summary["http_postgres"] / 1000:.3f} ms ([samples](docs/results/bench.json)).
Automated fault localization, {r["diagnosis"]["events"]} events: raw JSONL {raw:.3f} ms vs SQL {sql:.3f} ms median; real UI recording {float(b["ffprobe"]["format"]["duration"]):.2f} s ([browser proof](docs/results/browser/review.json)); human diagnosis time **not measured**.

## Architecture

```mermaid
flowchart LR
    P[Python / Node application] --> S[Explicit tool and model wrappers]
    S --> R[Redact then append]
    R --> A[HTTP API / revision checks]
    A --> D[(Postgres runs and ordered events)]
    U[React edit room] --> A
    A --> W[Durable synthetic continuation]
    D --> T[Replay tape: no provider calls]
    W --> F[Fork prefix / edited tool output]
    F --> D
```

## Run it

Prerequisites: Python, Node/npm and PostgreSQL server tools on PATH. No model account, database account or dataset download. `make demo` owns a temporary database; set DATABASE_URL only for an explicitly owned persistent database. Existing traces on a supplied database are not cleared.

```sh
make demo
# Open http://127.0.0.1:8091
make lint test bench
```

Alternatively `docker compose up --build`; use the documented synthetic local console token in Connection settings. See [demo and recording steps](docs/DEMO.md), [SDK examples](docs/SDK.md), and the [actual recording](docs/results/browser/demo.webm).

## Decisions and limits

**Partial for the broader spec:** durable breakpoints, edited tool outputs and continuation are implemented for an explicit synthetic workflow. Generic Python/Node application traces support call capture, inspection, diff and application-driven replay; arbitrary application pause/edit/resume is unfinished. Human diagnosis-time improvement, actual model-provider integrations, streaming, multitenant authorization and hosted operation are not measured or implemented. Nothing is deployed.

The model boundary is a nondeterministic scripted synthetic function, not LLM inference. Replay equality means canonical **redacted call payloads** (including failures), excluding timing and run metadata. A configured secret cannot be reconstructed. The demo replay reruns its continuation logic; an uploaded SDK trace must be replayed inside its calling application to verify that application's behavior. The API cannot execute arbitrary uploaded code.

Original traces are immutable through this API; DB owners can still mutate rows. External tool effects and trace commits are not atomic. Synchronous persistence fails closed and has visible cost; neither pooling nor asynchronous buffering conceals that cost. One worker per SDK tape. Per-run/body limits do not bound database growth. See [design](docs/DESIGN.md) and [ADRs](docs/adr/).

The automated SQL lookup did not improve the raw-log baseline in this run. It times a known predicate, not a person discovering a bug or navigating this UI. Node memory samples are separate; Node HTTP overhead is not separately measured. Results are local, small-workload observations, not production forecasts.

Demonstrated caught failures: [divergent replay rejected](docs/results/caught-failure.json), [outdated bundled pip rejected by dependency scan](docs/results/caught-outdated-pip-audit.txt), repaired [clean scan](docs/results/python-audit.txt); tests cover stale revisions, conflicting writes, actual process exit before commit and unavailable Postgres. [Browser proof](docs/results/browser/review.json) exercises real fault/recovery, responsive layouts and keyboard focus. [UI reference and original design](docs/UI_REFERENCES.md).

[Interview walkthrough](INTERVIEW.md) · [Hard follow-ups](DRILL.md) · [Migration provenance](docs/migration/stepwise.md) · [CI](https://github.com/rjrddy/stepwise/actions)

## Next

A cooperative SDK continuation protocol for arbitrary agents; instrument an actual provider through an explicit adapter; streaming/async spans; pooled batched ingest with a documented loss budget; user identities, retention and trace pagination; a counterbalanced human diagnosis study. Integrate with Lean only after it independently passes its checks.
"""
(root / "README.md").write_text(content)
