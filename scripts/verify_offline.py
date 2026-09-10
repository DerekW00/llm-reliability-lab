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
for name in ('connect', 'connect_ex', 'send', 'sendall', 'sendto'):
    setattr(socket.socket, name, blocked)
for name in ('create_connection', 'getaddrinfo', 'gethostbyname', 'gethostbyname_ex',
             'gethostbyaddr', 'getfqdn', 'getnameinfo'):
    setattr(socket, name, blocked)
import os
import reliability_lab
with open(os.environ["OFFLINE_IMPORT_ORIGIN"], "w") as handle:
    handle.write(reliability_lab.__file__)
from reliability_lab.cli import main
raise SystemExit(main())
"""

# The child needs only enough environment to locate an interpreter, Git and a
# temporary directory. An allowlist keeps unrelated provider credentials out;
# a name denylist cannot, because most credential names are unpredictable.
# PYTHONPATH is deliberately absent: it precedes site-packages, so forwarding it
# would let the gate certify whatever code the caller pointed at instead of the
# installed distribution. The child reports what it imported, and it is checked.
PASSTHROUGH = ("PATH", "HOME", "TMPDIR", "SYSTEMROOT", "COMSPEC")


class CheckFailed(RuntimeError):
    """A verification check failed. Not an assert: it must survive `python -O`."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise CheckFailed(message)


def main() -> int:
    environment = {key: os.environ[key] for key in PASSTHROUGH if key in os.environ}
    environment["UV_OFFLINE"] = "1"
    environment["LANG"] = "en_US.UTF-8"
    import reliability_lab

    expected_origin = reliability_lab.__file__
    with tempfile.TemporaryDirectory(prefix="reliability-offline-") as temporary:
        out = Path(temporary) / "reports"
        origin = Path(temporary) / "import-origin.txt"
        environment["OFFLINE_IMPORT_ORIGIN"] = str(origin)
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
            require(origin.is_file(), "the child never reported which package it imported")
            require(origin.read_text(encoding="utf-8") == expected_origin,
                    f"the child imported {origin.read_text(encoding='utf-8')!r}, "
                    f"not the installed {expected_origin!r}")
            if completed.returncode != expected or "OFFLINE GUARD:" in completed.stderr:
                print(completed.stdout)
                print(completed.stderr, file=sys.stderr)
                return 1
        for scenario in ("baseline", "regression", "repaired"):
            report = json.loads((out / f"{scenario}.json").read_text(encoding="utf-8"))
            require(report["mode"] == "synthetic_fixture", f"{scenario}: mode is not a fixture")
            require(report["provenance"]["live_calls"] is False, f"{scenario}: live_calls set")
            require(report["provenance"]["model"] is None, f"{scenario}: a model was recorded")
    print("Offline subprocess checks passed; no provider credentials were forwarded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
