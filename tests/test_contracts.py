"""Contract boundaries tested independently of the synthetic demonstration."""

import copy
from decimal import Decimal

import pytest

from reliability_lab.contracts import (
    FIELDS,
    InputError,
    fingerprint,
    normalize,
    read_json,
    validate_dataset,
    validate_policy,
    validate_predictions,
)
from reliability_lab.resources import resource_path


def case(case_id="test-1"):
    record = dict(zip(FIELDS, ["0007", "Sample Co", "USD", "0.00", "2028-02-29"], strict=True))
    return {"case_id": case_id, "document": "0007 Sample Co USD 0.00 due 2028-02-29",
            "tags": ["original-unit-test"], "expected": record,
            "evidence": {f: [1] for f in FIELDS}, "rationale": "All explicit on line 1."}


def dataset():
    return {"dataset_id": "test", "version": 1, "split": "evaluation", "cases": [case()]}


def predictions(data):
    return {"dataset_id": data["dataset_id"], "mode": "external_predictions",
            "scenario": "test", "predictions": [
                {"case_id": c["case_id"], "record": copy.deepcopy(c["expected"]),
                 "evidence": copy.deepcopy(c["evidence"])} for c in data["cases"]]}


def test_meaning_preserving_normalization():
    assert normalize("invoice_id", " 0007 ") == "0007"
    assert normalize("invoice_id", "ab-7") != normalize("invoice_id", "AB-7")
    assert normalize("supplier_name", "  Sample\t CO ") == "sample co"
    assert normalize("currency", " usd ") == "USD"
    assert normalize("total_amount", "0.00") == Decimal("0.00")
    assert normalize("total_amount", "9007199254740993.01") == Decimal("9007199254740993.01")
    assert normalize("due_date", "2028-02-29") == "2028-02-29"
    assert normalize("total_amount", None) is None


@pytest.mark.parametrize("field,value", [
    ("invoice_id", ""), ("invoice_id", 7), ("supplier_name", " \n "),
    ("currency", "US"), ("currency", "JPY"), ("total_amount", 12.50),
    ("total_amount", "1e3"), ("total_amount", "00.00"), ("total_amount", "-1.00"),
    ("total_amount", "1.001"), ("total_amount", "NaN"), ("total_amount", "١.00"),
    ("due_date", "2027-02-29"), ("due_date", "02/03/2027"),
    ("due_date", "20280229"), ("due_date", "2028-02-29T00:00:00"),
])
def test_invalid_values_are_not_coerced(field, value):
    with pytest.raises(InputError):
        normalize(field, value)


@pytest.mark.parametrize("mutation", [
    lambda d: d.update(version=True),
    lambda d: d.update(cases=[]),
    lambda d: d.update(extra=1),
    lambda d: d["cases"].append(copy.deepcopy(d["cases"][0])),
    lambda d: d["cases"][0]["expected"].pop("currency"),
    lambda d: d["cases"][0]["evidence"].update(currency=[2]),
    lambda d: d["cases"][0]["evidence"].update(currency=[True]),
    lambda d: d["cases"][0]["evidence"].update(currency=[1, 1]),
    lambda d: d["cases"][0]["evidence"].update(currency=[]),
    lambda d: d["cases"][0]["expected"].update(currency=None),
    lambda d: d["cases"][0].update(document=""),
])
def test_bad_dataset_fails_closed(mutation):
    data = dataset()
    mutation(data)
    with pytest.raises(InputError):
        validate_dataset(data)


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(dataset_id="other"),
    lambda p: p.update(predictions=[]),
    lambda p: p["predictions"].append(copy.deepcopy(p["predictions"][0])),
    lambda p: p["predictions"][0].update(case_id="unknown"),
    lambda p: p["predictions"][0]["record"].pop("invoice_id"),
    lambda p: p["predictions"][0]["evidence"].update(invoice_id=[0]),
])
def test_bad_predictions_cannot_disappear(mutation):
    data = dataset()
    pred = predictions(data)
    mutation(pred)
    with pytest.raises(InputError):
        validate_predictions(pred, data)


def test_full_null_record_is_valid_when_evidence_empty():
    data = dataset()
    data["cases"][0]["expected"] = dict.fromkeys(FIELDS)
    data["cases"][0]["evidence"] = {f: [] for f in FIELDS}
    assert validate_dataset(data) == data
    validate_predictions(predictions(data), data)


@pytest.mark.parametrize("value", [True, -0.01, 1.01, float("inf"), float("nan"),
                                  "0.98", 10 ** 1000, None])
def test_invalid_policy_threshold(value):
    policy = read_json(resource_path("policy.json"))
    policy["min_micro_f1"] = value
    with pytest.raises(InputError):
        validate_policy(policy)


@pytest.mark.parametrize("text", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}',
                                  '{"a":1e400}', '{"a":[-1e400]}', '[]', '{broken'])
def test_strict_json(tmp_path, text):
    path = tmp_path / "bad.json"
    path.write_text(text)
    with pytest.raises(InputError):
        read_json(path)


def test_missing_and_non_utf8_files(tmp_path):
    with pytest.raises(InputError):
        read_json(tmp_path / "missing.json")
    bad = tmp_path / "invalid.json"
    bad.write_bytes(b"\xff")
    with pytest.raises(InputError):
        read_json(bad)


def test_fingerprint_ignores_case_order_not_content():
    data = dataset()
    data["cases"].append(case("test-2"))
    original = fingerprint(data)
    data["cases"].reverse()
    assert fingerprint(data) == original
    data["cases"][0]["document"] += "\nNew information"
    assert fingerprint(data) != original


def test_resources_outside_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert read_json(resource_path("policy.json"))["version"] == 1
    with pytest.raises(InputError):
        resource_path("../policy.json")
