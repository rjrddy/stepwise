# Salvage provenance

Reviewed the root audit's mapped projects: sensor-fusion replay (`projects/p1-sensor-fusion-replay/src/replay.py`), robot action validation (`projects/r1-robot-action-validator/src/validator.py`), and arm regression evaluation (`projects/r2-arm-regression-harness/src/harness.py`). Reused ideas only: seeded scenarios, deterministic replay comparison, explicit rejection evidence and regression gates. Their signal, robot action and arm semantics do not belong in an agent debugger.

All Stepwise source, wire protocol, Postgres schema, Python/Node SDKs, synthetic quote workflow, UI, tests and benchmarks were written here. No old source was copied and no old directory or remote was removed. No code changed in the kept projects. Lean integration is deferred until Lean passes independently.
