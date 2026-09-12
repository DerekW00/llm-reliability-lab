# Walkthrough: catch a formatting regression that changes identity

**Synthetic fixture evaluation.** This local demonstration uses newly authored,
fictional documents and fixed predictions. It does not run an LLM. Fixture authors
may use the labels to construct stored predictions; that is fixture construction,
not independent evidence of extraction accuracy.

## Follow the same input through three scenarios

1. Run `uv run --frozen reliability-lab demo --scenario baseline`. The baseline
   predictions retain one deliberate supplier-name error on the evaluation set.
   The gate checks absolute policy thresholds without a comparison baseline.
2. Run `uv run --frozen reliability-lab demo --scenario regression`. This is
   expected to exit 1. A numeric-coercion bug treats purely numeric invoice IDs
   as numbers and removes leading zeros. In actual case EVAL-01,
   `000482` becomes `482`; those are different IDs under the contract.
3. Run `uv run --frozen reliability-lab demo --scenario repaired`. Removing
   numeric coercion preserves the original string IDs. The same supplier-name
   imperfection remains. The repaired demo should pass the original policy and
   the comparison checks.

Allow about one minute per scenario and two minutes for the evidence and limits.
The computed baseline and repaired micro F1 is 99.4536%, with 39/40 exact records
and zero critical failures. The regression has 95.0820% micro F1, 31/40 exact
records and eight critical ID failures. Open EVAL-01 to connect its source line
to the changed identifier, then point to the original policy file: the repair
passes without label or threshold edits.

Run these separately, or use the expected-rejection shell block in
[quickstart.md](quickstart.md). Every candidate demo computes a baseline report
from the same input dataset and policy before comparison. Scenario names are
metadata: the evaluator measures the supplied record values and never grants a
pass because a scenario is called `baseline` or `repaired`.

## Read the evidence before the verdict

Open `reports/regression.md`. The report starts with the fixture disclosure and
the gate decision. Coverage shows every case and prediction; malformed or
incomplete inputs fail before a quality report is produced. The metrics include
integer confusion counts and the denominators used for precision, recall, F1,
and exact-record accuracy. Correct abstention contributes a true negative, not
a true positive. An undefined required metric is `null` and rejects the gate.

The gate checks absolute limits and allowed drops against an accepted baseline.
Invoice ID, currency, total amount, and due date are critical fields under the
bundled policy. A single mismatch in these fields exhausts its zero-error budget,
even if aggregate F1 remains high. A critical failure count counts field mismatches;
one document can contribute more than one. Every failed policy rule is reported.

The representative differences show critical errors first, including expected and
actual values, a failure category, source line numbers, excerpts, and an action.
The ID regression is categorized as `identifier_format`. Its repair is concrete:
preserve invoice IDs as strings through postprocessing. The Markdown shows at most
10 differences; the JSON contains the complete list. A valid evidence line number
is useful for auditing, but does not itself establish that the prediction is correct.

## Reproduce and challenge a result

The JSON report embeds its validated dataset, predictions, policy, and any
comparison baseline. Fingerprints identify content; timestamps, code revision,
working-tree status, Python version, and evaluation time describe the run. Timing
is local fixture scoring time, never model latency. A saved report is a reproducibility
artifact, not a signed attestation. `compare` re-evaluates embedded artifacts and
rejects inconsistent or incompatible reports instead of trusting supplied totals.

To try a different failure, copy a prediction file, change an explicit critical
value while retaining a structurally valid record and evidence reference, and
evaluate the copy using the original dataset and policy. A new critical mismatch
must reject regardless of its scenario label. Harmless formatting accepted by
the frozen normalizers, such as outer whitespace around an invoice ID, must not
create an error. Keep the original dataset, policy, and fixtures intact so the
comparison remains meaningful.

This bounded schema excludes unsupported currencies, credits, line items, and
tax reconciliation. The small fictional dataset, authored predictions, illustrative
thresholds, and deterministic local scoring demonstrate an evaluation workflow.
They do not establish statistical generalization, production readiness, or a
specific model's performance. Actual numerical results belong in the generated
reports and the integrated project result summary.
