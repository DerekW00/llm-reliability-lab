"""Policy thresholds and adversarial replay checks using independent small cases."""

from __future__ import annotations

import copy
import json

import pytest
from test_evaluation import NULL_RECORD, OTHER, RECORD, artifacts, permissive

from reliability_lab.contracts import FIELDS, InputError
from reliability_lab.evaluation import evaluate
from reliability_lab.gate import MAX_BASELINE_DEPTH, compare_reports


def comparison_inputs(*, pairs=None):
    dataset, supplied, policy = artifacts(pairs)
    baseline_predictions = copy.deepcopy(supplied)
    for item, case in zip(baseline_predictions["predictions"], dataset["cases"], strict=True):
        item["record"] = copy.deepcopy(case["expected"])
        item["evidence"] = copy.deepcopy(case["evidence"])
    baseline_predictions["scenario"] = "independent baseline"
    return dataset, supplied, permissive(policy), baseline_predictions


def test_undefined_required_metrics_reject_even_at_zero_minimum():
    dataset, predictions, policy = artifacts([(NULL_RECORD, NULL_RECORD)])
    report = evaluate(dataset, predictions, permissive(policy))
    assert report["summary"]["exact_record_accuracy"] == 1
    assert report["gate"]["accepted"] is False
    assert len(report["gate"]["reasons"]) == 6
    assert all("undefined" in reason for reason in report["gate"]["reasons"])


def test_absolute_threshold_equality_passes_using_exact_counts():
    dataset, supplied, policy, _ = comparison_inputs(pairs=[(RECORD, RECORD)] * 19 + [(RECORD, OTHER)])
    policy.update(min_micro_f1=0.95, min_exact_record_accuracy=0.95, max_critical_failures=4)
    policy["min_field_f1"] = dict.fromkeys(FIELDS, 0.95)
    report = evaluate(dataset, supplied, policy)
    assert report["gate"]["accepted"] is True
    assert all(check["passed"] for check in report["gate"]["checks"])


def test_comparison_threshold_equality_uses_rational_drop():
    # One wrong supplier among 40 records: F1 199/200=.995, exact 39/40=.975.
    pairs = [(RECORD, RECORD)] * 39 + [(RECORD, {**RECORD, "supplier_name": "Other Studio"})]
    dataset, supplied, policy, baseline_predictions = comparison_inputs(pairs=pairs)
    baseline = evaluate(dataset, baseline_predictions, policy)
    candidate = evaluate(dataset, supplied, policy, baseline=baseline)
    assert candidate["gate"]["accepted"] is True
    assert candidate["gate"]["checks"][-2:] == [
        {"name": "micro_f1_drop", "passed": True, "actual": 0.005, "required": 0.005},
        {"name": "exact_record_accuracy_drop", "passed": True, "actual": 0.025, "required": 0.025},
    ]


def test_exact_accuracy_drop_from_975_to_95_passes_at_025():
    pairs = [(RECORD, RECORD)] * 38 + [
        (RECORD, {**RECORD, "supplier_name": "Other Studio"}),
        (RECORD, {**RECORD, "supplier_name": "Other Studio"}),
    ]
    dataset, supplied, policy, baseline_predictions = comparison_inputs(pairs=pairs)
    baseline_predictions["predictions"][-1]["record"]["supplier_name"] = "Other Studio"
    baseline = evaluate(dataset, baseline_predictions, policy)
    assert baseline["summary"]["exact_record_accuracy"] == 0.975
    candidate = evaluate(dataset, supplied, policy, baseline=baseline)
    assert candidate["summary"]["exact_record_accuracy"] == 0.95
    assert candidate["gate"]["accepted"] is True
    assert candidate["gate"]["checks"][-1] == {
        "name": "exact_record_accuracy_drop", "passed": True,
        "actual": 0.025, "required": 0.025,
    }


