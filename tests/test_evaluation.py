"""Independent, authored arithmetic examples; no bundled fixture dependencies."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from reliability_lab import evaluation
from reliability_lab.contracts import FIELDS, InputError
from reliability_lab.evaluation import evaluate

RECORD = {
    "invoice_id": "00127",
    "supplier_name": "Copper Finch Studio",
    "currency": "USD",
    "total_amount": "17.25",
    "due_date": "2026-12-01",
}
OTHER = {
    "invoice_id": "00128",
    "supplier_name": "Juniper Lantern Workshop",
    "currency": "EUR",
    "total_amount": "18.25",
    "due_date": "2026-12-02",
}
NULL_RECORD = dict.fromkeys(FIELDS)


def artifacts(pairs=None, *, mode="external_predictions", scenario="authored test"):
    pairs = [(RECORD, RECORD)] if pairs is None else pairs
    cases, predictions = [], []
    for index, (expected, actual) in enumerate(pairs):
        case_id = f"authored-{index:03}"
        document = "\n".join(f"{field}: {value or 'Not established'}" for field, value in expected.items())

        def evidence(record):
            return {field: [line] if record[field] is not None else []
                    for line, field in enumerate(FIELDS, start=1)}

        cases.append({"case_id": case_id, "document": document, "tags": ["authored-unit-case"],
                      "expected": copy.deepcopy(expected), "evidence": evidence(expected),
                      "rationale": "This test explicitly labels missing values as undetermined."})
        predictions.append({"case_id": case_id, "record": copy.deepcopy(actual),
                            "evidence": evidence(actual)})
    dataset = {"dataset_id": "independent-unit-examples", "version": 1, "split": "evaluation",
               "cases": cases}
    supplied = {"dataset_id": dataset["dataset_id"], "mode": mode, "scenario": scenario,
                "predictions": predictions}
    policy = {
        "version": 1,
        "critical_fields": ["invoice_id", "currency", "total_amount", "due_date"],
        "max_critical_failures": 0,
        "min_micro_f1": 0.98,
        "min_exact_record_accuracy": 0.95,
        "min_field_f1": dict.fromkeys(FIELDS, 0.9),
        "max_micro_f1_drop": 0.005,
        "max_exact_record_accuracy_drop": 0.025,
    }
    return dataset, supplied, policy


def permissive(policy):
    policy["max_critical_failures"] = 1_000_000
    policy["min_micro_f1"] = 0
    policy["min_exact_record_accuracy"] = 0
    policy["min_field_f1"] = dict.fromkeys(FIELDS, 0)
    return policy


def test_hand_calculated_confusion_counts_and_abstentions():
    report = evaluate(*artifacts([
        (RECORD, RECORD), (NULL_RECORD, NULL_RECORD), (RECORD, NULL_RECORD),
        (NULL_RECORD, RECORD), (RECORD, OTHER),
    ]))
    assert report["summary"]["micro"] == {
        "tp": 5, "fp": 10, "fn": 10, "tn": 5,
        "precision": 1 / 3, "recall": 1 / 3, "f1": 1 / 3,
    }
    for metrics in report["fields"].values():
        assert metrics == {"tp": 1, "fp": 2, "fn": 2, "tn": 1,
                           "precision": 1 / 3, "recall": 1 / 3, "f1": 1 / 3}
    assert report["summary"]["exact_record_accuracy"] == 0.4
    assert report["summary"]["exact_record_count"] == 2
    assert report["summary"]["critical_failure_count"] == 12
    assert report["summary"]["abstentions"] == {
        "expected_null": 10, "predicted_null": 10, "correct_abstention": 5,
        "missed_value": 5, "unsupported_value": 5,
    }
    assert len(report["diffs"]) == 15
    assert {diff["category"] for diff in report["diffs"]} == {
        "missed_value", "unsupported_value", "wrong_value",
    }
    assert report["summary"]["schema_valid"] is True
    assert report["summary"]["coverage_complete"] is True
    assert report["summary"]["case_count"] == report["summary"]["prediction_count"] == 5


def test_asymmetric_precision_recall_and_micro_are_not_macro_averages():
    partial = {**RECORD, "invoice_id": None, "supplier_name": "Other Studio", "due_date": None}
    invented = {**NULL_RECORD, "invoice_id": "00127"}
    report = evaluate(*artifacts([(RECORD, RECORD), (RECORD, partial), (NULL_RECORD, invented)]))
    assert report["summary"]["micro"] == {
        "tp": 7, "fp": 2, "fn": 3, "tn": 4,
        "precision": 7 / 9, "recall": 7 / 10, "f1": 14 / 19,
    }
    assert report["fields"]["due_date"] == {
        "tp": 1, "fp": 0, "fn": 1, "tn": 1,
        "precision": 1.0, "recall": 0.5, "f1": 2 / 3,
    }
    macro_f1 = sum(metrics["f1"] for metrics in report["fields"].values()) / 5
    assert report["summary"]["micro"]["f1"] != macro_f1
    assert report["summary"]["exact_record_accuracy"] == 1 / 3


@pytest.mark.parametrize(("expected", "actual", "precision", "recall", "f1"), [
    (NULL_RECORD, NULL_RECORD, None, None, None),
    (RECORD, NULL_RECORD, None, 0.0, 0.0),
    (NULL_RECORD, RECORD, 0.0, None, 0.0),
])
def test_zero_denominators_are_undefined(expected, actual, precision, recall, f1):
    report = evaluate(*artifacts([(expected, actual)]))
    assert report["summary"]["micro"]["precision"] == precision
    assert report["summary"]["micro"]["recall"] == recall
    assert report["summary"]["micro"]["f1"] == f1


def test_normalization_is_field_specific_and_zero_is_a_value():
    expected = {**RECORD, "supplier_name": "Straße  Studio", "total_amount": "0.00"}
    actual = {"invoice_id": " 00127 ", "supplier_name": " STRASSE \t studio ",
              "currency": " usd ", "total_amount": " 0.00 ", "due_date": " 2026-12-01 "}
    report = evaluate(*artifacts([(expected, actual)]))
    assert report["gate"]["accepted"] is True
    assert report["diffs"] == []
    assert report["summary"]["micro"]["tp"] == 5
    assert report["summary"]["abstentions"]["correct_abstention"] == 0


def test_identifier_format_diff_preserves_values_and_document_evidence():
    report = evaluate(*artifacts([(RECORD, {**RECORD, "invoice_id": "127"})]))
    assert report["diffs"] == [{
        "case_id": "authored-000", "field": "invoice_id", "expected": "00127", "actual": "127",
        "category": "identifier_format", "critical": True,
        "evidence": {"expected": [1], "actual": [1]},
        "document_excerpts": {
            "expected": [{"line": 1, "text": "invoice_id: 00127"}],
            "actual": [{"line": 1, "text": "invoice_id: 00127"}],
        },
    }]


def test_identifier_classification_never_coerces_huge_ids_to_integers():
    identifier = "7" * 5_000
    expected = {**RECORD, "invoice_id": "000" + identifier}
    actual = {**RECORD, "invoice_id": identifier}
    report = evaluate(*artifacts([(expected, actual)]))
    assert report["diffs"][0]["category"] == "identifier_format"
    assert report["summary"]["critical_failure_count"] == 1


@pytest.mark.parametrize("field,value", [("invoice_id", "00127-A"),
                                          ("supplier_name", "Copper-Finch Studio")])
def test_meaningful_punctuation_is_not_normalized_away(field, value):
    report = evaluate(*artifacts([(RECORD, {**RECORD, field: value})]))
    assert report["diffs"][0]["category"] == "wrong_value"


def test_scenario_is_metadata_and_order_does_not_change_metrics():
    dataset, predictions, policy = artifacts([(RECORD, OTHER), (RECORD, RECORD)])
    first = evaluate(dataset, predictions, policy)
    dataset["cases"].reverse()
    predictions["predictions"].reverse()
    predictions["scenario"] = "baseline repaired regression any arbitrary words"
    second = evaluate(dataset, predictions, policy)
    for key in ("summary", "fields", "diffs", "gate"):
        assert first[key] == second[key]
    assert first["provenance"]["dataset_sha256"] == second["provenance"]["dataset_sha256"]


def test_report_embeds_independent_complete_artifacts():
    dataset, predictions, policy = artifacts()
    original = copy.deepcopy((dataset, predictions, policy))
    report = evaluate(dataset, predictions, policy)
    assert (dataset, predictions, policy) == original
    assert report["artifacts"] == dict(zip(("dataset", "predictions", "policy"), original, strict=True))
    predictions["predictions"][0]["record"]["invoice_id"] = "999"
    assert report["artifacts"]["predictions"]["predictions"][0]["record"]["invoice_id"] == "00127"


@pytest.mark.parametrize("mutation", [
    lambda d, p: p["predictions"].clear(),
    lambda d, p: p["predictions"].append(copy.deepcopy(p["predictions"][0])),
    lambda d, p: p["predictions"][0].update(case_id="unknown"),
    lambda d, p: p.update(dataset_id="wrong-dataset"),
    lambda d, p: p["predictions"][0]["record"].pop("invoice_id"),
    lambda d, p: p["predictions"][0]["record"].update(total_amount=17.25),
    lambda d, p: p["predictions"][0]["evidence"].update(invoice_id=[99]),
    lambda d, p: d["cases"].clear(),
])
def test_invalid_inputs_never_become_partial_scores(mutation):
    dataset, predictions, policy = artifacts()
    mutation(dataset, predictions)
    with pytest.raises(InputError):
        evaluate(dataset, predictions, policy)


def test_all_fields_and_all_rules_use_configured_policy():
    dataset, predictions, policy = artifacts([(RECORD, OTHER)])
    policy["critical_fields"] = ["supplier_name"]
    report = evaluate(dataset, predictions, policy)
    assert report["summary"]["critical_failure_count"] == 1
    assert [diff["field"] for diff in report["diffs"] if diff["critical"]] == ["supplier_name"]
    assert len(report["gate"]["checks"]) == len(report["gate"]["reasons"]) == 8


def test_provenance_timing_is_evaluation_only_and_never_model_latency():
    for mode, timing in (("synthetic_fixture", "fixture_evaluation"),
                         ("external_predictions", "evaluation_only")):
        provenance = evaluate(*artifacts(mode=mode))["provenance"]
        assert provenance["timing_kind"] == timing
        assert provenance["evaluation_seconds"] >= 0
        assert provenance["live_calls"] is False
        assert provenance["provider"] is provenance["model"] is None


def test_source_provenance_ignores_cwd_and_git_environment(monkeypatch, tmp_path):
    calls = []

    def git_run(args, **kwargs):
        calls.append((args, kwargs))
        source = Path(evaluation.__file__).resolve()
        answers = [str(source.parents[2]), "src/reliability_lab/evaluation.py", "a" * 40, ""]
        return type("Result", (), {"stdout": answers[len(calls) - 1]})()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_DIR", "/unrelated/repository/.git")
    monkeypatch.setenv("GIT_WORK_TREE", "/unrelated/repository")
    monkeypatch.setattr(evaluation.subprocess, "run", git_run)
    assert evaluation._code_provenance() == ("a" * 40, False)
    assert all(call[0][2] == str(Path(evaluation.__file__).resolve().parent) for call in calls)
    assert all(not any(key.startswith("GIT_") for key in call[1]["env"]) for call in calls)


def test_installed_untracked_module_has_unknown_git_provenance(monkeypatch):
    def git_run(args, **kwargs):
        if "ls-files" in args:
            raise evaluation.subprocess.CalledProcessError(1, args)
        return type("Result", (), {"stdout": str(Path(evaluation.__file__).resolve().parents[3])})()

    monkeypatch.setattr(evaluation.subprocess, "run", git_run)
    assert evaluation._code_provenance() == (None, None)
