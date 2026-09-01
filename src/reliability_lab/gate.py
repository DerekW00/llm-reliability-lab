"""Policy decisions and replay validation of embedded evaluation reports."""

from __future__ import annotations

import copy
import math
import re
from datetime import datetime
from fractions import Fraction
from typing import Any

from .contracts import FIELDS, InputError, fingerprint

# Bound replay cost and reject recursive Python objects before copying them.
MAX_BASELINE_DEPTH = 16
MAX_JSON_DEPTH = 128


def _metric_fraction(report: dict, metric: str, field: str | None = None) -> Fraction | None:
    if metric == "exact_record_accuracy":
        return Fraction(report["summary"]["exact_record_count"], report["summary"]["case_count"])
    counts = report["fields"][field] if field else report["summary"]["micro"]
    denominator = 2 * counts["tp"] + counts["fp"] + counts["fn"]
    return Fraction(2 * counts["tp"], denominator) if denominator else None


def _check(name: str, actual: int | float | None, required: int | float,
           value: Fraction | int | None, *, minimum: bool) -> dict:
    boundary = Fraction(str(required))
    passed = value is not None and (value >= boundary if minimum else value <= boundary)
    return {"name": name, "passed": passed, "actual": actual, "required": required}


def _decision(checks: list[dict]) -> dict:
    reasons = []
    for check in checks:
        if check["passed"]:
            continue
        name, actual, required = (check[key] for key in ("name", "actual", "required"))
        if actual is None:
            reasons.append(f"{name} is undefined; required threshold is {required}.")
        elif name == "critical_failure_count" or name.endswith("_drop"):
            reasons.append(f"{name} {actual} exceeds maximum {required}.")
        else:
            reasons.append(f"{name} {actual} is below minimum {required}.")
    return {"accepted": not reasons, "reasons": reasons, "checks": checks}


def _absolute_gate(report: dict, policy: dict) -> dict:
    summary = report["summary"]
    critical = summary["critical_failure_count"]
    checks = [_check("critical_failure_count", critical, policy["max_critical_failures"],
                     critical, minimum=False)]
    checks.append(_check("micro_f1", summary["micro"]["f1"], policy["min_micro_f1"],
                         _metric_fraction(report, "f1"), minimum=True))
    checks.append(_check("exact_record_accuracy", summary["exact_record_accuracy"],
                         policy["min_exact_record_accuracy"],
                         _metric_fraction(report, "exact_record_accuracy"), minimum=True))
    for field in FIELDS:
        checks.append(_check(f"field_f1.{field}", report["fields"][field]["f1"],
                             policy["min_field_f1"][field],
                             _metric_fraction(report, "f1", field), minimum=True))
    return _decision(checks)


def _compatible(baseline: dict, candidate: dict) -> None:
    for key in ("dataset_sha256", "policy_sha256"):
        if baseline["provenance"][key] != candidate["provenance"][key]:
            raise InputError(f"comparison: incompatible {key}")
    if baseline["mode"] != candidate["mode"]:
        raise InputError("comparison: incompatible prediction modes")
    if not baseline["gate"]["accepted"]:
        raise InputError("comparison: baseline must be accepted")


def _apply_comparison(baseline: dict, candidate: dict) -> dict:
    _compatible(baseline, candidate)
    policy = candidate["artifacts"]["policy"]
    checks = list(candidate["gate"]["checks"])
    for name, metric in (("micro_f1", "f1"), ("exact_record_accuracy", "exact_record_accuracy")):
        before = _metric_fraction(baseline, metric)
        after = _metric_fraction(candidate, metric)
        drop = before - after if before is not None and after is not None else None
        checks.append(_check(f"{name}_drop", float(drop) if drop is not None else None,
                             policy[f"max_{name}_drop"], drop, minimum=False))
    candidate["gate"] = _decision(checks)
    candidate["artifacts"]["baseline"] = copy.deepcopy(baseline)
    return candidate


def _json_tree(value: Any, *, path: str = "report", depth: int = 0,
               active: set[int] | None = None) -> None:
    if depth > MAX_JSON_DEPTH:
        raise InputError(f"{path}: excessive JSON nesting")
    if value is None or type(value) in (str, int, bool):
        if isinstance(value, str):
            try:
                value.encode("utf-8")
            except UnicodeError as exc:
                raise InputError(f"{path}: invalid Unicode") from exc
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise InputError(f"{path}: non-finite number")
        return
    if type(value) not in (dict, list):
        raise InputError(f"{path}: expected JSON value")
    active = set() if active is None else active
    if id(value) in active:
        raise InputError(f"{path}: cyclic report")
    active.add(id(value))
    try:
        items = value.items() if isinstance(value, dict) else enumerate(value)
        for key, item in items:
            if isinstance(value, dict) and type(key) is not str:
                raise InputError(f"{path}: object key must be a string")
            _json_tree(item, path=f"{path}.{key}", depth=depth + 1, active=active)
    finally:
        active.remove(id(value))


