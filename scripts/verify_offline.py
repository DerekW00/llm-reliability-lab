"""Run the installed CLI with Python network entry points instrumented to fail.

Install dependencies first. Invoke with `uv run --offline python scripts/verify_offline.py`.
The guard covers each CLI subprocess, not dependency installation or arbitrary OS processes.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

GUARD = """
import socket
def blocked(*args, **kwargs):
    raise RuntimeError('OFFLINE GUARD: runtime network access forbidden')
socket.socket.connect = blocked
socket.socket.connect_ex = blocked
socket.create_connection = blocked
socket.getaddrinfo = blocked
from reliability_lab.cli import main
raise SystemExit(main())
"""


def main() -> int:
    environment = {
        key: value for key, value in os.environ.items()
        if not any(part in key.upper() for part in ("API_KEY", "API_TOKEN", "ACCESS_TOKEN"))
    }
    environment["UV_OFFLINE"] = "1"
    with tempfile.TemporaryDirectory(prefix="reliability-offline-") as temporary:
        out = Path(temporary) / "reports"
        commands = [
            (["demo", "--scenario", name, "--output-dir", str(out)], expected)
            for name, expected in (("baseline", 0), ("regression", 1), ("repaired", 0))
        ]
        commands.append((["compare", str(out / "baseline.json"),
                          str(out / "regression.json"), "--output-dir", str(out)], 1))
        for args, expected in commands:
            completed = subprocess.run([sys.executable, "-c", GUARD, *args],
                                       cwd=temporary, env=environment, capture_output=True,
                                       text=True, timeout=60, check=False)
            print(f"{' '.join(args[:3])}: exit {completed.returncode} (expected {expected})")
            if completed.returncode != expected or "OFFLINE GUARD:" in completed.stderr:
                print(completed.stdout)
                print(completed.stderr, file=sys.stderr)
                return 1
        for scenario in ("baseline", "regression", "repaired"):
            report = json.loads((out / f"{scenario}.json").read_text())
            assert report["mode"] == "synthetic_fixture"
            assert report["provenance"]["live_calls"] is False
            assert report["provenance"]["model"] is None
    print("Offline subprocess checks passed; no provider credentials were needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
