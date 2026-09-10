# Quickstart

This is **synthetic fixture evaluation**, using authored fictional invoice documents
and stored predictions. It makes no live model calls, needs no credentials, and
does not measure model accuracy or production reliability.

## Install and run

Open a shell in the repository checkout. Python 3.12 and `uv` are required. The
first sync may download the pinned development/build tools; subsequent evaluation
uses local files and the Python standard library only.

```sh
uv sync --frozen
uv run --frozen reliability-lab demo --scenario baseline
uv run --frozen reliability-lab demo --scenario repaired
```

Each command prints its computed report and writes `reports/<scenario>.json` and
`reports/<scenario>.md`. Baseline and repaired are expected to exit **0** (accepted).
Both retain the same deliberate, noncritical supplier-name imperfection. Regression
is expected to exit **1** (quality rejected): numeric coercion strips leading zeros
from invoice IDs. Repaired removes that mechanism. Candidate demos compute their
comparison baseline from the same bundled dataset, policy, and evaluator on each run.

An expected rejection needs explicit handling in scripts that stop on errors:

```sh
if uv run --frozen reliability-lab demo --scenario regression; then
    echo "ERROR: the regression unexpectedly passed" >&2
    exit 1
else
    regression_status=$?
    if [ "$regression_status" -ne 1 ]; then
        echo "ERROR: evaluation failed to execute (status $regression_status)" >&2
        exit "$regression_status"
    fi
fi
```

Read `reports/regression.md` for failed rules and critical examples. Read the JSON
for every field difference, complete embedded inputs, and content fingerprints.
All displayed scores are computed from the selected inputs. Rates include their
numerators and denominators; `null` means a metric is undefined.

## Evaluate supplied predictions

Inputs must follow [SPEC.md](../SPEC.md). Missing predictions, unknown case IDs,
duplicate JSON keys, invalid values, and invalid evidence references are errors;
the evaluator does not silently drop records or invent missing predictions.

```sh
uv run --frozen reliability-lab evaluate \
    --dataset data/evaluation.json \
    --predictions data/predictions/repaired.json \
    --policy policy.json \
    --baseline reports/baseline.json \
    --output-dir reports/custom \
    --name candidate
```

Omit `--baseline` for a policy-only evaluation. `--name` is a filename stem of
letters, digits, underscores, and hyphens, starting with a letter or digit. It is
limited to 100 characters and cannot contain a path. Outputs cannot overwrite
the supplied dataset, predictions, policy, or baseline report. Reusing an output
name replaces whatever file is at that name when publication succeeds. If the new
evaluation fails, its reserved old outputs
are removed so an old acceptance does not appear to describe the failed run. That
removal is best effort: a reserved output that cannot be read, or that is not
recognisable as a report written here, is deliberately left alone rather than
deleted, and the error message names every file kept for that reason.
If publication fails partway through, newly published files are removed; unrelated
files that were never replaced are preserved. Cleanup is best effort in this case
too. Diagnostics go to stderr; redirecting stderr hides those details, while exit 2
still identifies a failed execution.

## Compare saved reports

```sh
uv run --frozen reliability-lab compare \
    reports/baseline.json reports/repaired.json \
    --output-dir reports/comparison
```

This writes `comparison.json` and `comparison.md` in the chosen directory. The
comparison validates and recomputes reports from their embedded inputs. It requires
the same dataset content, policy, mode, and an accepted baseline. Comparing the
regression report returns **1**; handle that status as in the regression demo above.

| Exit | Meaning |
| --- | --- |
| 0 | Evaluation completed and every required quality check passed |
| 1 | Evaluation completed and quality was rejected; inspect report reasons |
| 2 | Invalid input or execution error; no new quality verdict was published |

The installed command also works outside the repository. After the sync above,
use the checkout's absolute virtual-environment command path. Start this example
in the repository checkout:

```sh
lab_checkout=$(pwd)
cd /tmp
"$lab_checkout/.venv/bin/reliability-lab" demo \
    --scenario baseline --output-dir /tmp/reliability-lab-example
```

To check the assembled project from its checkout:

```sh
uv run --frozen pytest
uv run --frozen ruff check .
```

The test suite asserts that the regression is rejected; that expected result does
not make pytest fail. See [walkthrough.md](walkthrough.md) for the mechanism and
limits, and the generated reports for the actual current scores.
