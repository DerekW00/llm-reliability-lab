"""Strict JSON contracts. Validation never drops or repairs invalid input."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

FIELDS = ("invoice_id", "supplier_name", "currency", "total_amount", "due_date")
CRITICAL_FIELDS = ("invoice_id", "currency", "total_amount", "due_date")
CURRENCIES = {"USD", "EUR", "GBP", "CAD"}


class InputError(ValueError):
    """An artifact cannot be evaluated safely under the declared contract."""


def _fail(message: str) -> None:
    raise InputError(message)


def _object(value: Any, keys: set[str], where: str) -> dict:
    if not isinstance(value, dict):
        _fail(f"{where}: expected an object")
    if set(value) != keys:
        missing = sorted(keys - set(value))
        extra = sorted(str(k) for k in set(value) - keys)
        _fail(f"{where}: missing keys {missing}; unknown keys {extra}")
    return value


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{where}: expected a nonblank string")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise InputError(f"{where}: invalid Unicode") from exc
    return value


def _unique_strings(value: Any, where: str, *, nonempty: bool = True) -> list:
    if not isinstance(value, list) or (nonempty and not value):
        _fail(f"{where}: expected {'nonempty ' if nonempty else ''}array")
    for item in value:
        _text(item, where)
    if len(set(value)) != len(value):
        _fail(f"{where}: duplicate values")
    return value


def _version(value: Any, where: str) -> None:
    if type(value) is not int or value != 1:
        _fail(f"{where}: expected integer version 1")


def normalize(field: str, value: Any) -> str | Decimal | None:
    """Normalize a single valid value without erasing meaning-bearing formatting."""
    if field not in FIELDS:
        _fail(f"unknown field: {field}")
    if value is None:
        return None
    text = _text(value, field).strip()
    if field == "supplier_name":
        return " ".join(text.split()).casefold()
    if field == "currency":
        text = text.upper()
        if text not in CURRENCIES:
            _fail(f"currency: expected one of {sorted(CURRENCIES)}")
    elif field == "total_amount":
        if re.fullmatch(r"(?:0|[1-9][0-9]*)\.[0-9]{2}", text) is None:
            _fail("total_amount: expected a nonnegative decimal string with two places")
        return Decimal(text)
    elif field == "due_date":
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text) is None:
            _fail("due_date: expected YYYY-MM-DD")
        try:
            date.fromisoformat(text)
        except ValueError as exc:
            raise InputError("due_date: invalid calendar date") from exc
    return text


def _record(value: Any, where: str) -> dict:
    record = _object(value, set(FIELDS), where)
    for field in FIELDS:
        try:
            normalize(field, record[field])
        except InputError as exc:
            raise InputError(f"{where}.{field}: {exc}") from exc
    return record


def _evidence(value: Any, record: dict, document: str, where: str) -> dict:
    evidence = _object(value, set(FIELDS), where)
    count = len(document.splitlines())
    for field in FIELDS:
        lines = evidence[field]
        if not isinstance(lines, list):
            _fail(f"{where}.{field}: expected line-number array")
        if any(type(line) is not int or line < 1 or line > count for line in lines):
            _fail(f"{where}.{field}: evidence line outside 1..{count} or not an integer")
        if len(set(lines)) != len(lines):
            _fail(f"{where}.{field}: duplicate evidence lines")
        if record[field] is None and lines:
            _fail(f"{where}.{field}: null values require empty evidence")
        if record[field] is not None and not lines:
            _fail(f"{where}.{field}: non-null values require evidence")
    return evidence


def validate_dataset(data: Any) -> dict:
    dataset = _object(data, {"dataset_id", "version", "split", "cases"}, "dataset")
    _text(dataset["dataset_id"], "dataset.dataset_id")
    _version(dataset["version"], "dataset.version")
    if dataset["split"] not in ("development", "evaluation"):
        _fail("dataset.split: expected development or evaluation")
    cases = dataset["cases"]
    if not isinstance(cases, list) or not cases:
        _fail("dataset.cases: expected a nonempty array")
    seen = set()
    for i, item in enumerate(cases):
        where = f"dataset.cases[{i}]"
        case = _object(item, {"case_id", "document", "tags", "expected", "evidence",
                              "rationale"}, where)
        case_id = _text(case["case_id"], f"{where}.case_id")
        if case_id in seen:
            _fail(f"{where}: duplicate case_id {case_id}")
        seen.add(case_id)
        document = _text(case["document"], f"{where}.document")
        _unique_strings(case["tags"], f"{where}.tags")
        _text(case["rationale"], f"{where}.rationale")
        record = _record(case["expected"], f"{where}.expected")
        _evidence(case["evidence"], record, document, f"{where}.evidence")
    return dataset


def validate_predictions(data: Any, dataset: dict) -> dict:
    validate_dataset(dataset)
    predictions = _object(data, {"dataset_id", "mode", "scenario", "predictions"},
                          "predictions")
    if predictions["dataset_id"] != dataset["dataset_id"]:
        _fail("predictions.dataset_id: does not match dataset")
    if predictions["mode"] not in ("synthetic_fixture", "external_predictions"):
        _fail("predictions.mode: unsupported mode")
    _text(predictions["scenario"], "predictions.scenario")
    records = predictions["predictions"]
    if not isinstance(records, list):
        _fail("predictions.predictions: expected an array")
    cases = {case["case_id"]: case for case in dataset["cases"]}
    seen = set()
    for i, item in enumerate(records):
        where = f"predictions.predictions[{i}]"
        prediction = _object(item, {"case_id", "record", "evidence"}, where)
        case_id = _text(prediction["case_id"], f"{where}.case_id")
        if case_id in seen:
            _fail(f"{where}: duplicate case_id {case_id}")
        if case_id not in cases:
            _fail(f"{where}: unknown case_id {case_id}")
        seen.add(case_id)
        record = _record(prediction["record"], f"{where}.record")
        _evidence(prediction["evidence"], record, cases[case_id]["document"],
                  f"{where}.evidence")
    missing = sorted(set(cases) - seen)
    if missing:
        _fail(f"predictions: missing case IDs {missing}")
    return predictions


def validate_policy(data: Any) -> dict:
    policy = _object(data, {"version", "critical_fields", "max_critical_failures",
                            "min_micro_f1", "min_exact_record_accuracy", "min_field_f1",
                            "max_micro_f1_drop", "max_exact_record_accuracy_drop"}, "policy")
    _version(policy["version"], "policy.version")
    critical = _unique_strings(policy["critical_fields"], "policy.critical_fields")
    if not set(critical) <= set(FIELDS):
        _fail("policy.critical_fields: unknown field")
    count = policy["max_critical_failures"]
    if type(count) is not int or count < 0:
        _fail("policy.max_critical_failures: expected nonnegative integer")

    def rate(value: Any, where: str) -> None:
        if type(value) not in (int, float) or not 0 <= value <= 1 or not math.isfinite(value):
            _fail(f"{where}: expected finite rate in [0,1]")

    for key in ("min_micro_f1", "min_exact_record_accuracy", "max_micro_f1_drop",
                "max_exact_record_accuracy_drop"):
        rate(policy[key], f"policy.{key}")
    minima = _object(policy["min_field_f1"], set(FIELDS), "policy.min_field_f1")
    for field, value in minima.items():
        rate(value, f"policy.min_field_f1.{field}")
    return policy


def read_json(path: str | Path) -> dict:
    def pairs(items: list[tuple[str, Any]]) -> dict:
        obj: dict = {}
        for key, value in items:
            if key in obj:
                _fail(f"duplicate JSON key: {key}")
            obj[key] = value
        return obj

    def constant(value: str) -> None:
        _fail(f"non-finite JSON number: {value}")

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                           parse_constant=constant)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise InputError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        _fail(f"{path}: expected a JSON object")
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, float) and not math.isfinite(item):
            _fail(f"{path}: non-finite JSON number")
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return value


def _case_order(item: Any) -> tuple[str, str]:
    return item["case_id"], json.dumps(item, ensure_ascii=False, sort_keys=True,
                                       separators=(",", ":"), allow_nan=False)


def fingerprint(artifact: dict) -> str:
    """Hash payload content independently of object keys and case-array ordering."""
    try:
        value = dict(artifact)
        for key in ("cases", "predictions"):
            if isinstance(value.get(key), list):
                # Ordering by case_id alone is not a total order once an artifact
                # repeats one, which would leak input order into the hash.
                value[key] = sorted(value[key], key=_case_order)
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise InputError(f"Cannot fingerprint artifact: {exc}") from exc
    return hashlib.sha256(encoded).hexdigest()