def test_comparative_rejection_is_preserved_on_replay():
    dataset, supplied, policy, baseline_predictions = comparison_inputs(pairs=[(RECORD, OTHER)])
    baseline = evaluate(dataset, baseline_predictions, policy)
    candidate = evaluate(dataset, supplied, policy)
    assert candidate["gate"]["accepted"] is True  # This deliberately lenient policy permits it.
    rejected = compare_reports(baseline, candidate)
    assert rejected["gate"]["accepted"] is False
    assert len(rejected["gate"]["reasons"]) == 2
    replayed = compare_reports(baseline, rejected)
    assert replayed["gate"] == rejected["gate"]
    assert replayed["summary"] == rejected["summary"]


def test_rejected_candidate_cannot_switch_to_easier_baseline():
    dataset, supplied, policy, baseline_predictions = comparison_inputs(pairs=[(RECORD, OTHER)])
    baseline = evaluate(dataset, baseline_predictions, policy)
    candidate = evaluate(dataset, supplied, policy)
    rejected = compare_reports(baseline, candidate)
    with pytest.raises(InputError, match="different baseline"):
        compare_reports(candidate, rejected)


def test_absolute_rejection_survives_comparison():
    dataset, supplied, policy = artifacts([(RECORD, OTHER)])
    baseline_predictions = copy.deepcopy(supplied)
    baseline_predictions["predictions"][0]["record"] = copy.deepcopy(RECORD)
    baseline = evaluate(dataset, baseline_predictions, policy)
    candidate = evaluate(dataset, supplied, policy)
    compared = compare_reports(baseline, candidate)
    assert compared["gate"]["accepted"] is False
    assert len(compared["gate"]["reasons"]) == 10


def test_baseline_identity_ignores_timing_and_code_metadata():
    baseline = evaluate(*artifacts())
    candidate = compare_reports(baseline, baseline)
    refreshed = copy.deepcopy(baseline)
    refreshed["provenance"].update(timestamp_utc="2026-09-11T12:00:00Z", evaluation_seconds=5.0,
                                   code_revision="a" * 40, working_tree_dirty=True)
    assert compare_reports(refreshed, candidate)["gate"]["accepted"] is True


@pytest.mark.parametrize("mutate", [
    lambda r: r["summary"]["micro"].update(tp=999),
    lambda r: r["summary"]["micro"].update(f1=0.2),
    lambda r: r["summary"].update(exact_record_count=True),
    lambda r: r["summary"].update(schema_valid=1),
    lambda r: r["summary"].update(coverage_complete=1),
    lambda r: r["summary"].update(critical_failure_count=False),
    lambda r: r["fields"]["invoice_id"].update(f1=True),
    lambda r: r["fields"]["invoice_id"].update(tp=1.0),
    lambda r: r["gate"].update(accepted=1),
    lambda r: r["gate"]["checks"][0].update(passed=1),
    lambda r: r["gate"]["checks"].pop(),
    lambda r: r["gate"]["reasons"].append("unearned rejection"),
    lambda r: r.update(report_version=True),
    lambda r: r.update(scenario="modified only in report"),
    lambda r: r.update(extra="unknown"),
    lambda r: r["summary"].update(extra="unknown"),
    lambda r: r["provenance"].update(dataset_sha256="0" * 64),
    lambda r: r["provenance"].update(live_calls=0),
    lambda r: r["provenance"].update(evaluation_seconds=True),
    lambda r: r["provenance"].update(evaluation_seconds=float("nan")),
    lambda r: r["provenance"].update(timestamp_utc="not a date"),
    lambda r: r["provenance"].update(model="model-name"),
    lambda r: r["artifacts"]["predictions"]["predictions"][0]["record"].update(invoice_id="changed"),
    lambda r: r["artifacts"].update(extra={}),
])
def test_tampered_or_wrong_type_reports_are_input_errors(mutate):
    baseline = evaluate(*artifacts())
    candidate = copy.deepcopy(baseline)
    mutate(candidate)
    with pytest.raises(InputError):
        compare_reports(baseline, candidate)


