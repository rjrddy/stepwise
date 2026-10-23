"""Render measured claims only from retained command outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from string import Template

root = Path(__file__).resolve().parents[1]
r = json.loads((root / "docs/results/bench.json").read_text())
b = json.loads((root / "docs/results/browser/review.json").read_text())
counts = re.findall(r"(\d+) passed", (root / "docs/results/gates-and-bench.txt").read_text())
values = {
    "frames": r["replay_frames"],
    "tests": counts[-1],
    "disabled": f"{r['summary']['disabled']:.3f}",
    "memory": f"{r['summary']['memory']:.3f}",
    "http": f"{r['summary']['http_postgres'] / 1000:.3f}",
    "events": r["diagnosis"]["events"],
    "raw": f"{r['diagnosis']['raw_jsonl']['p50_us'] / 1000:.3f}",
    "sql": f"{r['diagnosis']['postgres_query']['p50_us'] / 1000:.3f}",
    "duration": f"{float(b['ffprobe']['format']['duration']):.2f}",
}
text = Template((root / "docs/README.template.md").read_text()).substitute(values)
(root / "README.md").write_text(text)
