"""Evaluate supplied extraction artifacts, without inference or scenario logic."""

from __future__ import annotations

import copy
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from .contracts import (
    FIELDS,
    fingerprint,
    normalize,
    validate_dataset,
    validate_policy,
    validate_predictions,
)


def _rates(counts: dict) -> dict:
    tp, fp, fn = (counts[key] for key in ("tp", "fp", "fn"))
    return {
        **counts,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
    }


def _code_provenance() -> tuple[str | None, bool | None]:
    """Use the tracked module's checkout, never the caller's current directory."""
    source = Path(__file__).resolve()
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}

    def git(*arguments: str) -> str:
        return subprocess.run(
            ["git", "-C", str(source.parent), *arguments],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
            env=environment,
        ).stdout.strip()

    try:
        root = Path(git("rev-parse", "--show-toplevel")).resolve()
        relative = source.relative_to(root)
        # Git runs from the module directory; anchor the literal pathspec at
        # the checkout root instead of interpreting it relative to that directory.
        git("ls-files", "--error-unmatch", "--", f":(top,literal){relative.as_posix()}")
        revision = git("rev-parse", "HEAD")
        dirty = bool(git("status", "--porcelain", "--untracked-files=normal"))
    except (OSError, ValueError, subprocess.SubprocessError):
        # A wheel has no source checkout identity. Installed files inside an
        # unrelated repository must not inherit that repository's revision.
        return None, None
    return revision, dirty


def _derive_report(dataset: dict, predictions: dict, policy: dict) -> dict:
    """Deterministic report components; also used for untrusted-report replay."""
    from .gate import _absolute_gate

    validate_dataset(dataset)
    validate_predictions(predictions, dataset)
    validate_policy(policy)
    by_id = {item["case_id"]: item for item in predictions["predictions"]}
    counts = {field: dict.fromkeys(("tp", "fp", "fn", "tn"), 0) for field in FIELDS}
    abstentions = dict.fromkeys(
        ("expected_null", "predicted_null", "correct_abstention", "missed_value",
         "unsupported_value"), 0
    )
    diffs = []
    exact_records = 0
    critical_failures = 0
    for case in sorted(dataset["cases"], key=lambda item: item["case_id"]):
        prediction = by_id[case["case_id"]]
        exact = True
        document_lines = case["document"].splitlines()
        for field in FIELDS:
            expected = normalize(field, case["expected"][field])
            actual = normalize(field, prediction["record"][field])
            field_counts = counts[field]
            abstentions["expected_null"] += int(expected is None)
            abstentions["predicted_null"] += int(actual is None)
            if expected is None and actual is None:
                field_counts["tn"] += 1
                abstentions["correct_abstention"] += 1
                continue
            if expected == actual:
                field_counts["tp"] += 1
                continue
            exact = False
            if actual is None:
                field_counts["fn"] += 1
                abstentions["missed_value"] += 1
                category = "missed_value"
            elif expected is None:
                field_counts["fp"] += 1
                abstentions["unsupported_value"] += 1
                category = "unsupported_value"
            else:
                field_counts["fp"] += 1
                field_counts["fn"] += 1
                category = "wrong_value"
                if field == "invoice_id" and expected.lstrip("0") == actual.lstrip("0"):
                    category = "identifier_format"
            critical = field in policy["critical_fields"]
            critical_failures += int(critical)
            evidence = {
                "expected": sorted(case["evidence"][field]),
                "actual": sorted(prediction["evidence"][field]),
            }
            diffs.append({
                "case_id": case["case_id"],
                "field": field,
                "expected": case["expected"][field],
                "actual": prediction["record"][field],
                "category": category,
                "critical": critical,
                "evidence": evidence,
                "document_excerpts": {
                    side: [{"line": line, "text": document_lines[line - 1]} for line in lines]
                    for side, lines in evidence.items()
                },
            })
        exact_records += int(exact)
    micro_counts = {key: sum(item[key] for item in counts.values()) for key in ("tp", "fp", "fn", "tn")}
    case_count = len(dataset["cases"])
    report = {
        "report_version": 1,
        "mode": predictions["mode"],
        "scenario": predictions["scenario"],
        "dataset_id": dataset["dataset_id"],
        "split": dataset["split"],
        "summary": {
            "case_count": case_count,
            "prediction_count": len(predictions["predictions"]),
            "schema_valid": True,
            "coverage_complete": True,
            "micro": _rates(micro_counts),
            "exact_record_accuracy": exact_records / case_count,
            "exact_record_count": exact_records,
            "critical_failure_count": critical_failures,
            "abstentions": abstentions,
        },
        "fields": {field: _rates(counts[field]) for field in FIELDS},
        "diffs": diffs,
        "artifacts": copy.deepcopy({"dataset": dataset, "predictions": predictions, "policy": policy}),
    }
    report["gate"] = _absolute_gate(report, policy)
    return report


def _base_report(dataset: dict, predictions: dict, policy: dict) -> dict:
    start = perf_counter()
    report = _derive_report(dataset, predictions, policy)
    revision, dirty = _code_provenance()
    report["provenance"] = {
        "dataset_sha256": fingerprint(dataset),
        "predictions_sha256": fingerprint(predictions),
        "policy_sha256": fingerprint(policy),
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "code_revision": revision,
        "working_tree_dirty": dirty,
        "python_version": platform.python_version(),
        "evaluation_seconds": perf_counter() - start,
        "timing_kind": "fixture_evaluation" if predictions["mode"] == "synthetic_fixture" else "evaluation_only",
        "provider": None,
        "model": None,
        "live_calls": False,
    }
    return report


def evaluate(dataset: dict, predictions: dict, policy: dict, *, baseline: dict | None = None) -> dict:
    """Validate all inputs and evaluate every case; optionally compare a baseline.

    A quality rejection is a report. Malformed inputs, inconsistent reports and
    incompatible comparisons raise InputError. No predictions are constructed.
    """
    report = _base_report(dataset, predictions, policy)
    if baseline is not None:
        from .gate import compare_reports

        return compare_reports(baseline, report)
    return report
