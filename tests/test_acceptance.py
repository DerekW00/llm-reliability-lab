"""Integrated release behavior over the same frozen inputs and policy."""

from copy import deepcopy

import pytest

from reliability_lab.contracts import InputError, read_json
from reliability_lab.evaluation import evaluate
from reliability_lab.gate import compare_reports
from reliability_lab.resources import resource_path


def inputs(scenario="baseline"):
    return (read_json(resource_path("data/evaluation.json")),
            read_json(resource_path(f"data/predictions/{scenario}.json")),
            read_json(resource_path("policy.json")))


def stable(report):
    return {key: report[key] for key in ("summary", "fields", "diffs", "gate")}


def test_same_evaluator_and_policy_exposes_regression_and_accepts_repair():
    baseline = evaluate(*inputs())
    assert baseline["gate"]["accepted"] is True
    assert baseline["summary"]["case_count"] == 40
    for scenario, accepted in (("regression", False), ("repaired", True)):
        candidate = evaluate(*inputs(scenario), baseline=baseline)
        assert candidate["gate"]["accepted"] is accepted
        assert candidate["provenance"]["dataset_sha256"] == baseline["provenance"]["dataset_sha256"]
        assert candidate["provenance"]["policy_sha256"] == baseline["provenance"]["policy_sha256"]
        assert compare_reports(baseline, candidate)["gate"]["accepted"] is accepted
        if not accepted:
            assert candidate["summary"]["critical_failure_count"] > 0
            assert any(diff["field"] == "invoice_id" for diff in candidate["diffs"])


def test_repeated_runs_and_shuffled_inputs_have_identical_decisions():
    data, predictions, policy = inputs()
    original = evaluate(data, predictions, policy)
    assert stable(evaluate(data, predictions, policy)) == stable(original)
    data["cases"].reverse()
    predictions["predictions"].reverse()
    shuffled = evaluate(data, predictions, policy)
    assert stable(shuffled) == stable(original)
    assert shuffled["provenance"]["dataset_sha256"] == original["provenance"]["dataset_sha256"]
    assert shuffled["provenance"]["predictions_sha256"] == original["provenance"]["predictions_sha256"]


def test_unrelated_critical_change_rejects_even_with_baseline_scenario_name():
    data, predictions, policy = inputs()
    baseline = evaluate(data, predictions, policy)
    item = next(p for p in predictions["predictions"] if p["record"]["total_amount"] is not None)
    item["record"]["total_amount"] = "99999999999999.99"
    # Scenario remains 'baseline': metadata grants no special behavior.
    report = evaluate(data, predictions, policy, baseline=baseline)
    assert not report["gate"]["accepted"]
    assert any(d["field"] == "total_amount" and d["critical"] for d in report["diffs"])


def test_harmless_formatting_passes_without_improving_existing_errors():
    data, predictions, policy = inputs()
    baseline = evaluate(data, predictions, policy)
    for item in predictions["predictions"]:
        record = item["record"]
        if record["supplier_name"] is not None:
            record["supplier_name"] = "  " + record["supplier_name"].upper().replace(" ", "   ") + " "
        if record["currency"] is not None:
            record["currency"] = record["currency"].lower()
        if record["invoice_id"] is not None:
            record["invoice_id"] = " " + record["invoice_id"] + " "
    report = evaluate(data, predictions, policy, baseline=baseline)
    assert report["gate"]["accepted"]
    assert report["summary"] == baseline["summary"]


def test_report_comparison_does_not_trust_replaced_metrics_or_reference_data():
    original = evaluate(*inputs())
    candidate = evaluate(*inputs("regression"), baseline=original)
    forged = deepcopy(candidate)
    forged["gate"]["accepted"] = True
    with pytest.raises(InputError):
        compare_reports(original, forged)
    altered = deepcopy(original)
    altered["artifacts"]["dataset"]["cases"][0]["document"] += "\nReplaced input"
    with pytest.raises(InputError):
        compare_reports(original, altered)


def test_duplicate_looking_documents_remain_independent_cases():
    data = read_json(resource_path("data/duplicate-looking-development.json"))
    policy = read_json(resource_path("policy.json"))
    predictions = {"dataset_id": data["dataset_id"], "mode": "external_predictions",
                   "scenario": "duplicate-looking-unit-check", "predictions": [
                       {"case_id": case["case_id"], "record": deepcopy(case["expected"]),
                        "evidence": deepcopy(case["evidence"])} for case in data["cases"]]}
    baseline = evaluate(data, predictions, policy)
    assert baseline["gate"]["accepted"]
    assert baseline["summary"]["case_count"] == 2
    predictions["predictions"][1]["record"]["invoice_id"] = (
        predictions["predictions"][0]["record"]["invoice_id"]
    )
    candidate = evaluate(data, predictions, policy, baseline=baseline)
    assert candidate["summary"]["case_count"] == 2
    assert candidate["summary"]["critical_failure_count"] == 1
    assert not candidate["gate"]["accepted"]
