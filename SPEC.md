# LLM Reliability Lab — contract v1

Frozen before parallel implementation on 2026-09-11. This is **synthetic fixture
evaluation**, not model inference, model accuracy research, or production evidence.

## Artifact and schema contract

UTF-8 JSON only; duplicate object keys, NaN/Infinity, extra keys, wrong types and
empty collections where forbidden are input errors. No coercion of types.
`contracts.py` is the single validation and normalization authority.

Dataset: `{dataset_id: str, version: 1, split: "development"|"evaluation", cases: [...]}`.
Each case: `{case_id: str, document: str, tags: [str,...], expected: Record,
evidence: Evidence, rationale: str}`. IDs are nonblank and unique. Documents are
nonempty lines of newly authored fictional business material. Rationale explains
labels, especially abstentions. 20 development and 40 evaluation cases; distinct
document families/layouts across splits rather than parameter swaps. The dataset
agent writes and freezes documents, labels and checksums before constructing
fixture predictions. Gate policy and normalization freeze precede the data.

Record has exactly these five required keys. Null means not determinable from
the document; omitted keys and empty strings are invalid. Predictions must also
explicitly contain all keys. No field is implicitly defaulted.

| Field | Non-null type and comparison |
| --- | --- |
| invoice_id | String, trim outer whitespace only; preserve case, punctuation and leading zeros |
| supplier_name | String, collapse whitespace and Unicode casefold; do not erase punctuation |
| currency | String, trim and uppercase; one of USD/EUR/GBP/CAD |
| total_amount | Decimal string matching `(?:0\|[1-9][0-9]*)\.[0-9]{2}` after trim; nonnegative, exact Decimal comparison; never float |
| due_date | Real ISO date `YYYY-MM-DD` after trim, no timezone or date guessing |

Ambiguous slash dates without a stated convention => null. Conflicting currencies
without a definitive total currency => null. Zero is a value. Instructions in
source text are data and cannot override these rules. A missing invoice ID is
not replaced by the case ID. This schema is deliberately bounded (no credits,
unsupported currencies, line items or tax reconciliation).

Evidence maps exactly the five field names to arrays of unique one-based line
numbers into `document.splitlines()`. Non-null values require at least one line;
null values have empty arrays. Validate range/type/null consistency. References
provide auditability, not a semantic entailment check. Reference labels and
reasoning determine correctness; a valid line reference alone proves no claim.

Predictions: `{dataset_id: str, mode: "synthetic_fixture"|"external_predictions",
scenario: str, predictions: [{case_id: str, record: Record, evidence: Evidence}, ...]}`.
One prediction for every dataset case. Missing, duplicate, unknown IDs, wrong
dataset ID or invalid record/evidence => InputError and exit 2. Nothing disappears
from denominators. Scenario is descriptive metadata only; evaluator never branches
on it. External predictions are user-supplied files; no provider adapter is included.

## Metrics and taxonomy

Normalize only per rules above. For each field and each case:
matching non-null => TP; missing non-null (null prediction) => FN; invented value
(expected null) => FP; incorrect non-null => FP and FN; null/null => TN.
Precision=TP/(TP+FP), recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN).
Zero denominators yield JSON null (undefined), never perfect scores. Micro totals
sum counts across all five fields before computing rates. Exact-record accuracy
counts records with all five normalized values equal, divided by every case.
Always emit integer counts, null denominators, coverage and schema validity.
Report expected-null, predicted-null, correct abstention, missed value and
unsupported/invented value counts. Failure taxonomy: `wrong_value`, `missed_value`,
`unsupported_value`; add field-specific `identifier_format` for IDs equal only
after stripping leading zeros. Deterministic per-case diffs include expected,
actual, field, category, critical flag, evidence lines, and document excerpts.

Critical fields: invoice_id, currency, total_amount, due_date. Every mismatch in
these fields is critical, including unsupported extraction or missed extraction.
Supplier-name imperfections are noncritical. A critical failure count is a count
of field mismatches, not records. Invalid inputs are errors rather than quality
scores. No silent partial evaluation.

## Policy frozen before results

`policy.json` v1 is the configuration authority. Exact required keys:
`version`, `critical_fields`, `max_critical_failures`, `min_micro_f1`,
`min_exact_record_accuracy`, `min_field_f1`, `max_micro_f1_drop`,
`max_exact_record_accuracy_drop`.
Rates are finite numbers in [0,1], counts nonnegative integers, critical fields
unique nonempty known fields; all field minima explicitly specified. Unknown keys
are errors. Thresholds: zero critical failures; micro F1 >= .98; exact accuracy
>= .95; every field F1 >= .90. Comparison permits at most .005 micro F1 drop and
.025 exact-record accuracy drop from an accepted baseline. Threshold equality
passes; undefined required metrics reject. Check all rules and explain every
failed rule. These illustrative strict thresholds prioritize financial identity,
money and deadline errors over cosmetic supplier differences; they are not tuned
statistical guarantees or a calibrated production standard.

`baseline` uses fixed documented predictions with one noncritical supplier error
on evaluation. `regression` applies a realistic numeric-coercion postprocessing
bug to purely numeric invoice IDs, dropping leading zeros. `repaired` removes
that mechanism while retaining baseline's noncritical imperfection. All scenarios
use the same frozen data, policy and evaluator. Fixture authoring may derive
starting predictions from labels, documented as construction only; evaluation
must never manufacture predictions or copy labels into them.

