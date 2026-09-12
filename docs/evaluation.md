# Evaluation and release gate

This evaluator scores supplied predictions against reference labels. Bundled
scenarios are synthetic fixtures, not model runs. External prediction mode reads
the same bounded schema without making provider calls. Scenario names are metadata
and never select evaluation behavior.

## Counting and normalization

Each case contributes all five fields. A matching non-null value contributes a
true positive (TP); a missed value contributes a false negative (FN); a value
invented where the reference is null contributes a false positive (FP); an
incorrect non-null value contributes both FP and FN. Null/null contributes a true
negative (TN). The evaluator reports each count as an integer.

Precision is `TP / (TP + FP)`, recall is `TP / (TP + FN)`, and F1 is
`2 TP / (2 TP + FP + FN)`. A zero denominator produces JSON `null`, including
all-abstention fields. Micro rates use summed field counts, not averages of field
rates. Exact-record accuracy counts records whose five normalized fields all
match, including correct abstentions. It always divides by the entire dataset.
Abstention counts separately expose expected nulls, predicted nulls, correct
abstentions, missed values, and unsupported values.

`contracts.py` owns validation and normalization: only outer whitespace is removed
from invoice IDs; supplier whitespace is collapsed and Unicode casefolded;
currencies are uppercased; amounts use exact `Decimal` values; dates must be valid
ISO calendar dates. IDs preserve leading zeros. Null is distinct from zero.
Invalid or incomplete inputs raise `InputError`; no cases disappear from scores.
Successful reports therefore explicitly record complete coverage and valid schema.

Diffs sort by case ID and then the fixed field order. Their keys are `case_id`,
`field`, `expected`, `actual`, `category`, `critical`, `evidence`, and
`document_excerpts`. Expected and actual values retain the original artifact text;
normalization determines equality. `evidence` maps `expected` and `actual` to sorted
line-number arrays. `document_excerpts` maps those sides to `{line, text}` objects.
Categories are `wrong_value`, `missed_value`, and `unsupported_value`; invoice IDs
equal only after stripping leading zeros use `identifier_format`. Evidence links
make a mismatch inspectable; they do not establish semantic correctness by
themselves. Critical failures count mismatched fields selected by the policy,
including missed and unsupported values, rather than counting affected records.

## Policy and comparison

The unchanged bundled policy allows zero critical mismatches, requires micro F1
at least .98, exact-record accuracy at least .95, and each field F1 at least .90.
Allowed drops from baseline are .005 micro F1 and .025 exact-record accuracy.
These illustrative thresholds prioritize identity, money and deadlines while
allowing limited supplier-name imperfection. They are not calibrated against a
deployment population. `policy.json` and its original SHA-256 in the dataset
manifest establish the pre-results choice.

The policy file supplies every threshold and the critical-field set. The gate
checks critical failures, micro F1, exact-record accuracy, and all five field F1
minima. It retains every failed rule. An undefined required F1 rejects even when
its minimum is zero. Threshold equality passes. Decisions compare exact count
fractions against the policy's decimal number representation, so binary floating
point subtraction cannot turn an allowed boundary drop into a rejection.

`evaluate(dataset, predictions, policy, baseline=None)` returns an absolute report.
With a baseline, it returns a comparison report. `compare_reports(baseline,
candidate)` validates and recomputes both reports from their embedded dataset,
predictions, policy, and optional baseline. It checks the supplied summary, field
metrics, diffs, gate rules, decision, identity metadata, and artifact hashes against
recomputed values. Unknown keys, changed counts, altered decisions, malformed
provenance, booleans substituted for numeric values, and inconsistent evidence are
input errors, rather than quality rejections.

A comparison requires identical dataset and policy content fingerprints, identical
prediction modes, and an accepted baseline. It adds micro F1 and exact-record
accuracy drop checks to every absolute check. A candidate already compared against
a baseline can be replayed against that same baseline; its valid rejection remains
a rejection. A different baseline is an input error. Baseline identity includes
artifact fingerprints, recomputed metrics and gates, and recursive comparison
history, while ignoring timestamps, timing, and code-revision metadata.

Reports may embed up to 16 report levels, including the outer report; cyclic
objects and JSON nesting beyond 128 levels are rejected. These are bounded local
replay artifacts, not a general unbounded historical report database.

## Provenance and limits

Each report embeds independent copies of its validated inputs. Content hashes use
the shared canonical fingerprint function, which ignores case/prediction array
ordering. These hashes differ from the raw file hashes used to freeze fixture
bytes. Replay recomputes hashes, metrics, diffs, and policy decisions; changes to
source labels together with consistently regenerated reports can still produce a
valid report. Reports are reproducibility artifacts, not signed evidence or secure
attestation of what an external system produced.

Code provenance looks up the tracked evaluator source file's Git checkout,
independent of the caller's working directory and `GIT_*` overrides. Revision and
dirty state are null when the module is installed without a tracked source
checkout, including a wheel installed inside an unrelated repository. Git status
includes untracked files. This records available source context; it is not a code
integrity signature.

`evaluation_seconds` measures local report construction and provenance collection,
not inference or model latency, and excludes the additional comparison replay
work. `timing_kind` is `fixture_evaluation` for synthetic fixtures or
`evaluation_only` for external predictions. Provider and model remain null and
`live_calls` remains false. Reports also include the UTC generation timestamp and
Python version. Provenance metadata is validated for shape and consistency, but
the evaluator cannot verify the historical truth of another report's timestamp
or claimed source revision.

The unit tests use independently authored small records for confusion-matrix
arithmetic, null denominators, normalization, threshold equality, critical fields,
report tampering, compatibility, baseline rejection preservation, and recursion
bounds. They do not rely on the bundled scenario fixture scores.
