# LLM Reliability Lab

Catch a harmful invoice-extraction change before it passes a release gate.
A numeric conversion turns invoice ID `000482` into `482`. The output still
satisfies the schema, but it names a different invoice. This Python CLI shows how
field-level evaluation, critical-error checks and baseline comparison expose that
change and verify its repair.

**Synthetic fixture evaluation.** These are fictional documents and authored
predictions. No LLM runs, credentials or paid APIs are involved. The scores
demonstrate evaluation mechanics and a simulated postprocessing regression;
they do not measure a real model or establish production outcomes.

## Actual results

All scenarios use the same 40 evaluation documents, labels, normalizers and policy.
The baseline deliberately misspells one noncritical supplier name. Repaired
preserves that imperfection, making the targeted repair visible.

| Fixture | Micro precision / recall / F1 | Exact records | Critical errors | Exit |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 99.4536% | 39/40 (97.5%) | 0 | 0 — accepted |
| Regression | 95.0820% | 31/40 (77.5%) | 8 | 1 — rejected |
| Repaired | 99.4536% | 39/40 (97.5%) | 0 | 0 — accepted |

Precision and recall happen to be equal here; they are computed separately and
differ on asymmetric errors. See [generated reports](examples/reports/) for full
counts, all differences, gate reasons and embedded inputs.

## Five-minute quickstart

Prerequisites: [uv](https://docs.astral.sh/uv/getting-started/installation/) and
Python 3.12.14. If needed, `uv python install` installs the version recorded in
`.python-version`. Dependency installation can use the network; running the
application uses local files only. Tested locally with uv 0.12.8.

Clone the repository and enter its directory:

```sh
git clone https://github.com/DerekW00/llm-reliability-lab.git
cd llm-reliability-lab
```

Then run these commands **one at a time**:

```sh
uv sync --frozen
uv run reliability-lab demo --scenario baseline
uv run reliability-lab demo --scenario regression
uv run reliability-lab demo --scenario repaired
uv run reliability-lab compare reports/baseline.json reports/regression.json
uv run pytest
```

Regression and its comparison intentionally return **exit 1**. Baseline, repaired,
sync and pytest return **0**. Tests assert that the regression is rejected, so the
suite passes. **Exit 2** means invalid input or execution error, not a quality
verdict. Scripts that stop on nonzero exits should use the checked rejection
block in [the full quickstart](docs/quickstart.md).

Reports are printed to the terminal and saved as JSON and Markdown in `reports/`.
Selected lines from the generated regression report:

```text
**SYNTHETIC FIXTURE EVALUATION**
Authored fixtures, no live model calls. These scores are not model accuracy or production evidence.
**Decision: REJECTED**
Critical failures: **8 field mismatches** (not a count of records).
```

For an explicit offline runtime check and lint:

```sh
uv run --offline python scripts/verify_offline.py
uv run ruff check .
```

The offline check removes API credentials and instruments Python socket/DNS calls
to fail in each CLI subprocess, including execution outside the repository.
It is runtime instrumentation, not an operating-system firewall.

## What the evaluator checks

- **Complete, valid inputs:** every case needs exactly one prediction; missing,
  duplicate, unknown or malformed records are errors. No dropped denominators.
- **Value correctness:** per-field and micro precision, recall and F1; exact
  record accuracy; null/abstention counts; evidence-linked differences.
  Incorrect non-null values count as both false positives and false negatives.
- **A frozen policy:** zero critical errors in ID, currency, amount or due date;
  F1 at least .98 overall and .90 per field; exact accuracy at least .95.
  Candidate F1 may drop at most .005 and exact accuracy at most .025 from baseline.
- **Replayable comparisons:** reports embed their inputs. Comparison recomputes
  metrics and gates, checks compatibility, and preserves rejection. Changing a
  stored acceptance flag or score is an input error.

Evaluate conforming files through the same interface:

```sh
uv run reliability-lab evaluate \
  --dataset data/evaluation.json \
  --predictions data/predictions/repaired.json \
  --policy policy.json --baseline reports/baseline.json \
  --output-dir reports/custom --name candidate
```

This example still reads synthetic fixtures. User-supplied files can use
`external_predictions` mode without a provider connection.

## Architecture and limits

`contracts.py` validates strict JSON, exact decimal money, dates and line evidence.
`evaluation.py` counts field outcomes; `gate.py` applies policy and replays reports.
`cli.py` and `reporting.py` expose commands and readable artifacts. Frozen data is
bundled in wheel installs. The runtime has no third-party dependencies.

The corpus contains 20 primary development cases, 40 evaluation cases and a
separately frozen two-case development supplement for duplicate-looking invoices.
It covers missing fields, ambiguous dates, zero totals, conflicting currency,
distractor amounts, formatting changes and instruction-like document text.
Labels are agent-authored and agent-reviewed synthetic references. Fixtures may
start from labels during their documented construction; the evaluator never
generates predictions or copies labels into them.

This is a deterministic evaluation harness, not an extractor, prompt-injection
defense benchmark or production-ready finance system. There is no OCR, PDF parser,
live provider adapter, statistical generalization claim or semantic evidence judge.
Evidence references validate line locations, not entailment. Four currencies and
nonnegative, two-place amounts are supported. Policy thresholds are illustrative.
The [GitHub Actions workflow](https://github.com/DerekW00/llm-reliability-lab/actions/workflows/ci.yml)
checks lint, tests, offline execution and the installed wheel. No hosted application
or package release is provided.

Read [SPEC.md](SPEC.md), [dataset](docs/dataset.md), [evaluation](docs/evaluation.md),
[walkthrough](docs/walkthrough.md), [independent review](docs/review.md), [Opus repair review](docs/claude-review.md), and
[FINAL_REPORT.md](FINAL_REPORT.md) for the contract and verified local handoff.
Construction details are in [reproducibility](docs/reproducibility.md).
Commit dates follow a documented [reconstructed two-week timeline](docs/history-timeline.md);
the original signed history and actual build dates are preserved.
Original project contents use the [MIT license](LICENSE).