def test_tampered_failed_gate_and_diff_are_rejected():
    dataset, supplied, policy, baseline_predictions = comparison_inputs(pairs=[(RECORD, OTHER)])
    baseline = evaluate(dataset, baseline_predictions, policy)
    rejected = evaluate(dataset, supplied, policy, baseline=baseline)
    forged = copy.deepcopy(rejected)
    forged["gate"]["accepted"] = True
    forged["gate"]["reasons"] = []
    with pytest.raises(InputError):
        compare_reports(baseline, forged)
    forged = copy.deepcopy(rejected)
    forged["diffs"][0]["evidence"]["expected"] = [2]
    with pytest.raises(InputError):
        compare_reports(baseline, forged)


@pytest.mark.parametrize("dimension", ["dataset", "policy", "mode"])
def test_incompatible_reports_fail_explicitly(dimension):
    baseline = evaluate(*artifacts())
    dataset, predictions, policy = artifacts()
    if dimension == "dataset":
        dataset["cases"][0]["document"] += "\nA new fact changes content identity."
    elif dimension == "policy":
        policy["min_micro_f1"] = 0.97
    else:
        predictions["mode"] = "synthetic_fixture"
    with pytest.raises(InputError, match="incompatible"):
        compare_reports(baseline, evaluate(dataset, predictions, policy))


def test_baseline_must_be_accepted_and_it_is_also_validated():
    rejected = evaluate(*artifacts([(RECORD, OTHER)]))
    with pytest.raises(InputError, match="baseline must be accepted"):
        compare_reports(rejected, rejected)
    rejected["gate"]["accepted"] = True
    with pytest.raises(InputError, match="inconsistent"):
        compare_reports(rejected, evaluate(*artifacts()))


def test_report_cycle_and_deep_baseline_chains_are_input_errors():
    baseline = evaluate(*artifacts())
    cyclic = copy.deepcopy(baseline)
    cyclic["artifacts"]["baseline"] = cyclic
    with pytest.raises(InputError, match="cyclic"):
        compare_reports(baseline, cyclic)
    nested = baseline
    for _ in range(MAX_BASELINE_DEPTH):
        # Valid construction adds a report each time. The next replay must
        # reject the oversized chain before uncontrolled Python recursion.
        parent = copy.deepcopy(baseline)
        parent["artifacts"]["baseline"] = nested
        nested = parent
    with pytest.raises(InputError, match="nesting"):
        compare_reports(baseline, nested)


def test_comparison_never_emits_an_unreplayable_depth():
    candidate = evaluate(*artifacts())
    baseline = candidate
    for _ in range(MAX_BASELINE_DEPTH - 1):
        baseline = compare_reports(baseline, candidate)
    assert baseline["gate"]["accepted"] is True
    with pytest.raises(InputError, match="nesting"):
        compare_reports(baseline, candidate)


def test_very_large_integer_provenance_duration_does_not_overflow():
    baseline = evaluate(*artifacts())
    baseline["provenance"]["evaluation_seconds"] = 10 ** 500
    # Integers are finite JSON numbers; duration metadata is not an attestation.
    assert compare_reports(baseline, baseline)["gate"]["accepted"] is True


def test_json_round_trip_and_shuffled_artifacts_replay():
    original = evaluate(*artifacts([(RECORD, RECORD), (OTHER, OTHER)]))
    shuffled = json.loads(json.dumps(original, allow_nan=False))
    shuffled["artifacts"]["dataset"]["cases"].reverse()
    shuffled["artifacts"]["predictions"]["predictions"].reverse()
    result = compare_reports(original, shuffled)
    assert result["gate"]["accepted"] is True
    assert result["summary"] == original["summary"]


def test_comparison_does_not_mutate_report_inputs():
    baseline = evaluate(*artifacts())
    candidate = copy.deepcopy(baseline)
    before = copy.deepcopy((baseline, candidate))
    compare_reports(baseline, candidate)
    assert (baseline, candidate) == before
