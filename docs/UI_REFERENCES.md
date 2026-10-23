# The edit room

An original lavender/plum/salmon film-editing workbench: numbered filmstrip frames, perforations, an alternate-cut library, side-by-side input/output, tool response editor, and replay/diff receipts. Georgia italic headings and monospace payload labels separate narrative from machine data. All graphics are original CSS and a small inline staircase SVG. No remote fonts, images, template components or copied assets.

Outside interaction reference: [Chrome DevTools Recorder reference](https://developer.chrome.com/docs/devtools/recorder/reference), inspected during implementation. It documents slowing execution, stepping and breaking before recorded actions. Stepwise uses those familiar semantics while giving call-boundary replay and forked continuation their own visual presentation.

Responsive browser proofs and actual screenshots/recording are under `docs/results/browser/`. The design retains horizontal scrolling inside the filmstrip, stacks inspectors on narrow screens, and keeps the page itself within the viewport. Error/reconnect, keyboard focus and live state transitions are exercised by `scripts/review.py`.
