# Design: record the boundary, keep the continuation explicit

The hard part is that calling the same model twice does not imply the same response, and a tool can change the outside world. An execution recording must capture the response at the boundary, preserve order, reject mismatched replay inputs, and avoid pretending that replaying a log re-executes the agent's code.

## Call tape

`core.Tape.call(kind, name, input, fn)` records one explicit synchronous boundary. The Python SDK returns the original result to the application, records a redacted copy, and persists synchronously through its sink before returning. The async Node SDK follows the same protocol and rejects overlapping calls on a tape. Applications must wrap both tools and model message calls; there is no automatic interception of arbitrary SDK libraries, token streaming, generators, or hidden I/O. Python tapes require a single caller. A tape contains JSON values only, bounded nesting, and an error or a response. Both client and server redact. A persistence failure propagates to the caller.

Replay checks kind, name and canonical input at each boundary, returns a detached copy of the recorded public result, and never invokes the callable. `finish()` rejects unused frames. A recorded failure becomes a replay exception. The actual application must still execute its own intervening code: the HTTP SDK tests demonstrate that use. A developer who branches on a secret that was removed cannot expect identical downstream behavior.

The demo's replay endpoint reconstructs the workflow's next input from the preceding replayed output; altered continuation inputs are rejected. For arbitrary uploaded SDK traces the endpoint only verifies call-tape roundtripping: it does not possess or execute the caller's application. Use the SDK inside that application for meaningful replay. Equality includes public call kind, name, input, output and error; excludes identifiers, timing, metadata, and original secrets. A hash is a comparison aid, not a signature or anti-tamper guarantee.

## Durable workflow and debugger

The synthetic workflow calls a nondeterministic scripted model, looks up an instrument, converts cents to dollars, decides against a budget, and formats an answer. The seeded conversion bug drops the divisor. It is not an actual LLM integration and evaluates no model quality. The browser records real server executions rather than playing a prepared JSON fixture.

Each advance locks its run row, checks the expected revision, inserts its frame and changes status in a transaction. Repeated stale advance requests conflict instead of running another tool. A configured breakpoint commits `paused` before the selected tool executes; Resume explicitly consumes it. A pause survives application restart because the cursor is the length of the committed tape, not Python memory.

Editing a tool response atomically creates a child run with a copied prefix and a replaced selected output. It never updates original trace rows through the API. Running the child computes subsequent calls from its edited result. This is a defined JSON state machine, not a saved Python stack. Uploaded SDK runs can be inspected, diffed and replayed in their application; durable breakpoint/edit/resume for arbitrary application code is unfinished. This gap makes the broader project **partial**.

## Storage and ownership

Postgres `runs` contains status/revision/parent/breakpoint; `events` has a `(run_id, seq)` primary key and redacted JSONB. All readers and writers lock the run row so metadata and events are consistent. Appends accept the next sequence or an identical retry of an existing frame; changed retries or skipped sequences conflict. A process dying before commit leaves no frame. A process dying after a real external tool succeeds but before commit can still leave an unrecorded side effect. There is no exactly-once external execution guarantee. The demo tools are pure synthetic functions and safe to retry.

The service opens a database connection per operation. Appending reads the existing tape under its row lock, so cost grows with tape length. This is deliberately simple, not a production trace ingest pipeline. Per-run SDK event and HTTP body limits bound individual work, not total database growth. Listing returns the latest runs. Retention, paging beyond that window, object storage, pooling, multi-worker async traces and spans are Next.

## Redaction and access

Recursive sensitive key matching, Bearer-token patterns and configured exact secret values are removed before transport (SDK) and before storage (server). `STEPWISE_SECRETS` is a pipe-separated list: configure both SDK and server for defense in depth. Never use real credentials in fixtures. Arbitrary free-form secrets not configured or matching a rule, secret-bearing object keys, encodings, and inference of private data are not covered. SDK exceptions re-raised to the calling application remain that application's logging responsibility. Outputs returned to live caller code are not redacted.

No raw payloads, URLs, exception strings or auth headers appear in service logs. API errors are generic. Non-loopback binding requires an environment token; UI holds it only in memory. Writes check same-origin when a browser Origin is present. There is no CORS wildcard. JSON/body limits, DB lock/statement timeouts, CSP and MIME protections are applied. The standard-library threaded server is a local developer tool, not an Internet-facing multitenant service. Use a hardened proxy, TLS, SSO, per-user authorization, connection limits and retention before sharing it. DB owner credentials can mutate historical data: API immutability is not cryptographic immutability.

## Evidence boundaries

See `docs/results/bench.json` for per-call samples across repeated trials and machine/runtime details. Disabled, in-memory record, and synchronous HTTP/Postgres recording are separate scopes. The underlying function is a tiny synthetic JSON callable, not model inference. Node memory costs are measured separately; Node HTTP persistence overhead is not separately benchmarked.

Diagnosis benchmark compares the same known cents/dollars predicate over the same corpus through a SQL JSON predicate versus parsing raw JSONL. It includes connection establishment and file read/parse respectively. It is an automated localization task, not a human study or evidence that this UI improves diagnosis time. Neither path has an injected fault label. A warm local corpus and a single fault type limit generalization. Both raw samples and counterproductive results are retained.

References: [Postgres explicit row locking](https://www.postgresql.org/docs/17/explicit-locking.html), [Chrome DevTools Recorder step/break controls](https://developer.chrome.com/docs/devtools/recorder/reference). These inform locking semantics and interaction design; no assets or interface implementation were copied.
