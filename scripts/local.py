"""Own a temporary Postgres cluster, or use the caller's explicit DATABASE_URL."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "serve"
    commands = {
        "serve": [sys.executable, "-m", "stepwise.server"],
        "test": [sys.executable, "-m", "pytest", "-q"],
        "bench": [sys.executable, "scripts/bench.py"],
        "review": [sys.executable, "scripts/review.py", *sys.argv[2:]],
    }
    command = commands[action]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    if env.get("DATABASE_URL"):
        subprocess.run(command, cwd=ROOT, env=env, check=True)
        return
    pg = shutil.which("pg_ctl")
    if not pg:
        raise SystemExit("Install PostgreSQL tools, or set DATABASE_URL. See docs/DEMO.md.")
    with tempfile.TemporaryDirectory(prefix="stepwise-pg-") as tmp:
        data, sock = Path(tmp) / "data", Path(tmp) / "socket"
        sock.mkdir()
        # Avoid long macOS unix socket paths; TCP port is independently selected.
        with socket.socket() as selector:
            selector.bind(("127.0.0.1", 0))
            port = selector.getsockname()[1]
        subprocess.run(
            ["initdb", "-D", str(data), "-A", "trust", "--no-locale", "-E", "UTF8"],
            stdout=subprocess.DEVNULL,
            check=True,
        )
        subprocess.run(
            [
                pg,
                "-D",
                str(data),
                "-l",
                str(Path(tmp) / "postgres.log"),
                "-o",
                f"-h 127.0.0.1 -p {port} -k {sock}",
                "-w",
                "start",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        env["DATABASE_URL"] = (
            f"postgresql://{os.getenv('USER', 'postgres')}@127.0.0.1:{port}/postgres"
        )
        try:
            subprocess.run(command, cwd=ROOT, env=env, check=True)
        finally:
            subprocess.run(
                [pg, "-D", str(data), "-m", "immediate", "-w", "stop"],
                stdout=subprocess.DEVNULL,
                check=True,
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
