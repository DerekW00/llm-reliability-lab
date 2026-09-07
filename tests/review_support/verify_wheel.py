"""Independent local wheel installation/CLI probe; build the wheel beforehand.

Run: uv run --offline python tests/review_support/verify_wheel.py dist/*.whl
The wheel environment is intentionally inside a real Git checkout, but its files
are not tracked source. Commands run in another temporary directory outside it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = '''
import atexit
import json
import os
import socket
calls = []
def blocked(*args, **kwargs):
    calls.append("network-attempt")
    raise OSError("REVIEW_NETWORK_FORBIDDEN")
for name in ("connect", "connect_ex", "sendto", "sendall", "send"):
    setattr(socket.socket, name, blocked)
for name in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex",
             "gethostbyaddr", "getfqdn"):
    setattr(socket, name, blocked)
def save_guard_result():
    with open(os.environ["REVIEW_GUARD_RESULT"], "w") as file:
        json.dump({"loaded": True, "network_attempts": calls}, file)
atexit.register(save_guard_result)
'''


class CheckFailed(RuntimeError):
    """A verification check failed. Not an assert: it must survive `python -O`."""


def require(condition: object, message: object) -> None:
    if not condition:
        raise CheckFailed(str(message))


def main() -> None:
    wheel = Path(sys.argv[1]).resolve()
    require(wheel.is_file(), wheel)
    (ROOT / "reports").mkdir(exist_ok=True)
    with (tempfile.TemporaryDirectory(prefix="review-wheel-", dir=ROOT / "reports") as nested,
          tempfile.TemporaryDirectory(prefix="review-outside-") as external):
        env_path = Path(nested) / "env"
        outside = Path(external)
        for args in (
            ["uv", "venv", "--python", sys.executable, str(env_path)],
            ["uv", "pip", "install", "--python", str(env_path / "bin/python"),
             "--no-index", "--no-deps", str(wheel)],
        ):
            completed = subprocess.run(args, cwd=outside, capture_output=True, text=True)
            print(json.dumps({"command": args, "exit": completed.returncode}))
            require(completed.returncode == 0, completed.stdout + completed.stderr)
        guard_dir = outside / "guard"
        guard_dir.mkdir()
        (guard_dir / "sitecustomize.py").write_text(GUARD)
        guard_result = outside / "guard-result.json"
        environment = {
            "PATH": os.environ["PATH"], "LANG": "en_US.UTF-8",
            "PYTHONPATH": str(guard_dir), "REVIEW_GUARD_RESULT": str(guard_result),
        }
        python = str(env_path / "bin/python")
        cli = str(env_path / "bin/reliability-lab")
        imported = subprocess.run(
            [python, "-c", "import json,reliability_lab; "
             "from reliability_lab.evaluation import _code_provenance; "
             "from reliability_lab.resources import resource_path; "
             "print(json.dumps({'import':reliability_lab.__file__, "
             "'data':str(resource_path('data/evaluation.json')), "
             "'provenance':_code_provenance()}))"],
            cwd=outside, env=environment, capture_output=True, text=True,
        )
        require(imported.returncode == 0, imported.stderr)
        info = json.loads(imported.stdout)
        require(str(env_path) in info["import"] and "site-packages" in info["import"],
                f"import did not come from the installed wheel: {info}")
        require(str(env_path) in info["data"] and "site-packages" in info["data"],
                f"bundled data did not come from the installed wheel: {info}")
        require(info["provenance"] == [None, None], info)
        print(json.dumps({"wheel_import": info, "exit": imported.returncode}))
        require(json.loads(guard_result.read_text(encoding="utf-8"))
                == {"loaded": True, "network_attempts": []},
                "network guard missing or a network call was attempted")
        out = outside / "reports"
        commands = [(["--help"], 0)]
        commands += [(["demo", "--scenario", scenario, "--output-dir", str(out)], expected)
                     for scenario, expected in (("baseline", 0), ("regression", 1), ("repaired", 0))]
        commands += [(["compare", str(out / "baseline.json"), str(out / "regression.json"),
                      "--output-dir", str(out)], 1)]
        commands += [(["evaluate", "--dataset", info["data"], "--predictions",
                      str(Path(info["data"]).parent / "predictions/repaired.json"),
                      "--policy", str(Path(info["data"]).parents[1] / "policy.json"),
                      "--output-dir", str(out)], 0)]
        for args, expected in commands:
            guard_result.unlink(missing_ok=True)
            completed = subprocess.run([cli, *args], cwd=outside, env=environment,
                                       capture_output=True, text=True, timeout=30)
            print(json.dumps({"command": [cli, *args], "exit": completed.returncode,
                              "expected": expected}))
            require(completed.returncode == expected, completed.stdout + completed.stderr)
            require(json.loads(guard_result.read_text(encoding="utf-8"))
                == {"loaded": True, "network_attempts": []},
                "network guard missing or a network call was attempted")
        for name, accepted in (("baseline", True), ("regression", False), ("repaired", True),
                               ("comparison", False), ("evaluation", True)):
            report = json.loads((out / f"{name}.json").read_text(encoding="utf-8"))
            require(report["gate"]["accepted"] is accepted, f"{name}: unexpected gate decision")
            require(report["provenance"]["code_revision"] is None,
                    f"{name}: a wheel install inherited a Git revision")
            require(report["provenance"]["working_tree_dirty"] is None,
                    f"{name}: a wheel install inherited a dirty-tree flag")
        print("PASS: wheel imports/resources, actual console entry point, credential-free "
              "socket/DNS instrumentation, and no unrelated Git provenance.")


if __name__ == "__main__":
    main()
