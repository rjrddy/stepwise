# Hard follow-ups

1. **Why lock reads?** Separate metadata and event queries could otherwise see a concurrent commit between them. Run-row locking makes the API view consistent.
2. **Can an append acknowledge before commit?** No, the connection context exits before the store method returns. Network loss after commit still makes acknowledgement ambiguous.
3. **What is idempotent?** An SDK event retried at the same sequence with exactly the same redacted body. Continuation advances use revisions and conflict on stale retries.
4. **Why are stale advances not silently accepted?** A caller could otherwise accidentally consume another step. It must reread state and decide whether to resume.
5. **Can a paused tool already have executed?** The transition to paused commits before the call. A stale resume conflicts. External effects after execution still have the commit gap.
6. **What if the process exits inside a DB transaction?** Postgres discards the uncommitted frame; a child that actually calls os._exit is tested.
7. **Can DB credentials rewrite history?** Yes. This is API-level original preservation, not a tamper-evident log. Seal is a separate future project.
8. **Why not replay timestamps?** They are observations rather than call responses. Equality is explicitly scoped to canonical public events.
9. **Can a secret affect a branch?** Yes; the public replay may diverge after redaction. The debugger cannot reconstruct erased information.
10. **Are regexes enough for privacy?** No. Key/pattern/exact-value rules have known blind spots; this is not a PHI or universal secret classifier.
11. **Why deepcopy replay outputs?** Caller mutation must not alter the source tape or the retained replay receipt.
12. **What if an event is unused?** finish rejects it. A caller that skips finish loses that completeness check.
13. **Why does the generic endpoint's replay not suffice?** Iterating recorded calls only roundtrips their data. Application-driven replay must execute the surrounding application code.
14. **How are SDKs compared?** Real HTTP/Postgres tests exercise each SDK, including model/tool capture and replay. They do not assert floating-point canonical-byte parity across every JSON representation.
15. **What about large integers?** Cross-language input must stay within JavaScript's safe integer range; Python arbitrary precision does not make Node precise.
16. **Is persistence overhead constant?** No. The append path reads prior events and opens connections; the raw benchmark exposes a bounded local workload, not an asymptotic guarantee.
17. **Why can SQL lose?** Its connection and database work can outweigh JSON parsing on a small warm file. Raw samples retain that counterexample.
18. **Does a recording prove accessibility?** It proves tested interactions and viewport constraints. It is not a full screen-reader or WCAG audit.
19. **Can Node run overlapping calls on one tape?** It rejects them to avoid ambiguous ordering; independent tapes can record independent runs.
20. **Why partial?** Durable breakpoint/edit/resume is limited to the defined demo continuation, not arbitrary agents. Human diagnosis improvement and real-model behavior have not been measured.
