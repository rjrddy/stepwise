import "./motion";
import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";
type Frame = {
  kind: string;
  name: string;
  input: unknown;
  output: unknown;
  error: string | null;
};
type Run = {
  id: string;
  status: string;
  revision: number;
  parent: string | null;
  events: Frame[];
  mode: string;
};
type Receipt = {
  exact: boolean;
  frames: number;
  replay_sha256: string;
  provider_calls: number;
};
type Change = { seq: number; before: Frame; after: Frame };
const names = ["plan", "catalog.lookup", "quote.convert", "decision", "answer"];
const pretty = (v: unknown) => JSON.stringify(v, null, 2);
function App() {
  const [runs, setRuns] = useState<Run[]>([]),
    [run, setRun] = useState<Run | null>(null),
    [frame, setFrame] = useState(0),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [token, setToken] = useState(""),
    [connected, setConnected] = useState(false),
    [breakpoint, setBreakpoint] = useState("2"),
    [edit, setEdit] = useState(""),
    [other, setOther] = useState(""),
    [receipt, setReceipt] = useState<Receipt | null>(null),
    [changes, setChanges] = useState<Change[] | null>(null);
  const active = run?.events[frame];
  async function api(path: string, data?: unknown) {
    const r = await fetch("/api" + path, {
      method: data === undefined ? "GET" : "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
      body: data === undefined ? undefined : JSON.stringify(data),
    });
    const value = await r.json();
    if (!r.ok) throw Error(value.error);
    return value;
  }
  async function refresh() {
    setRuns(await api("/runs"));
    setConnected(true);
  }
  async function task(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(String(e));
      setConnected(false);
    } finally {
      setBusy(false);
    }
  }
  async function select(id: string) {
    const value = await api("/runs/" + id);
    setRun(value);
    setFrame(Math.max(0, value.events.length - 1));
    setReceipt(null);
    setChanges(null);
  }
  useEffect(() => {
    void task(refresh);
  }, []);
  useEffect(() => {
    setEdit(active ? pretty(active.output) : "");
  }, [run?.id, frame, run?.revision]);
  async function record() {
    await task(async () => {
      const { id } = await api("/runs", {
        label: "Synthetic quote",
        mode: "demo",
        breakpoint: breakpoint === "" ? null : Number(breakpoint),
      });
      await select(id);
      await refresh();
    });
  }
  async function advance(all = false) {
    if (!run) return;
    await task(async () => {
      let value = run;
      do {
        value = await api("/runs/" + run.id + "/advance", {
          revision: value.revision,
          resume: value.status === "paused",
        });
      } while (all && value.status === "open");
      setRun(value);
      setFrame(Math.max(0, value.events.length - 1));
      setReceipt(null);
      await refresh();
    });
  }
  async function fork() {
    if (!run) return;
    await task(async () => {
      const { id } = await api("/runs/" + run.id + "/fork", {
        seq: frame,
        output: JSON.parse(edit),
      });
      setOther(run.id);
      await select(id);
      await refresh();
    });
  }
  return (
    <div className="room">
      <header>
        <a href="/" className="brand">
          <svg viewBox="0 0 36 36" aria-hidden="true">
            <path
              d="M3 32V22h10V12h10V2h10"
              fill="none"
              stroke="currentColor"
              strokeWidth="4"
            />
          </svg>
          stepwise<small>THE EDIT ROOM</small>
        </a>
        <span role="status" className="connection">
          {connected ? "● Postgres connected" : "○ Connection needs attention"}
        </span>
        <span className="edition">SYNTHETIC SESSION / LOCAL</span>
      </header>
      <div className="intro">
        <div>
          <p className="eyebrow">AN AGENT RUN IS A SEQUENCE OF DECISIONS.</p>
          <h1>
            Find the frame.
            <br />
            <em>Change the outcome.</em>
          </h1>
        </div>
        <p className="intro-note">
          Inspect what the agent saw.
          <br />
          Replay what actually happened.
          <br />
          Keep the original intact.
          <small>No model account. Real recorded calls.</small>
        </p>
      </div>
      <main>
        <aside>
          <p className="eyebrow">01 / THE CUTS</p>
          <label>
            Break before tool
            <select
              aria-label="Break before tool"
              value={breakpoint}
              onChange={(e) => setBreakpoint(e.target.value)}
            >
              <option value="">No breakpoint</option>
              <option value="1">catalog.lookup</option>
              <option value="2">quote.convert</option>
            </select>
          </label>
          <button className="record" disabled={busy} onClick={record}>
            ● Record run
          </button>
          <div className="run-list">
            {runs.map((item, i) => (
              <button
                className={"run " + (run?.id === item.id ? "selected" : "")}
                key={item.id}
                disabled={busy}
                onClick={() => void task(() => select(item.id))}
              >
                <b>{(runs.length - i).toString().padStart(2, "0")}</b>
                <span>
                  {item.parent
                    ? "Alternate cut"
                    : item.mode === "sdk"
                      ? "SDK capture"
                      : "Original cut"}
                  <small>
                    {item.id.slice(0, 8)} · {item.status}
                  </small>
                </span>
                ↗
              </button>
            ))}
          </div>
          {!runs.length && (
            <p className="note">
              Your first recording starts here. The synthetic quote has a
              unit-conversion bug.
            </p>
          )}
          <details className="access">
            <summary>Connection settings</summary>
            <label>
              API token
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                autoComplete="off"
              />
            </label>
            <button onClick={() => void task(refresh)}>Reconnect</button>
            <p className="note">Token stays in memory.</p>
          </details>
          <p className="aside-foot">
            CAPTURE → INSPECT → FORK
            <br />
            Explicit boundaries, honest replay.
          </p>
        </aside>
        <section className="workbench" aria-label="Run debugger">
          <div className="transport">
            <div>
              <p className="eyebrow">02 / THE TIMELINE</p>
              <p className="note">
                {run
                  ? (run.parent ? "Alternate cut" : "Original cut") +
                    " / " +
                    run.status
                  : "Awaiting a recording"}
              </p>
            </div>
            <div className="actions">
              <button
                disabled={
                  busy || !run || run.status === "done" || run.mode !== "demo"
                }
                onClick={() => void advance()}
              >
                {run?.status === "paused" ? "Resume →" : "Step →"}
              </button>
              <button
                className="ink"
                disabled={
                  busy || !run || run.status === "done" || run.mode !== "demo"
                }
                onClick={() => void advance(true)}
              >
                Run to break ▷
              </button>
            </div>
          </div>
          <div className="filmstrip" aria-label="Frame timeline">
            {(run?.mode === "sdk" ? run.events.map((e) => e.name) : names).map(
              (name, i) => (
                <button
                  aria-label={`Frame ${i + 1} ${name}`}
                  aria-pressed={frame === i && !!run?.events[i]}
                  key={i}
                  disabled={!run?.events[i] || busy}
                  className={
                    "film-frame " +
                    (frame === i && run?.events[i] ? "current" : "")
                  }
                  onClick={() => setFrame(i)}
                >
                  <span>
                    {(i + 1).toString().padStart(2, "0")}
                    <i>
                      {run?.events[i]?.kind ||
                        (i === 1 || i === 2 ? "tool" : "model")}
                    </i>
                  </span>
                  <strong>{name}</strong>
                  <small>{run?.events[i] ? "RECORDED" : "NOT EXECUTED"}</small>
                </button>
              ),
            )}
          </div>
          {run?.status === "paused" && (
            <div className="pause" role="status">
              <b>Ⅱ Paused before {names[run.events.length]}</b>
              <span>The tool has not run. Resume executes it once.</span>
            </div>
          )}
          {active ? (
            <>
              <div className="inspector-title">
                <div>
                  <p className="eyebrow">
                    FRAME {(frame + 1).toString().padStart(2, "0")} /{" "}
                    {active.kind.toUpperCase()}
                  </p>
                  <h2>{active.name}</h2>
                </div>
                <span className="eyebrow">
                  {active.error ? "CAPTURED ERROR" : "RECORDED RESPONSE"}
                </span>
              </div>
              <div className="inspectors">
                <section>
                  <div className="code-title">
                    INPUT <span>What the agent sent</span>
                  </div>
                  <pre tabIndex={0}>{pretty(active.input)}</pre>
                </section>
                <section>
                  <div className="code-title">
                    OUTPUT <span>What it received</span>
                  </div>
                  <pre tabIndex={0}>
                    {active.error || pretty(active.output)}
                  </pre>
                </section>
              </div>
              {active.kind === "tool" && run?.mode === "demo" && (
                <section className="edit">
                  <div>
                    <p className="eyebrow">MAKE AN ALTERNATE CUT</p>
                    <h3>What if this response changed?</h3>
                    <p className="note">
                      Edit the JSON, fork here, then resume.
                      <br />
                      The original run stays intact.
                    </p>
                    {active.name === "quote.convert" && (
                      <button
                        className="text-button"
                        onClick={() =>
                          setEdit(pretty({ amount_usd: 42, divisor: 100 }))
                        }
                      >
                        Use corrected cents → dollars ↗
                      </button>
                    )}
                  </div>
                  <div>
                    <label className="sr-only" htmlFor="edited">
                      Edited tool output
                    </label>
                    <textarea
                      id="edited"
                      value={edit}
                      onChange={(e) => setEdit(e.target.value)}
                      spellCheck={false}
                    />
                    <button
                      className="ink"
                      disabled={busy}
                      onClick={() => void fork()}
                    >
                      Fork with edited output ↗
                    </button>
                  </div>
                </section>
              )}
            </>
          ) : (
            <div className="empty">
              <span>[ ▷ ]</span>
              <h2>Every call leaves a frame.</h2>
              <p className="note">
                Record a run, then step through its calls.
                <br />
                Pause at the quote conversion to inspect the seeded failure.
              </p>
            </div>
          )}
          {run && (
            <section className="verify">
              <div>
                <p className="eyebrow">03 / VERIFY THE CUT</p>
                <p className="note">
                  Replay public call payloads exactly.
                  <br />
                  Timing and run metadata are outside equality.
                </p>
                <button
                  disabled={busy || !run.events.length}
                  onClick={() =>
                    void task(async () => {
                      setReceipt(await api("/runs/" + run.id + "/replay", {}));
                    })
                  }
                >
                  Verify exact replay ↺
                </button>
                {receipt && (
                  <div className="receipt" role="status">
                    <b>
                      {receipt.exact ? "EXACT REPLAY" : "MISMATCH"} ·{" "}
                      {receipt.frames} frames
                    </b>
                    <span>
                      {receipt.provider_calls} provider calls during replay
                    </span>
                    <code>{receipt.replay_sha256}</code>
                  </div>
                )}
              </div>
              <div>
                <label>
                  Compare with
                  <select
                    aria-label="Compare with"
                    value={other}
                    onChange={(e) => setOther(e.target.value)}
                  >
                    <option value="">Choose a run</option>
                    {runs
                      .filter((r) => r.id !== run.id)
                      .map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.id.slice(0, 8)} ·{" "}
                          {r.parent ? "alternate" : "original"}
                        </option>
                      ))}
                  </select>
                </label>
                <button
                  disabled={busy || !other}
                  onClick={() =>
                    void task(async () => {
                      setChanges(
                        (await api("/runs/" + run.id + "/diff", { other }))
                          .changes,
                      );
                    })
                  }
                >
                  Diff the runs ⇄
                </button>
                {changes && (
                  <div className="diff">
                    <b>{changes.length} changed frames</b>
                    {changes.map((c) => (
                      <details key={c.seq}>
                        <summary>
                          Frame {c.seq + 1} · {c.before?.name || c.after?.name}
                        </summary>
                        <div>
                          <pre>{pretty(c.before?.output)}</pre>
                          <pre>{pretty(c.after?.output)}</pre>
                        </div>
                      </details>
                    ))}
                  </div>
                )}
              </div>
            </section>
          )}
        </section>
      </main>
      <div className="feedback" role="alert">
        {error && (
          <>
            <b>Action failed.</b> {error}{" "}
            <button onClick={() => void task(refresh)}>Retry connection</button>
          </>
        )}
        {busy && "Working with the trace store…"}
      </div>
      <footer>
        <span>STEPWISE / AGENT DEBUGGER</span>
        <span>
          Immutable originals. Explicit continuations. Synthetic data only.
        </span>
        <a href="https://github.com/rjrddy/stepwise">Source & guarantees ↗</a>
      </footer>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