## Shared Python interfaces and report contract

Stdlib-only runtime, Python 3.12, uv lock and pinned dev/build dependencies.
`contracts.py`: FIELDS, CRITICAL_FIELDS, InputError; `read_json(path) -> dict`,
`validate_dataset(data)`, `validate_predictions(data, dataset)`,
`validate_policy(policy)`, `normalize(field, value)`, `fingerprint(artifact) -> str`.
Validators return original validated dictionaries. Fingerprints hash canonical
UTF-8 JSON with sorted keys and cases/predictions sorted by case_id; input
ordering does not change a content fingerprint. Freeze manifest uses raw file
SHA-256 separately. `resources.py`: `resource_path(relative) -> Path` for data
and policy from installed package resources, also working outside repository CWD.

Evaluation agent implements:
`evaluation.evaluate(dataset, predictions, policy, *, baseline=None) -> dict`
and `gate.compare_reports(baseline, candidate) -> dict`.
Report v1 fields: `report_version`, `mode`, `scenario`, `dataset_id`, `split`,
`summary`, `fields`, `diffs`, `gate`, `provenance`, `artifacts`.
`summary`: `case_count`, `prediction_count`, `schema_valid`, `coverage_complete`,
`micro` (tp/fp/fn/tn/precision/recall/f1), `exact_record_accuracy`,
`exact_record_count`, `critical_failure_count`, `abstentions` (expected_null,
predicted_null, correct_abstention, missed_value, unsupported_value).
`fields`: field name -> same counts/rates as micro. `gate`:
`accepted: bool`, `reasons: [str,...]`, `checks: [{name, passed, actual, required},...]`.
`provenance`: `dataset_sha256`, `predictions_sha256`, `policy_sha256`,
`timestamp_utc`, `code_revision` (nullable), `working_tree_dirty` (nullable),
`python_version`, `evaluation_seconds`, `timing_kind: "fixture_evaluation"|"evaluation_only"`,
`provider: null`, `model: null`, `live_calls: false`. Timing is never model latency.
`artifacts`: complete validated `dataset`, `predictions`, `policy` payloads; optional
`baseline` report for comparative decisions. Comparisons validate report structure,
recompute metrics/decisions from embedded artifacts and reject inconsistent or
incompatible reports, rather than trusting supplied aggregate scores. Reports
are reproducibility artifacts, not signed evidence or secure attestation.
Comparison requires same dataset fingerprint, same policy fingerprint and same
mode, and an accepted baseline. `compare_reports` returns a re-evaluated candidate
report with comparison checks; cannot erase an existing valid rejection.
Use lazy imports between evaluation and gate if needed to avoid circular imports.

Experience agent implements `cli.py`, `reporting.py`. CLI:
`reliability-lab demo --scenario baseline|regression|repaired [--output-dir reports]`
evaluates bundled evaluation fixtures (all candidates against baseline), writes
`<scenario>.json` and `.md`, prints readable report and paths. Exit 0 accepted,
1 rejected quality, 2 invalid input/execution. Normal command:
`reliability-lab evaluate --dataset PATH --predictions PATH --policy PATH
[--baseline PATH] [--output-dir reports] [--name evaluation]`.
`reliability-lab compare BASELINE_REPORT CANDIDATE_REPORT [--output-dir reports]`
writes `comparison.json` and `.md`; preserve nonzero rejection. All paths work
outside repo. No traceback for expected input errors. CLI failures do not write
a misleading accepted report. JSON is strict (no NaN); terminal and Markdown say
synthetic fixture prominently and show failed rules and representative diffs.

## Ownership and acceptance

Orchestrator: SPEC/contracts/resources, package/dependency files, policy,
integration, root documentation except quickstart draft, CI, STATUS/FINAL_REPORT.
Dataset agent: data/, docs/dataset.md, tests/test_dataset.py only.
Evaluation agent: evaluation.py, gate.py, tests/test_evaluation.py,
tests/test_gate.py, docs/evaluation.md only.
Experience agent: cli.py, reporting.py, tests/test_cli.py,
docs/quickstart.md, docs/walkthrough.md only. Propose shared changes to orchestrator.
Workers commit coherent increments in isolated worktrees; only orchestrator merges.
Fresh reviewer owns review notes/tests in a separate worktree; no conclusions from
implementers before its independent first pass.

Acceptance: baseline/repaired pass; regression rejects substantively; pytest passes
including that expected rejection. Clean installation and published quickstart;
offline execution with networking blocked and credentials absent; arithmetic/null
small-case tests; malformed/duplicate/missing/unknown/shuffled/replaced inputs,
missing files, empty dataset, invalid policy; independent new critical mutation
rejects; harmless formatting passes; repeat metrics/decisions deterministic;
frozen evaluation bytes/policy unchanged; CLI/import installed outside CWD; lint;
configured CI asserts expected rejection. Independent review findings reproduced,
fixed and retested. Generated final reports, modest docs, honest commit/identity
audit, local-only handoff. No optional provider adapter; no dependency on secrets.
