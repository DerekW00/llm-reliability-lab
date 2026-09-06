"""Independent acceptance probes written after a code/data-only first pass.

Expected counts and the date mutation were selected independently of the fixture
regression. No production artifact is modified by these tests.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from reliability_lab import evaluation
from reliability_lab.contracts import FIELDS, InputError, read_json
from reliability_lab.evaluation import evaluate
from reliability_lab.gate import compare_reports
from reliability_lab.reporting import render_report

ROOT = Path(__file__).resolve().parents[1]


def inputs(scenario="baseline"):
    return (
        read_json(ROOT / "data/evaluation.json"),
        read_json(ROOT / f"data/predictions/{scenario}.json"),
        read_json(ROOT / "policy.json"),
    )


def stable(report):
    return {k: report[k] for k in ("summary", "fields", "diffs", "gate")}


def record(values):
    return dict(zip(FIELDS, values, strict=True))


def small_artifacts(pairs):
    cases, predictions = [], []
    for index, (expected, actual) in enumerate(pairs):
        case_id = f"REVIEW-{index}"
        expected_evidence = {f: [] if expected[f] is None else [1] for f in FIELDS}
        actual_evidence = {f: [] if actual[f] is None else [1] for f in FIELDS}
        cases.append({
            "case_id": case_id, "document": f"Fictional fields: {expected}",
            "tags": ["review-hand-counted"], "expected": expected,
            "evidence": expected_evidence, "rationale": "Fields not given are unknown.",
        })
        predictions.append({"case_id": case_id, "record": actual, "evidence": actual_evidence})
    dataset = {"dataset_id": "review-small", "version": 1, "split": "development", "cases": cases}
    supplied = {"dataset_id": "review-small", "mode": "external_predictions",
                "scenario": "hand-counted", "predictions": predictions}
    return dataset, supplied, read_json(ROOT / "policy.json")


def test_review_hand_counted_asymmetric_values_and_nulls():
    null = record([None] * 5)
    dataset, supplied, policy = small_artifacts([
        (record(["A", "Oak", "USD", "0.00", "2028-02-29"]),
         record(["A", "Oak", "GBP", None, None])),
        (record([None, "B", None, "5.00", None]),
         record(["X", "B", "CAD", None, None])),
        (null.copy(), null.copy()),
    ])
    report = evaluate(dataset, supplied, policy)
    assert report["summary"]["micro"] == {
        "tp": 3, "fp": 3, "fn": 4, "tn": 6,
        "precision": 1 / 2, "recall": 3 / 7, "f1": 6 / 13,
    }
    expected_counts = {
        "invoice_id": (1, 1, 0, 1), "supplier_name": (2, 0, 0, 1),
        "currency": (0, 2, 1, 1), "total_amount": (0, 0, 2, 1),
        "due_date": (0, 0, 1, 2),
    }
    for field, expected in expected_counts.items():
        assert tuple(report["fields"][field][k] for k in ("tp", "fp", "fn", "tn")) == expected
    assert report["summary"]["exact_record_count"] == 1
    assert report["summary"]["exact_record_accuracy"] == 1 / 3
    assert report["summary"]["critical_failure_count"] == 6
    assert report["summary"]["abstentions"] == {
        "expected_null": 8, "predicted_null": 9, "correct_abstention": 6,
        "missed_value": 3, "unsupported_value": 2,
    }
    assert len(report["diffs"]) == 6
    assert not report["gate"]["accepted"]


def test_review_all_null_is_undefined_even_with_zero_minima():
    null = record([None] * 5)
    data, supplied, policy = small_artifacts([(null.copy(), null.copy())])
    policy.update(min_micro_f1=0, min_exact_record_accuracy=0)
    policy["min_field_f1"] = dict.fromkeys(FIELDS, 0)
    result = evaluate(data, supplied, policy)
    assert result["summary"]["exact_record_accuracy"] == 1
    assert result["summary"]["micro"] == {
        "tp": 0, "fp": 0, "fn": 0, "tn": 5, "precision": None, "recall": None, "f1": None,
    }
    assert not result["gate"]["accepted"]
    assert len(result["gate"]["reasons"]) == 6


def test_review_new_date_convention_mutation_fails_ordinary_evaluator():
    data, supplied, policy = inputs()
    baseline = evaluate(data, supplied, policy)
    item = next(p for p in supplied["predictions"] if p["case_id"] == "EVAL-15")
    # Source explicitly says MM/DD/YYYY; interpreting 08/12/2026 as DD/MM/YYYY
    # is a new schema-valid critical mutation, unrelated to numeric invoice IDs.
    item["record"]["due_date"] = "2026-12-08"
    result = evaluate(data, supplied, policy, baseline=baseline)
    assert not result["gate"]["accepted"]
    assert result["summary"]["critical_failure_count"] == 1
    assert result["summary"]["exact_record_accuracy"] == 0.95
    assert result["summary"]["micro"]["f1"] == 181 / 183
    assert any(d["case_id"] == "EVAL-15" and d["field"] == "due_date"
               and d["category"] == "wrong_value" and d["critical"] for d in result["diffs"])
    assert result["scenario"] == "baseline"


def test_review_harmless_formatting_keeps_metrics_and_gate():
    data, supplied, policy = inputs()
    original = evaluate(data, supplied, policy)
    for item in supplied["predictions"]:
        for field, value in item["record"].items():
            if value is None:
                continue
            if field == "supplier_name":
                value = value.upper().replace(" ", " \t ")
            if field == "currency":
                value = value.lower()
            item["record"][field] = f"  {value}\t"
    formatted = evaluate(data, supplied, policy)
    assert formatted["summary"] == original["summary"]
    assert formatted["fields"] == original["fields"]
    assert formatted["gate"] == original["gate"]


@pytest.mark.parametrize("fault", [
    "omitted_prediction", "duplicated_prediction", "unexpected_id", "replaced_id",
    "wrong_dataset", "missing_field", "empty_value", "wrong_type", "invalid_date",
    "invalid_money", "null_evidence", "missing_evidence", "out_of_range_evidence",
    "duplicate_dataset", "empty_dataset", "unknown_policy_key", "nan_policy",
    "bool_policy", "missing_policy_field", "empty_critical_fields",
])
def test_review_invalid_artifacts_fail_closed(fault):
    data, supplied, policy = inputs()
    first = supplied["predictions"][0]
    if fault == "omitted_prediction":
        supplied["predictions"].pop()
    elif fault == "duplicated_prediction":
        supplied["predictions"].append(copy.deepcopy(first))
    elif fault == "unexpected_id":
        extra = copy.deepcopy(first)
        extra["case_id"] = "UNKNOWN"
        supplied["predictions"].append(extra)
    elif fault == "replaced_id":
        first["case_id"] = "NOT-A-DATASET-CASE"
    elif fault == "wrong_dataset":
        supplied["dataset_id"] = "other-dataset"
    elif fault == "missing_field":
        del first["record"]["invoice_id"]
    elif fault == "empty_value":
        first["record"]["invoice_id"] = "  "
    elif fault == "wrong_type":
        first["record"]["total_amount"] = 118.45
    elif fault == "invalid_date":
        first["record"]["due_date"] = "2026-02-29"
    elif fault == "invalid_money":
        first["record"]["total_amount"] = "1e3"
    elif fault == "null_evidence":
        first["record"]["invoice_id"] = None
    elif fault == "missing_evidence":
        first["evidence"]["invoice_id"] = []
    elif fault == "out_of_range_evidence":
        first["evidence"]["invoice_id"] = [999]
    elif fault == "duplicate_dataset":
        data["cases"].append(copy.deepcopy(data["cases"][0]))
    elif fault == "empty_dataset":
        data["cases"] = []
    elif fault == "unknown_policy_key":
        policy["allow_failures"] = True
    elif fault == "nan_policy":
        policy["min_micro_f1"] = float("nan")
    elif fault == "bool_policy":
        policy["max_critical_failures"] = False
    elif fault == "missing_policy_field":
        del policy["min_field_f1"]["due_date"]
    elif fault == "empty_critical_fields":
        policy["critical_fields"] = []
    with pytest.raises(InputError):
        evaluate(data, supplied, policy)


@pytest.mark.parametrize("text", [
    '{"a": 1, "a": 2}', '{"a": NaN}', '{"a": Infinity}', '{"a": 1e999}',
    '{"a":', '[]', '\xff',
])
def test_review_corrupt_json_is_input_error(tmp_path, text):
    path = tmp_path / "bad.json"
    path.write_bytes(text.encode("latin1"))
    with pytest.raises(InputError):
        read_json(path)


@pytest.mark.parametrize("dimension", ["document", "label", "policy", "mode"])
def test_review_self_consistent_replaced_artifacts_cannot_compare(dimension):
    data, supplied, policy = inputs()
    baseline = evaluate(data, supplied, policy)
    if dimension == "document":
        data["cases"][0]["document"] += "\nAn added statement changes input identity."
    elif dimension == "label":
        data["cases"][0]["expected"]["invoice_id"] = "replacement"
        supplied["predictions"][0]["record"]["invoice_id"] = "replacement"
    elif dimension == "policy":
        policy["min_micro_f1"] = 0.97
    else:
        supplied["mode"] = "external_predictions"
    replacement = evaluate(data, supplied, policy)
    with pytest.raises(InputError, match="incompatible"):
        compare_reports(baseline, replacement)


@pytest.mark.parametrize("dimension", [
    "accepted", "count", "bool_count", "score", "checks", "diff", "evidence",
    "artifact", "hash", "schema", "provider", "unknown_key",
])
def test_review_tampered_reports_cannot_claim_acceptance(dimension):
    baseline = evaluate(*inputs())
    candidate = evaluate(*inputs("regression"), baseline=baseline)
    if dimension == "accepted":
        candidate["gate"].update(accepted=True, reasons=[])
    elif dimension == "count":
        candidate["summary"]["critical_failure_count"] = 0
    elif dimension == "bool_count":
        candidate["summary"]["schema_valid"] = 1
    elif dimension == "score":
        candidate["summary"]["micro"]["f1"] = 1.0
    elif dimension == "checks":
        candidate["gate"]["checks"] = []
    elif dimension == "diff":
        candidate["diffs"] = []
    elif dimension == "evidence":
        candidate["diffs"][0]["document_excerpts"]["actual"][0]["text"] = "safe"
    elif dimension == "artifact":
        candidate["artifacts"]["predictions"]["predictions"][0]["record"]["invoice_id"] = "safe"
    elif dimension == "hash":
        candidate["provenance"]["dataset_sha256"] = "0" * 64
    elif dimension == "schema":
        del candidate["artifacts"]["dataset"]
    elif dimension == "provider":
        candidate["provenance"]["live_calls"] = True
    else:
        candidate["summary"]["override"] = "accepted"
    with pytest.raises(InputError):
        compare_reports(baseline, candidate)


def test_review_relative_only_rejection_preserved_with_frozen_policy():
    data, supplied, policy = inputs()
    ordinary = evaluate(data, supplied, policy)
    supplied["predictions"][1]["record"]["supplier_name"] = "Copper Vale Binding"
    perfect = evaluate(data, supplied, policy)
    assert ordinary["gate"]["accepted"] and perfect["gate"]["accepted"]
    rejected = compare_reports(perfect, ordinary)
    assert not rejected["gate"]["accepted"]
    assert [c["name"] for c in rejected["gate"]["checks"] if not c["passed"]] == ["micro_f1_drop"]
    assert rejected["gate"] == compare_reports(perfect, rejected)["gate"]
    with pytest.raises(InputError, match="different baseline"):
        compare_reports(ordinary, rejected)


def test_review_frozen_bytes_and_scenario_independence():
    expected = {
        "data/development.json": "6ea77e04ff6ced3af2cebbc9ef25856acd247231048cdc94e6aa8819edbfa24a",
        "data/evaluation.json": "27b447e9318d25a4af94e2801ce35199e34771f0837603306172cbd8b89117e0",
        "policy.json": "b81326e57c06b797858a346824596d2e84d6e64c4ad7b56c90a6027652b43ff2",
        "data/duplicate-looking-development.json":
            "b4ef2f5874b902fe530f2538d27ff5a657521aafb495507238b54ec1f04352f0",
        "data/predictions/baseline.json":
            "f39542c5f9c7ed633f96629fe2a7ba29913610fb77c56ebe15a5e7a4389a18ca",
        "data/predictions/regression.json":
            "26ce19c971de3e4d1f07bfc1be320d07b7687db3a07d65e457ce0a7aa64629c4",
        "data/predictions/repaired.json":
            "0977102b09d3ee9f9699b630c5f43036f38fbc0afc4f367405ed6b59a4bcd7f7",
    }
    for path, digest in expected.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    source_files = sorted((ROOT / "src/reliability_lab").glob("*.py"))
    before = {p: p.read_bytes() for p in source_files}
    baseline = evaluate(*inputs())
    for scenario, accepted in [("baseline", True), ("regression", False), ("repaired", True)]:
        data, supplied, policy = inputs(scenario)
        result = evaluate(data, supplied, policy, baseline=baseline)
        assert result["gate"]["accepted"] is accepted
        assert stable(evaluate(data, supplied, policy, baseline=baseline)) == stable(result)
        supplied["scenario"] = "reviewer-arbitrary-scenario-label"
        assert stable(evaluate(data, supplied, policy, baseline=baseline)) == stable(result)
        data["cases"].reverse()
        supplied["predictions"] = supplied["predictions"][7:] + supplied["predictions"][:7]
        shuffled = evaluate(data, supplied, policy, baseline=baseline)
        assert stable(shuffled) == stable(result)
        assert shuffled["provenance"]["dataset_sha256"] == baseline["provenance"]["dataset_sha256"]
        assert shuffled["provenance"]["policy_sha256"] == baseline["provenance"]["policy_sha256"]
    assert before == {p: p.read_bytes() for p in source_files}


def test_review_checkout_provenance_is_actual_tracked_revision():
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], env=environment, text=True,
    ).strip()
    dirty = bool(subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=normal"],
        env=environment, text=True,
    ).strip())
    actual_revision, actual_dirty = evaluation._code_provenance()
    assert actual_revision == revision
    assert actual_dirty is dirty


def invoke(args, cwd):
    environment = {"PATH": os.environ["PATH"], "LANG": "en_US.UTF-8"}
    return subprocess.run([sys.executable, "-m", "reliability_lab.cli", *args],
                          cwd=cwd, env=environment, capture_output=True, text=True, timeout=30)


def test_review_cli_offline_guard_and_no_credentials_in_fresh_subprocesses(tmp_path):
    guard = '''
import socket
calls = []
def blocked(*args, **kwargs):
    calls.append(True)
    raise OSError("REVIEW_NETWORK_FORBIDDEN")
for name in ("connect", "connect_ex", "sendto", "sendall", "send"):
    setattr(socket.socket, name, blocked)
for name in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex",
             "gethostbyaddr", "getfqdn"):
    setattr(socket, name, blocked)
try:
    socket.getaddrinfo("review.invalid", 443)
except OSError:
    pass
else:
    raise AssertionError("DNS guard did not intercept")
with socket.socket() as connection:
    try:
        connection.connect(("127.0.0.1", 9))
    except OSError:
        pass
    else:
        raise AssertionError("Socket guard did not intercept")
assert len(calls) == 2
calls.clear()
from reliability_lab.cli import main
code = main()
assert calls == [], "CLI attempted networking, even if an exception was swallowed"
raise SystemExit(code)
'''
    environment = {"PATH": os.environ["PATH"], "LANG": "en_US.UTF-8"}
    out = tmp_path / "offline"
    commands = [
        (["demo", "--scenario", scenario, "--output-dir", str(out)], code)
        for scenario, code in [("baseline", 0), ("regression", 1), ("repaired", 0)]
    ]
    commands += [
        (["compare", str(out / "baseline.json"), str(out / "regression.json"),
          "--output-dir", str(out)], 1),
        (["evaluate", "--dataset", str(ROOT / "data/evaluation.json"),
          "--predictions", str(ROOT / "data/predictions/repaired.json"),
          "--policy", str(ROOT / "policy.json"), "--output-dir", str(out)], 0),
    ]
    for args, expected in commands:
        result = subprocess.run([sys.executable, "-c", guard, *args], cwd=tmp_path,
                                env=environment, capture_output=True, text=True, timeout=30)
        assert result.returncode == expected, (result.stdout, result.stderr)
        assert "REVIEW_NETWORK_FORBIDDEN" not in result.stdout + result.stderr
    baseline = json.loads((out / "baseline.json").read_text())
    assert baseline["provenance"]["live_calls"] is False
    assert baseline["provenance"]["provider"] is None
    assert baseline["provenance"]["model"] is None


@pytest.mark.parametrize("missing", ["dataset", "predictions", "policy", "baseline"])
def test_review_cli_missing_files_remove_stale_pass(tmp_path, missing):
    args = ["evaluate", "--output-dir", str(tmp_path), "--name", "stale"]
    paths = {"dataset": ROOT / "data/evaluation.json",
             "predictions": ROOT / "data/predictions/baseline.json",
             "policy": ROOT / "policy.json"}
    if missing == "baseline":
        paths["baseline"] = tmp_path / "missing-baseline.json"
    else:
        paths[missing] = tmp_path / f"missing-{missing}.json"
    for key, path in paths.items():
        args += [f"--{key}", str(path)]
    (tmp_path / "stale.json").write_text('{"gate":{"accepted":true}}')
    (tmp_path / "stale.md").write_text("ACCEPTED")
    result = invoke(args, tmp_path)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "stale.json").exists()
    assert not (tmp_path / "stale.md").exists()


@pytest.mark.parametrize("kind", ["same_path", "hardlink", "symlink"])
def test_review_output_collision_preserves_input(tmp_path, kind):
    supplied = tmp_path / "source.json"
    supplied.write_bytes((ROOT / "data/predictions/baseline.json").read_bytes())
    destination = tmp_path / "evaluation.json"
    if kind == "same_path":
        destination = supplied
    elif kind == "hardlink":
        os.link(supplied, destination)
    else:
        destination.symlink_to(supplied)
    before = supplied.read_bytes()
    args = ["evaluate", "--dataset", str(ROOT / "data/evaluation.json"),
            "--predictions", str(supplied), "--policy", str(ROOT / "policy.json"),
            "--output-dir", str(tmp_path), "--name", destination.stem]
    result = invoke(args, tmp_path)
    assert result.returncode == 2
    assert supplied.read_bytes() == before
    assert destination.read_bytes() == before


def test_review_untrusted_text_is_inert_in_human_report():
    data, supplied, policy = inputs()
    payload = "\x1b[2J\u202e<script>alert(1)</script>[click](https://example.invalid)"
    supplied["scenario"] = payload
    supplied["predictions"][0]["record"]["invoice_id"] = payload
    data["cases"][0]["document"] += "\n" + payload
    supplied["predictions"][0]["evidence"]["invoice_id"] = [5]
    output = render_report(evaluate(data, supplied, policy))
    assert "\x1b" not in output and "\u202e" not in output
    assert "<script>" not in output and "[click](" not in output
    assert "\\x1b" in output and "\\u202e" in output
    assert "SYNTHETIC FIXTURE EVALUATION" in output
    assert "Decision: REJECTED" in output


def test_review_duplicate_looking_cases_are_two_independent_obligations():
    data = read_json(ROOT / "data/duplicate-looking-development.json")
    policy = read_json(ROOT / "policy.json")
    # Independently transcribed from the two raw slips, not generated from labels.
    supplied = {"dataset_id": data["dataset_id"], "mode": "external_predictions",
                "scenario": "reviewer-slip-check", "predictions": []}
    for index, invoice in enumerate(("011842", "011843"), start=1):
        supplied["predictions"].append({
            "case_id": f"DUPDEV-0{index}",
            "record": record([invoice, "Brass Petal Screenworks", "USD", "64.64", "2027-01-15"]),
            "evidence": dict(zip(FIELDS, ([2], [1], [3], [3], [4]), strict=True)),
        })
    correct = evaluate(data, supplied, policy)
    assert correct["gate"]["accepted"]
    assert correct["summary"]["exact_record_count"] == 2
    supplied["predictions"][1]["record"]["invoice_id"] = "011842"
    confused = evaluate(data, supplied, policy)
    assert not confused["gate"]["accepted"]
    assert confused["summary"]["critical_failure_count"] == 1
    supplied["predictions"].pop()
    with pytest.raises(InputError, match="missing case"):
        evaluate(data, supplied, policy)
