"""Smoke an actual built image; CI supplies an actual Postgres service."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request

base = "http://127.0.0.1:18091"
token = "synthetic-container-token-0001"


def request(path: str, data=None):
    req = urllib.request.Request(
        base + path,
        data=None if data is None else json.dumps(data).encode(),
        headers={"Authorization": "Bearer " + token},
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


def main() -> None:
    name = "stepwise-ci-smoke"
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "--network",
            "host",
            "-e",
            "HOST=0.0.0.0",
            "-e",
            "PORT=18091",
            "-e",
            "STEPWISE_TOKEN=" + token,
            "-e",
            "DATABASE_URL=" + os.environ["DATABASE_URL"],
            "stepwise:test",
        ],
        check=True,
    )
    try:
        for _ in range(60):
            try:
                if request("/api/health")["status"] == "ready":
                    break
            except (OSError, urllib.error.HTTPError):
                time.sleep(0.5)
        else:
            raise AssertionError("container not ready")
        with urllib.request.urlopen(base) as response:
            html = response.read().decode()
        assert "Stepwise" in html and "/assets/" in html
        import re

        asset = re.search(r'src="([^"]+\.js)"', html).group(1)
        with urllib.request.urlopen(base + asset) as response:
            assert response.status == 200 and len(response.read()) > 0
        rid = request("/api/runs", {"label": "container restart", "mode": "demo"})["id"]
        run = request("/api/runs/" + rid)
        while run["status"] != "done":
            run = request(f"/api/runs/{rid}/advance", {"revision": run["revision"]})
        before = request(f"/api/runs/{rid}/replay", {})
        subprocess.run(["docker", "restart", name], check=True)
        for _ in range(60):
            try:
                after = request(f"/api/runs/{rid}/replay", {})
                break
            except (OSError, urllib.error.HTTPError):
                time.sleep(0.5)
        assert before == after and after["exact"]
        database = os.getenv("POSTGRES_CONTAINER")
        if database:
            subprocess.run(["docker", "restart", database], check=True)
            for _ in range(60):
                try:
                    restored = request(f"/api/runs/{rid}/replay", {})
                    assert restored == before
                    break
                except (OSError, urllib.error.HTTPError):
                    time.sleep(0.5)
            else:
                raise AssertionError("database restart did not recover")
        print(json.dumps({"actual_container": True, "restart_replay_equal": True, "proof": after}))
    finally:
        subprocess.run(["docker", "logs", name], check=True)
        subprocess.run(["docker", "rm", "-f", name], check=True)


if __name__ == "__main__":
    main()
