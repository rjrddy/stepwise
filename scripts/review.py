"""Real React/Postgres browser review; optional recording performs repeated real lifecycles."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/results/browser"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    receipts = []
    with (
        tempfile.TemporaryDirectory() as temp,
        (Path(tempfile.gettempdir()) / "stepwise-review.log").open("w") as log,
    ):
        process = subprocess.Popen(
            [sys.executable, "-m", "stepwise.server"],
            env={**os.environ, "PORT": "0"},
            stdout=log,
            stderr=log,
        )
        try:
            base = ""
            for _ in range(200):
                for line in Path(log.name).read_text().splitlines():
                    row = json.loads(line)
                    if row.get("event") == "ready":
                        base = row["url"]
                if base:
                    break
                if process.poll() is not None:
                    raise RuntimeError(Path(log.name).read_text())
                time.sleep(0.025)
            assert base, "server readiness timeout"
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=p.chromium.executable_path)
                context = browser.new_context(
                    viewport={"width": 1440, "height": 1100},
                    **(
                        {
                            "record_video_dir": temp,
                            "record_video_size": {"width": 1440, "height": 1100},
                        }
                        if args.record
                        else {}
                    ),
                )
                page = context.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base)
                expect(
                    page.get_by_role("status").filter(has_text="Postgres connected")
                ).to_be_visible()
                started = time.monotonic()

                def click(name):
                    page.get_by_role("button", name=name, exact=True).click()

                def lifecycle():
                    click("● Record run")
                    expect(page.get_by_role("button", name="Run to break ▷")).to_be_enabled()
                    click("Run to break ▷")
                    expect(
                        page.get_by_role("status").filter(has_text="Paused before quote.convert")
                    ).to_be_visible()
                    click("Resume →")
                    click("Run to break ▷")
                    expect(page.locator(".transport .note")).to_contain_text("done")
                    expect(page.locator(".inspectors")).to_contain_text("Reject")
                    click("Verify exact replay ↺")
                    expect(page.locator(".receipt")).to_contain_text("EXACT REPLAY · 5 frames")
                    page.get_by_role("button", name="Frame 3 quote.convert", exact=True).click()
                    click("Use corrected cents → dollars ↗")
                    click("Fork with edited output ↗")
                    expect(page.locator(".transport .note")).to_contain_text("Alternate cut")
                    click("Run to break ▷")
                    expect(page.locator(".inspectors")).to_contain_text("Approve")
                    click("Verify exact replay ↺")
                    expect(page.locator(".receipt")).to_contain_text("EXACT REPLAY · 5 frames")
                    click("Diff the runs ⇄")
                    expect(page.locator(".diff")).to_contain_text("3 changed frames")
                    with urllib.request.urlopen(base + "/api/runs") as response:
                        newest = json.load(response)[0]
                    with urllib.request.urlopen(base + "/api/runs/" + newest["id"]) as response:
                        run = json.load(response)
                    assert run["events"][-1]["output"]["message"] == "Approve"
                    receipts.append(
                        {
                            "run": run["id"],
                            "frames": len(run["events"]),
                            "elapsed_s": time.monotonic() - started,
                        }
                    )

                lifecycle()
                page.screenshot(path=str(OUT / "desktop.png"), full_page=True)
                widths = []
                for width in [390, 768, 1024, 1440]:
                    page.set_viewport_size({"width": width, "height": 1000})
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    expect(page.get_by_role("heading", level=1)).to_be_visible()
                    widths.append(width)
                page.set_viewport_size({"width": 390, "height": 1000})
                page.screenshot(path=str(OUT / "mobile.png"), full_page=True)
                page.set_viewport_size({"width": 1440, "height": 1100})
                page.get_by_text("Connection settings", exact=True).click()
                page.route("**/api/runs", lambda route: route.abort())
                click("Reconnect")
                expect(page.get_by_role("alert")).to_contain_text("Action failed")
                page.unroute("**/api/runs")
                click("Retry connection")
                expect(
                    page.get_by_role("status").filter(has_text="Postgres connected")
                ).to_be_visible()
                page.keyboard.press("Tab")
                assert page.evaluate("document.activeElement !== document.body")
                if args.record:
                    while time.monotonic() - started < 92:
                        lifecycle()  # Real tool execution, edit, continuation, replay, diff.
                video = page.video
                context.close()
                if video:
                    video.save_as(str(OUT / "demo.webm"))
                browser.close()
                assert not errors, errors
                result = {
                    "responsive_widths": widths,
                    "page_errors": errors,
                    "network_failure_recovery": True,
                    "keyboard_focus": True,
                    "lifecycles": receipts,
                    "duration_s": time.monotonic() - started,
                }
                if args.record:
                    result["ffprobe"] = json.loads(
                        subprocess.check_output(
                            [
                                "ffprobe",
                                "-v",
                                "quiet",
                                "-show_format",
                                "-of",
                                "json",
                                str(OUT / "demo.webm"),
                            ],
                            text=True,
                        )
                    )
                    assert float(result["ffprobe"]["format"]["duration"]) >= 90
                (OUT / "review.json").write_text(json.dumps(result, indent=2) + "\n")
                print(json.dumps(result))
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
