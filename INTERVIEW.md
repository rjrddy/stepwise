# Stepwise interview

## Two-minute pitch

I built an agent debugger around explicit model and tool boundaries. Agent runs are nondeterministic, but an invocation's observed response can be captured. The Python and async Node SDKs record public JSON call data to Postgres, redact it, and replay recorded responses without calling the provider again. Replay checks call order and inputs and rejects unused frames.

The React interface presents calls as an edit-room filmstrip. A synthetic quote workflow contains a cents-to-dollars error. I can break before the tool, inspect its actual response, fork a corrected output, resume a child run and diff it against the untouched original. The next call is computed from the edited response, not a replacement screenshot.

The difficult part is stating what replay guarantees. A call tape does not freeze a process or make an external effect atomic with its log write. Durable continuation is implemented for the explicit synthetic state machine; arbitrary application pause/edit/resume is still a gap, so I mark the project partial. Recorded model calls are synthetic functions, not model inference. My measurements include the synchronous persistence cost, and the automated SQL diagnostic lost to a small raw-log baseline. I make no human productivity claim. Exact values and commands are in the generated README and raw results.

## Ten-minute walkthrough

Start with `core.py`: finite JSON validation, recursive redaction, canonical encoding, detached replay responses and order/input matching. Point out that an original provider failure is recorded but re-raised, while replay raises a recorded-error exception.

Walk through `sdk.py` and `sdk/node/index.mjs`. The caller passes its actual function to an explicit wrapper. Redaction happens before HTTP serialization and again at the store. The server acknowledges only after commit; a missing acknowledgement is not proof a tool never ran. Node awaits its sink and rejects overlapping calls on the tape. Python is synchronous and requires a single caller.

Then show the Postgres primary key and `FOR UPDATE` in `store.py`. The run row is the unit of serialization. Identical duplicate sequence retries are idempotent; changed retries conflict. Readers lock the same row so metadata and frames form a consistent view. DB timeouts prevent an indefinite lock wait. No database owner restriction or cryptographic tamper proof is implied.

Open `workflow.py`: revision fencing, paused state before execution, synthetic call functions, atomic child-prefix construction, and continuation input reconstruction. Explain why the same method cannot snapshot arbitrary Python stack frames. Then show application-driven replay in the HTTP SDK tests and the corrupted-input rejection test.

Demonstrate the React filmstrip, breakpoint, erroneous conversion, edited child, actual changed answer, hash receipt and structural diff. Show the browser network-recovery check and mobile screenshot. Finish with raw benchmark samples and the losing SQL diagnostic control. The partial scope is a deliberate report of unfinished work, not a claim that it meets the full arbitrary-agent requirement.

## Five tradeoffs

- Explicit wrappers require integration work but make the interception boundary auditable; hidden I/O is excluded.
- Synchronous writes add call latency but provide a simple committed acknowledgement; they still do not guarantee external-effect atomicity.
- Per-run locking makes sequence and revision reasoning simple but limits concurrent ingestion and adds full-tape reads.
- Redaction protects registered patterns but removes information needed for secret-dependent replay.
- Forking copies a prefix and preserves the original API view but uses more storage than shared immutable segments.

## Five failure modes

- Wrong tool order or changed inputs: replay rejects at the frame rather than silently consuming another response.
- Duplicate/late write: identical append retries succeed; a changed sequence or stale continuation revision conflicts.
- Process death before transaction commit: Postgres rolls back the uncommitted frame; actual child process exit is tested.
- Tool succeeds, persistence fails: caller receives failure and must reconcile the external effect; no automatic retry is safe for irreversible tools.
- Unknown secret or encoded credential: redaction may miss it. Configure exact values, avoid real data, and do not market this as universal DLP.

## Fifteen likely questions

1. **What is deterministic?** The redacted call-tape responses and expected call sequence, not process scheduling, random application code or real provider behavior.
2. **Why Postgres?** Row locks, transactions, JSONB and a small understandable consistency model. A connection per operation is intentionally unoptimized.
3. **Why not capture every network request?** Explicit boundaries avoid accidentally recording unrelated credentials and expose what application code must integrate.
4. **Does the HTTP replay prove an uploaded application is correct?** No. Generic trace roundtrip cannot execute code it does not have; run the replay tape in the application.
5. **What does the demo replay add?** It reconstructs inputs using the workflow's continuation code and rejects a recorded input that disagrees.
6. **Can an edit change the original?** No update route exists for originals; a fork creates a new run and prefix in a transaction. A DB owner can still alter data.
7. **Is a tool called twice after a crash?** It can be, when an external effect occurs before a failed trace commit. Require tool-specific idempotency/reconciliation.
8. **Are traces secret-free?** Registered values, sensitive keys and Bearer patterns are redacted. Unknown/encoded content and secret-bearing keys are outside coverage.
9. **How is pause durable?** The run status and committed event count live in Postgres. A continuation checks revision before consuming a frame.
10. **Why a state machine?** It gives a restartable JSON continuation without pretending to snapshot a language runtime.
11. **How was the UI verified?** Real browser actions exercise pause, edit, resume, diff, exact replay, viewport changes, failure/recovery and focus; the actual video is retained.
12. **Did diagnosis get faster?** The retained automated predicate benchmark did not beat its raw-log baseline; human diagnosis time is not measured.
13. **What overhead is measured?** Per-call samples for a tiny synthetic function disabled, memory-recorded and synchronously HTTP/Postgres-recorded; separate Node memory samples.
14. **What happens with concurrent SDK calls?** Node rejects overlap; Python requires a single caller. Multiple independent runs remain supported.
15. **What is unfinished?** Arbitrary-agent durable pause/edit/resume, real provider adapters, streaming, pooled ingest, retention, SSO and a human study; deployment remains unapproved.

## What I would do with three more months

Define a cooperative continuation protocol and integrate a real provider without implicit hooks. Separate ingestion from expensive tape reads, introduce bounded buffering with explicit durability semantics, and add streaming spans and retention. Add tenant isolation and production HTTP infrastructure before sharing sensitive traces. Run a preregistered, counterbalanced human study with multiple seeded failures, publishing negative outcomes. Connect Lean only after its independent evaluation exists.
