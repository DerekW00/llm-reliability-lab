"""CLI boundary tests; integrated scenario behavior is exercised after assembly."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from reliability_lab import cli, reporting
from reliability_lab.contracts import FIELDS, InputError


@pytest.fixture
def report() -> dict:
    counts = {"tp": 1, "fp": 0, "fn": 0, "tn": 0, "precision": 1.0, "recall": 1.0, "f1": 1.0}
    return {
        "report_version": 1,
        "mode": "synthetic_fixture",
        "scenario": "baseline",
        "dataset_id": "test-only",
        "split": "evaluation",
        "summary": {
            "case_count": 1, "prediction_count": 1, "schema_valid": True,
            "coverage_complete": True, "micro": {**counts, "tp": 5},
            "exact_record_accuracy": 1.0, "exact_record_count": 1, "critical_failure_count": 0,
            "abstentions": {key: 0 for key in (
                "expected_null", "predicted_null", "correct_abstention", "missed_value",
                "unsupported_value",
            )},
        },
        "fields": {field: dict(counts) for field in FIELDS},
        "diffs": [],
        "gate": {
            "accepted": True, "reasons": [],
            "checks": [{"name": "critical_failures", "passed": True, "actual": 0, "required": 0}],
        },
        "provenance": {
            "dataset_sha256": "a" * 64, "predictions_sha256": "b" * 64,
            "policy_sha256": "c" * 64, "timestamp_utc": "2026-09-11T00:00:00+00:00",
            "code_revision": None, "working_tree_dirty": None, "python_version": "3.12.14",
            "evaluation_seconds": 0.001, "timing_kind": "fixture_evaluation", "provider": None,
            "model": None, "live_calls": False,
        },
        "artifacts": {"dataset": {}, "predictions": {}, "policy": {}},
    }


@pytest.fixture
def inputs(tmp_path: Path) -> dict[str, Path]:
    result = {}
    for name in ("dataset", "predictions", "policy", "baseline"):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps({"fixture": name}), encoding="utf-8")
        result[name] = path
    return result


def evaluate_args(inputs: dict[str, Path], output_dir: Path) -> list[str]:
    args = ["evaluate", "--output-dir", str(output_dir)]
    for name in ("dataset", "predictions", "policy"):
        args += [f"--{name}", str(inputs[name])]
    return args


def test_evaluate_writes_actual_result_and_prints_paths(monkeypatch, capsys, tmp_path, inputs, report):
    seen = []
    monkeypatch.setattr(cli, "_evaluate", lambda *args, **kwargs: seen.append((args, kwargs)) or report)
    output_dir = tmp_path / "out"
    assert cli.main(evaluate_args(inputs, output_dir)) == 0
    assert seen == [(({"fixture": "dataset"}, {"fixture": "predictions"}, {"fixture": "policy"}), {})]
    assert json.loads((output_dir / "evaluation.json").read_text()) == report
    terminal = capsys.readouterr()
    assert "SYNTHETIC FIXTURE EVALUATION" in terminal.out
    assert str((output_dir / "evaluation.json").resolve()) in terminal.out
    assert "100.0000% (10/10)" in terminal.out
    assert not terminal.err


def test_quality_rejection_is_written_and_returns_one(monkeypatch, capsys, tmp_path, inputs, report):
    report["gate"] = {"accepted": False, "reasons": ["Critical failure budget exceeded"],
                      "checks": [{"name": "critical", "passed": False, "actual": 1, "required": 0}]}
    monkeypatch.setattr(cli, "_evaluate", lambda *args, **kwargs: report)
    output_dir = tmp_path / "out"
    assert cli.main(evaluate_args(inputs, output_dir)) == 1
    assert json.loads((output_dir / "evaluation.json").read_text())["gate"]["accepted"] is False
    assert "Critical failure budget exceeded" in capsys.readouterr().out


def test_explicit_baseline_is_passed_to_evaluator(monkeypatch, tmp_path, inputs, report):
    seen = []
    monkeypatch.setattr(cli, "_evaluate", lambda *args, **kwargs: seen.append(kwargs) or report)
    args = evaluate_args(inputs, tmp_path / "out") + ["--baseline", str(inputs["baseline"])]
    assert cli.main(args) == 0
    assert seen == [{"baseline": {"fixture": "baseline"}}]


@pytest.mark.parametrize("scenario,call_count", [("baseline", 1), ("regression", 2), ("repaired", 2)])
def test_demo_uses_bundled_paths_and_fresh_baseline(
    monkeypatch, tmp_path, report, scenario, call_count,
):
    bundle = tmp_path / "bundle"
    for relative in ("data/evaluation.json", "policy.json", "data/predictions/baseline.json",
                     f"data/predictions/{scenario}.json"):
        path = bundle / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"resource": relative}))
    monkeypatch.setattr(cli, "resource_path", lambda relative: bundle / relative)
    seen = []
    monkeypatch.setattr(cli, "_evaluate", lambda *args, **kwargs: seen.append((args, kwargs)) or report)
    assert cli.main(["demo", "--scenario", scenario, "--output-dir", str(tmp_path / "out")]) == 0
    assert len(seen) == call_count
    assert seen[0][0][1] == {"resource": "data/predictions/baseline.json"}
    assert seen[0][1] == {}
    if call_count == 2:
        assert seen[1][0][1] == {"resource": f"data/predictions/{scenario}.json"}
        assert seen[1][1] == {"baseline": report}


def test_compare_preserves_returned_rejection(monkeypatch, tmp_path, inputs, report):
    report["gate"]["accepted"] = False
    report["gate"]["reasons"] = ["Micro F1 drop exceeds policy"]
    seen = []
    monkeypatch.setattr(cli, "_compare", lambda *args: seen.append(args) or report)
    output_dir = tmp_path / "out"
    assert cli.main(["compare", str(inputs["baseline"]), str(inputs["predictions"]),
                     "--output-dir", str(output_dir)]) == 1
    assert seen == [({"fixture": "baseline"}, {"fixture": "predictions"})]
    assert json.loads((output_dir / "comparison.json").read_text()) == report


@pytest.mark.parametrize("content", [None, "{", '{"a":1,"a":2}', '{"a":NaN}', "[]"])
def test_bad_input_returns_two_without_stale_pass(capsys, tmp_path, inputs, content):
    if content is None:
        inputs["dataset"].unlink()
    else:
        inputs["dataset"].write_text(content)
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    for suffix in ("json", "md"):
        (output_dir / f"evaluation.{suffix}").write_text("old accepted report")
    assert cli.main(evaluate_args(inputs, output_dir)) == 2
    assert list(output_dir.iterdir()) == []
    result = capsys.readouterr()
    assert "Error:" in result.err and "No fresh report" in result.err
    assert "Traceback" not in result.err
    assert not result.out


@pytest.mark.parametrize("error", [InputError("mismatched IDs"), RuntimeError("execution broke")])
def test_evaluation_error_does_not_write_report(monkeypatch, capsys, tmp_path, inputs, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(cli, "_evaluate", fail)
    output_dir = tmp_path / "out"
    assert cli.main(evaluate_args(inputs, output_dir)) == 2
    assert not (output_dir / "evaluation.json").exists()
    assert "Traceback" not in capsys.readouterr().err


@pytest.mark.parametrize("name", ["../escape", "/absolute", "a/b", "a\\b", ".", "..", "", "a.md",
                                  " a", "a\n", "a" * 101])
def test_unsafe_names_are_rejected(tmp_path, inputs, name):
    assert cli.main(evaluate_args(inputs, tmp_path / "out") + ["--name", name]) == 2
    assert not (tmp_path / "escape.json").exists()


def test_output_cannot_overwrite_input(tmp_path, inputs):
    original = inputs["dataset"].read_bytes()
    assert cli.main(evaluate_args(inputs, tmp_path) + ["--name", "dataset"]) == 2
    assert inputs["dataset"].read_bytes() == original


def test_compare_cannot_overwrite_input(tmp_path, inputs):
    source = tmp_path / "comparison.json"
    source.write_text('{"keep": true}')
    assert cli.main(["compare", str(source), str(inputs["baseline"]),
                     "--output-dir", str(tmp_path)]) == 2
    assert source.read_text() == '{"keep": true}'


@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_linked_input_is_preserved(tmp_path, inputs, kind):
    destination = tmp_path / "evaluation.json"
    if kind == "symlink":
        destination.symlink_to(inputs["dataset"])
    else:
        destination.hardlink_to(inputs["dataset"])
    original = inputs["dataset"].read_bytes()
    assert cli.main(evaluate_args(inputs, tmp_path)) == 2
    assert inputs["dataset"].read_bytes() == original
    assert destination.exists()


def test_output_directory_error_is_concise(monkeypatch, capsys, tmp_path, inputs, report):
    monkeypatch.setattr(cli, "_evaluate", lambda *args, **kwargs: report)
    output_dir = tmp_path / "a-file"
    output_dir.write_text("keep")
    assert cli.main(evaluate_args(inputs, output_dir)) == 2
    assert output_dir.read_text() == "keep"
    assert "Traceback" not in capsys.readouterr().err


def test_strict_json_refuses_nan_and_removes_stale_outputs(tmp_path, report):
    report["summary"]["micro"]["f1"] = float("nan")
    for suffix in ("json", "md"):
        (tmp_path / f"evaluation.{suffix}").write_text("old accepted report")
    with pytest.raises(ValueError):
        reporting.write_reports(report, tmp_path, "evaluation")
    assert list(tmp_path.iterdir()) == []


def test_failed_pair_publication_leaves_no_partial_or_stale_report(monkeypatch, tmp_path, report):
    replace = reporting.os.replace
    calls = 0

    def fail_second(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("disk write failed")
        replace(source, destination)

    monkeypatch.setattr(reporting.os, "replace", fail_second)
    with pytest.raises(OSError, match="disk write failed"):
        reporting.write_reports(report, tmp_path, "evaluation")
    assert list(tmp_path.iterdir()) == []


def make_diff(case_id="critical-case", field="invoice_id", critical=True):
    return {
        "case_id": case_id, "field": field, "expected": "00123", "actual": "123",
        "category": "identifier_format", "critical": critical,
        "evidence": {"expected": [1], "actual": [1]},
        "document_excerpts": {side: [{"line": 1, "text": "Invoice 00123"}]
                              for side in ("expected", "actual")},
    }


def test_report_escapes_untrusted_markdown_and_terminal_controls(report):
    payload = "\x1b[31m[click](https://invalid.example) <script>alert(1)</script> |\n\u202e"
    report["scenario"] = payload
    report["diffs"] = [make_diff()]
    report["diffs"][0]["document_excerpts"]["expected"][0]["text"] = payload
    result = reporting.render_report(report)
    assert "\x1b" not in result and "\u202e" not in result
    assert "<script>" not in result and "[click](" not in result
    assert "&lt;script&gt;" in result
    assert "\\|" in result
    assert "preserve leading zeros" in result
    assert "Line 1:" in result


def test_undefined_metrics_are_explicit(report):
    report["fields"]["invoice_id"] = {
        "tp": 0, "fp": 0, "fn": 0, "tn": 1, "precision": None, "recall": None, "f1": None,
    }
    assert reporting.render_report(report).count("null (undefined; 0/0)") == 3


def test_report_shows_critical_examples_first_and_bounds_excerpts(report):
    report["diffs"] = [make_diff(f"a-{number}", "supplier_name", False) for number in range(12)]
    report["diffs"].append(make_diff("z-critical"))
    result = reporting.render_report(report)
    assert "Showing 10 of 13" in result
    assert result.index("### z") < result.index("### a")
    assert result.count("### ") == 10


def test_external_mode_is_labeled(report):
    report["mode"] = "external_predictions"
    result = reporting.render_report(report)
    assert "EXTERNAL PREDICTION EVALUATION" in result
    assert "SYNTHETIC FIXTURE EVALUATION" not in result


def test_error_messages_are_terminal_safe(monkeypatch, capsys, tmp_path, inputs):
    def fail(*args, **kwargs):
        raise InputError("invalid \x1b[31mvalue\u202e")

    monkeypatch.setattr(cli, "_evaluate", fail)
    assert cli.main(evaluate_args(inputs, tmp_path / "out")) == 2
    error = capsys.readouterr().err
    assert "\x1b" not in error and "\u202e" not in error
    assert "\\x1b" in error and "\\u202e" in error


def test_module_help_works_outside_repository(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "reliability_lab.cli", "--help"], cwd=tmp_path,
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0
    assert "synthetic fixtures" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.skipif(
    importlib.util.find_spec("reliability_lab.evaluation") is None,
    reason="Evaluator and frozen fixtures are supplied by independent integration branches",
)
def test_integrated_demos_and_comparisons_outside_repository(tmp_path):
    output_dir = tmp_path / "reports"
    reports = {}
    for scenario, status in (("baseline", 0), ("regression", 1), ("repaired", 0)):
        result = subprocess.run(
            [sys.executable, "-m", "reliability_lab.cli", "demo", "--scenario", scenario,
             "--output-dir", str(output_dir)], cwd=tmp_path,
            text=True, capture_output=True, check=False,
        )
        assert result.returncode == status, result.stderr + result.stdout
        reports[scenario] = json.loads((output_dir / f"{scenario}.json").read_text())
        assert reports[scenario]["gate"]["accepted"] is (status == 0)
        assert "SYNTHETIC FIXTURE EVALUATION" in result.stdout
    baseline = reports["baseline"]
    assert baseline["summary"]["critical_failure_count"] == 0
    assert reports["regression"]["summary"]["critical_failure_count"] > 0
    assert reports["regression"]["gate"]["reasons"]
    assert reports["repaired"]["summary"] == baseline["summary"]
    for scenario, status in (("regression", 1), ("repaired", 0)):
        result = subprocess.run(
            [sys.executable, "-m", "reliability_lab.cli", "compare",
             str(output_dir / "baseline.json"), str(output_dir / f"{scenario}.json"),
             "--output-dir", str(tmp_path / f"compare-{scenario}")], cwd=tmp_path,
            text=True, capture_output=True, check=False,
        )
        assert result.returncode == status, result.stderr + result.stdout