def _keys(value: Any, keys: set[str], path: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise InputError(f"{path}: invalid object keys or type")


def _matches(actual: Any, expected: Any, path: str) -> None:
    """Compare reconstructed structure without Python's bool == 1 loophole."""
    if isinstance(expected, dict):
        _keys(actual, set(expected), path)
        for key, value in expected.items():
            _matches(actual[key], value, f"{path}.{key}")
        return
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise InputError(f"{path}: inconsistent array")
        for index, (left, right) in enumerate(zip(actual, expected, strict=True)):
            _matches(left, right, f"{path}[{index}]")
        return
    if type(expected) is float:
        valid_type = type(actual) in (int, float)
    else:
        valid_type = type(actual) is type(expected)
    if not valid_type or actual != expected:
        raise InputError(f"{path}: inconsistent value or type")


def _validate_provenance(report: dict) -> None:
    provenance = report["provenance"]
    keys = {"dataset_sha256", "predictions_sha256", "policy_sha256", "timestamp_utc",
            "code_revision", "working_tree_dirty", "python_version", "evaluation_seconds",
            "timing_kind", "provider", "model", "live_calls"}
    _keys(provenance, keys, "report.provenance")
    for artifact in ("dataset", "predictions", "policy"):
        _matches(provenance[f"{artifact}_sha256"], fingerprint(report["artifacts"][artifact]),
                 f"report.provenance.{artifact}_sha256")
    _matches(provenance["provider"], None, "report.provenance.provider")
    _matches(provenance["model"], None, "report.provenance.model")
    _matches(provenance["live_calls"], False, "report.provenance.live_calls")
    timing = "fixture_evaluation" if report["mode"] == "synthetic_fixture" else "evaluation_only"
    _matches(provenance["timing_kind"], timing, "report.provenance.timing_kind")
    seconds = provenance["evaluation_seconds"]
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
        raise InputError("report.provenance.evaluation_seconds: expected finite nonnegative number")
    revision = provenance["code_revision"]
    if revision is not None and (not isinstance(revision, str)
                                 or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision) is None):
        raise InputError("report.provenance.code_revision: expected Git hash or null")
    dirty = provenance["working_tree_dirty"]
    if dirty is not None and type(dirty) is not bool:
        raise InputError("report.provenance.working_tree_dirty: expected boolean or null")
    if (revision is None) != (dirty is None):
        raise InputError("report.provenance: revision and dirty state must both be known or null")
    version = provenance["python_version"]
    if not isinstance(version, str) or not version.strip():
        raise InputError("report.provenance.python_version: expected a nonblank string")
    timestamp = provenance["timestamp_utc"]
    try:
        if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
            raise ValueError
        parsed = datetime.fromisoformat(timestamp[:-1] + "+00:00")
        if parsed.utcoffset().total_seconds() != 0:
            raise ValueError
    except (ValueError, AttributeError) as exc:
        raise InputError("report.provenance.timestamp_utc: expected UTC ISO timestamp ending Z") from exc


def _recompute_report(report: dict, *, depth: int = 1) -> dict:
    from .evaluation import _derive_report

    if depth > MAX_BASELINE_DEPTH:
        raise InputError(f"report: baseline nesting exceeds {MAX_BASELINE_DEPTH} reports")
    _keys(report, {"report_version", "mode", "scenario", "dataset_id", "split", "summary",
                   "fields", "diffs", "gate", "provenance", "artifacts"}, "report")
    artifacts = report["artifacts"]
    if not isinstance(artifacts, dict):
        raise InputError("report.artifacts: expected an object")
    _keys(artifacts, {"dataset", "predictions", "policy"} | ({"baseline"} if "baseline" in artifacts else set()),
          "report.artifacts")
    derived = _derive_report(artifacts["dataset"], artifacts["predictions"], artifacts["policy"])
    _validate_provenance(report)
    derived["provenance"] = copy.deepcopy(report["provenance"])
    if "baseline" in artifacts:
        baseline = _recompute_report(artifacts["baseline"], depth=depth + 1)
        _apply_comparison(baseline, derived)
    for key in ("report_version", "mode", "scenario", "dataset_id", "split", "summary",
                "fields", "diffs", "gate"):
        _matches(report[key], derived[key], f"report.{key}")
    return derived


def _baseline_identity(report: dict) -> dict:
    identity = {
        "dataset": report["provenance"]["dataset_sha256"],
        "predictions": report["provenance"]["predictions_sha256"],
        "policy": report["provenance"]["policy_sha256"],
        "summary": report["summary"], "fields": report["fields"], "gate": report["gate"],
    }
    if "baseline" in report["artifacts"]:
        identity["baseline"] = _baseline_identity(report["artifacts"]["baseline"])
    return identity


def compare_reports(baseline: dict, candidate: dict) -> dict:
    """Replay reports and apply absolute and relative checks against a valid baseline.

    Supplied scores and decisions are never trusted. An already-compared candidate
    retains its original baseline; selecting a different one is an input error.
    """
    from .evaluation import _base_report

    _json_tree(baseline, path="baseline")
    _json_tree(candidate, path="candidate")
    verified_baseline = _recompute_report(baseline)
    verified_candidate = _recompute_report(candidate)
    previous = verified_candidate["artifacts"].get("baseline")
    if previous is not None:
        _matches(_baseline_identity(verified_baseline), _baseline_identity(previous),
                 "comparison: candidate already uses a different baseline")
    _compatible(verified_baseline, verified_candidate)
    # A new report records the code/time used for this replay. Original baseline
    # provenance remains attached as supplied, after validation.
    artifacts = verified_candidate["artifacts"]
    fresh = _base_report(artifacts["dataset"], artifacts["predictions"], artifacts["policy"])
    return _apply_comparison(verified_baseline, fresh)
