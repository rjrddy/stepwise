# Run and record

Native prerequisites: Python, Node/npm, PostgreSQL client/server tools on PATH. `make demo` installs dependencies, builds the React UI, starts a private temporary Postgres cluster and serves the app at http://127.0.0.1:8091. No database account or model account is needed. The temporary database is removed on exit. Set DATABASE_URL to an explicitly owned existing database to keep traces between launches; do not point tests at production data. `PORT` overrides the local HTTP port. Ctrl-C stops the owned processes.

Alternatively `docker compose up --build` creates a persistent local Postgres volume and a nonroot debugger. Open the same URL, expand Connection settings, and use `synthetic-local-console-key-0001` unless you supplied STEPWISE_TOKEN. These are public synthetic local demo values, not secrets suitable for shared hosting.

## An actual ninety-second demonstration

Start screen recording before the following actions and narrate the limits rather than padding an idle screen:

- Record a run with `quote.convert` as breakpoint. Run to break; show that the tool frame has not executed.
- Resume, then run to completion. Inspect the final Reject decision, then the catalog's cents and converter's incorrect amount.
- Verify exact replay and show the hash and absence of provider calls. Explain that this compares redacted call payloads, not timestamps or a frozen process.
- Select the conversion frame. Use the corrected cents-to-dollars response, fork, and run the child. Show the Approve decision.
- Diff against the original, inspect the changed conversion/decision/answer, then select the original to show it remains unchanged.
- Narrow the viewport and inspect the filmstrip. Explain that durable edits currently work only for this explicit state machine, while real applications use the Python/Node SDK to record and replay their own code.

Automated recorder (uses real repeated workflow lifecycles, no video padding): install `requirements-browser.txt`, run `.venv/bin/python -m playwright install chromium ffmpeg`, then `.venv/bin/python scripts/local.py review --record`. `PLAYWRIGHT_BROWSERS_PATH` may point to an already installed matching browser cache. Output is `docs/results/browser/demo.webm`; verify actual duration with `ffprobe -v quiet -show_format -of json docs/results/browser/demo.webm`. The checked-in recording's duration is in review.json, not estimated from the script.

## Hosting preparation only

Dockerfile and render.yaml are prepared. No provider was provisioned. To deploy later, approve hosting, choose an existing Postgres URL, configure DATABASE_URL, generate a long STEPWISE_TOKEN and review access/TLS/retention. Render free instances can sleep/restart; external Postgres must remain durable. There are no hosted latency claims. The browser token is only a single shared developer credential, not user authorization.
