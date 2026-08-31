# Reproduce and interpret this local build

Use Python 3.12.14 (recorded in `.python-version`) and uv 0.12.8, the uv version
used for this build. `uv sync --frozen` installs the dependency versions and
registry artifact hashes in `uv.lock`. The runtime uses only Python's standard
library. Test tools are locked, and the build backend plus its transitive build
requirements are explicitly pinned in `pyproject.toml`.

Installation can access official package registries and Python release hosts.
Application execution needs no network or model credentials. After installation,
run `uv run --offline python scripts/verify_offline.py`. This executes each CLI
scenario and a rejected comparison in separate Python processes, outside the
repository working directory. Each process has socket connect/DNS functions
patched to raise, and API-key/token environment variables filtered out. This is
runtime instrumentation, not an operating-system network firewall. Tests apply
the same prohibition within the test process. The application has no provider
adapter or command capable of model inference.

The CI action references were checked against the official
[uv GitHub Actions guide](https://docs.astral.sh/uv/guides/integration/github/).
Actions are pinned to commit hashes; the uv executable is pinned to the version
used locally. The workflow installs prerequisites, runs lint and pytest, checks
the CLI's expected rejection signals under the offline instrumentation, and
builds distributions. Configuration does not imply a remotely executed CI run.

Content fingerprints identify validated dataset, predictions and policy JSON,
with object keys and case arrays ordered deterministically. The dataset manifest
separately identifies exact frozen file bytes. Metric and decision comparisons
exclude timestamps, local duration, revision and working-tree status. Reordered
case arrays produce the same results. Edits to labels or documents change the
dataset fingerprint and make baseline comparison incompatible.

Generated reports contain embedded source artifacts for replay and validation.
They are not signed attestations: someone who replaces every embedded artifact
and computes a matching report can create a different valid experiment. Compare
the frozen manifest and known repository revision when reviewing provenance.

Python evaluation timing describes fixture grading or supplied-prediction grading;
it is not model latency. Provider/model fields are null and `live_calls` is false.
