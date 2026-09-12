"""Checks on the frozen synthetic corpus, separate from evaluator unit tests."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

import pytest

from reliability_lab.contracts import (
    FIELDS,
    normalize,
    read_json,
    validate_dataset,
    validate_predictions,
)

ROOT = Path(__file__).resolve().parents[1]
FROZEN_SHA256 = {
    "data/development.json": "6ea77e04ff6ced3af2cebbc9ef25856acd247231048cdc94e6aa8819edbfa24a",
    "data/evaluation.json": "27b447e9318d25a4af94e2801ce35199e34771f0837603306172cbd8b89117e0",
    "policy.json": "b81326e57c06b797858a346824596d2e84d6e64c4ad7b56c90a6027652b43ff2",
}
LEADING_ZERO_CASES = {
    "EVAL-01", "EVAL-04", "EVAL-09", "EVAL-12",
    "EVAL-17", "EVAL-23", "EVAL-31", "EVAL-37",
}
FIXTURE_SHA256 = {
    "baseline": "f39542c5f9c7ed633f96629fe2a7ba29913610fb77c56ebe15a5e7a4389a18ca",
    "regression": "26ce19c971de3e4d1f07bfc1be320d07b7687db3a07d65e457ce0a7aa64629c4",
    "repaired": "0977102b09d3ee9f9699b630c5f43036f38fbc0afc4f367405ed6b59a4bcd7f7",
}
SUPPLEMENT_SHA256 = "b4ef2f5874b902fe530f2538d27ff5a657521aafb495507238b54ec1f04352f0"


def dataset(split: str) -> dict:
    return read_json(ROOT / "data" / f"{split}.json")


def cases_by_id() -> dict:
    return {case["case_id"]: case for case in dataset("evaluation")["cases"]}


def family(case: dict) -> str:
    families = [tag for tag in case["tags"] if tag.startswith("family:")]
    assert len(families) == 1
    return families[0]


def masked_template(case: dict) -> str:
    """Mask content values so renamed or renumbered templates remain detectable.

    This heuristic supplements authored layout families. It is not a guarantee of
    semantic independence, nor a statistical leakage detector.
    """
    text = case["document"].casefold()
    values = [(field, value) for field, value in case["expected"].items() if value]
    for field, value in sorted(values, key=lambda pair: len(pair[1]), reverse=True):
        pattern = r"\s+".join(re.escape(token) for token in value.casefold().split())
        text = re.sub(pattern, f"<{field}>", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "<date>", text)
    text = re.sub(r"\b\d{1,2}/\d{1,2}/\d{4}\b", "<date>", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", "<number>", text)
    return " ".join(text.split())


def test_frozen_bytes_and_manifest_match_independent_pins():
    manifest = read_json(ROOT / "data/manifest.json")
    assert manifest["sha256_kind"] == "raw_file_bytes"
    assert manifest["construction_stage"] == (
        "documents_and_labels_frozen_before_prediction_construction"
    )
    assert manifest["provenance"] == "original_synthetic_agent_authored_and_agent_reviewed"
    assert set(manifest["files"]) == {"data/development.json", "data/evaluation.json"}
    for relative, digest in FROZEN_SHA256.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
        entry = manifest["policy"] if relative == "policy.json" else manifest["files"][relative]
        assert entry["sha256"] == digest
        if relative != "policy.json":
            data = read_json(ROOT / relative)
            assert entry["case_count"] == len(data["cases"])
            assert entry["dataset_id"] == data["dataset_id"]


@pytest.mark.parametrize(("split", "count", "prefix"), [
    ("development", 20, "DEV"), ("evaluation", 40, "EVAL"),
])
def test_complete_strict_datasets_with_auditable_labels(split, count, prefix):
    data = dataset(split)
    assert validate_dataset(data) is data
    assert data["split"] == split
    assert len(data["cases"]) == count
    assert {case["case_id"] for case in data["cases"]} == {
        f"{prefix}-{index:02d}" for index in range(1, count + 1)
    }
    for case in data["cases"]:
        assert 2 <= len(case["document"].splitlines()) <= 10
        assert len(case["rationale"]) >= 60
        family(case)
        for field in FIELDS:
            assert bool(case["evidence"][field]) == (case["expected"][field] is not None)


def test_split_families_documents_and_case_ids_are_disjoint():
    development = dataset("development")["cases"]
    evaluation = dataset("evaluation")["cases"]
    assert len({family(case) for case in development}) == 20
    assert len({family(case) for case in evaluation}) == 40
    assert {family(case) for case in development}.isdisjoint(family(case) for case in evaluation)
    for key in ("case_id", "document"):
        assert {case[key] for case in development}.isdisjoint(case[key] for case in evaluation)


def test_no_cross_split_near_duplicate_templates_after_value_masking():
    for dev in dataset("development")["cases"]:
        for evaluation in dataset("evaluation")["cases"]:
            similarity = SequenceMatcher(
                None, masked_template(dev), masked_template(evaluation), autojunk=False,
            ).ratio()
            assert similarity < 0.80, (
                f"Potential template reuse: {dev['case_id']} / {evaluation['case_id']} "
                f"at {similarity:.3f}; inspect the original documents."
            )


def test_template_guard_detects_parameter_only_swaps():
    first = {
        "document": "Seller: Cedar Mock\nInvoice: AA-1\nTotal: USD 12.30\nDue: 2026-10-01",
        "expected": dict(zip(FIELDS, ["AA-1", "Cedar Mock", "USD", "12.30", "2026-10-01"])),
    }
    renamed = {
        "document": "Seller: Maple Fiction\nInvoice: BB-2\nTotal: EUR 99.90\nDue: 2027-02-03",
        "expected": dict(zip(FIELDS, ["BB-2", "Maple Fiction", "EUR", "99.90", "2027-02-03"])),
    }
    assert masked_template(first) == masked_template(renamed)


def test_numeric_identifiers_cover_bug_and_unaffected_controls():
    cases = cases_by_id()
    affected = {
        case_id for case_id, case in cases.items()
        if isinstance((value := case["expected"]["invoice_id"]), str)
        and re.fullmatch(r"[0-9]+", value) and str(int(value)) != value
    }
    assert affected == LEADING_ZERO_CASES
    assert cases["EVAL-31"]["expected"]["invoice_id"] == "0000"
    assert cases["EVAL-28"]["expected"]["invoice_id"] == "429"
    assert cases["EVAL-21"]["expected"]["invoice_id"] == "00A-21"
    assert cases["EVAL-36"]["expected"]["invoice_id"] == "000-51"


def test_abstentions_zero_and_date_conventions_have_distinct_labels():
    cases = cases_by_id()
    all_null = cases["EVAL-30"]
    assert all_null["expected"] == dict.fromkeys(FIELDS)
    assert all_null["evidence"] == {field: [] for field in FIELDS}
    assert cases["EVAL-03"]["expected"]["total_amount"] == "0.00"
    assert cases["EVAL-31"]["expected"]["total_amount"] == "0.00"
    for case_id, field in [
        ("EVAL-05", "invoice_id"), ("EVAL-06", "currency"),
        ("EVAL-07", "due_date"), ("EVAL-10", "currency"),
        ("EVAL-11", "supplier_name"), ("EVAL-13", "total_amount"),
        ("EVAL-14", "due_date"), ("EVAL-18", "due_date"),
        ("EVAL-26", "invoice_id"), ("EVAL-29", "due_date"),
        ("EVAL-34", "total_amount"), ("EVAL-38", "currency"),
    ]:
        assert cases[case_id]["expected"][field] is None
        assert cases[case_id]["evidence"][field] == []
    for case_id, date in [("EVAL-15", "2026-08-12"), ("EVAL-35", "2027-01-07")]:
        assert cases[case_id]["expected"]["due_date"] == date
        assert len(cases[case_id]["evidence"]["due_date"]) == 2
    assert cases["EVAL-22"]["expected"]["due_date"] == "2028-02-29"


def test_instruction_like_text_does_not_supply_reference_labels():
    cases = cases_by_id()
    assert cases["EVAL-08"]["expected"]["total_amount"] == "460.25"
    assert cases["EVAL-08"]["expected"]["due_date"] == "2026-12-08"
    assert cases["EVAL-32"]["expected"]["invoice_id"] == "FSS[32]"
    assert cases["EVAL-32"]["expected"]["currency"] == "CAD"
    for case_id, instruction_line in [("EVAL-08", 5), ("EVAL-32", 3)]:
        assert "source_instruction" in cases[case_id]["tags"]
        assert all(instruction_line not in refs for refs in cases[case_id]["evidence"].values())


def test_reference_values_appear_in_cited_text_or_declared_date_format():
    """Catch swapped lines and label typos, without claiming full semantic entailment."""
    for split in ("development", "evaluation"):
        for case in dataset(split)["cases"]:
            lines = case["document"].splitlines()
            for field in FIELDS:
                value = case["expected"][field]
                if value is None:
                    continue
                excerpt = " ".join(lines[number - 1] for number in case["evidence"][field])
                if field == "supplier_name":
                    assert normalize(field, value) in " ".join(excerpt.split()).casefold()
                elif field == "due_date" and value not in excerpt:
                    pattern = "%m/%d/%Y" if "MM/DD/YYYY" in excerpt else "%d/%m/%Y"
                    assert "MM/DD/YYYY" in excerpt or "DD/MM/YYYY" in excerpt
                    dates = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", excerpt)
                    assert any(datetime.strptime(date, pattern).date().isoformat() == value
                               for date in dates)
                else:
                    assert value in excerpt, (case["case_id"], field, excerpt)


@pytest.mark.parametrize("scenario", ["baseline", "regression", "repaired"])
def test_static_fixtures_are_frozen_valid_and_complete(scenario):
    path = ROOT / "data/predictions" / f"{scenario}.json"
    artifact = read_json(path)
    assert validate_predictions(artifact, dataset("evaluation")) is artifact
    assert artifact["mode"] == "synthetic_fixture"
    assert artifact["scenario"] == scenario
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == FIXTURE_SHA256[scenario]
    manifest = read_json(ROOT / "data/predictions/manifest.json")
    assert manifest["files"][f"data/predictions/{scenario}.json"] == digest
    assert manifest["dataset_freeze_commit"] == "c2c4c4f26abbe413eb8db02e1b2570f3ffd458b2"


def test_baseline_has_exactly_one_noncritical_error_and_repair_retains_it():
    baseline = read_json(ROOT / "data/predictions/baseline.json")
    repaired = read_json(ROOT / "data/predictions/repaired.json")
    cases = cases_by_id()
    mismatches = [
        (prediction["case_id"], field)
        for prediction in baseline["predictions"] for field in FIELDS
        if normalize(field, prediction["record"][field])
        != normalize(field, cases[prediction["case_id"]]["expected"][field])
    ]
    assert mismatches == [("EVAL-02", "supplier_name")]
    assert repaired["predictions"] == baseline["predictions"]


def test_regression_is_exactly_the_documented_numeric_coercion():
    baseline = read_json(ROOT / "data/predictions/baseline.json")
    regression = read_json(ROOT / "data/predictions/regression.json")
    candidates = {prediction["case_id"]: prediction for prediction in regression["predictions"]}
    changed = set()
    for original in baseline["predictions"]:
        candidate = candidates[original["case_id"]]
        expected_record = original["record"].copy()
        invoice_id = expected_record["invoice_id"]
        if isinstance(invoice_id, str) and re.fullmatch(r"[0-9]+", invoice_id):
            expected_record["invoice_id"] = str(int(invoice_id))
        assert candidate["record"] == expected_record
        assert candidate["evidence"] == original["evidence"]
        if expected_record != original["record"]:
            changed.add(original["case_id"])
    assert changed == LEADING_ZERO_CASES


def test_supplemental_duplicate_looking_cases_remain_two_distinct_invoices():
    relative = "data/duplicate-looking-development.json"
    data = read_json(ROOT / relative)
    assert validate_dataset(data) is data
    assert data["split"] == "development"
    assert len(data["cases"]) == 2
    first, second = data["cases"]
    assert {first["case_id"], second["case_id"]} == {"DUPDEV-01", "DUPDEV-02"}
    assert first["expected"]["invoice_id"] == "011842"
    assert second["expected"]["invoice_id"] == "011843"
    assert first["document"].replace("011842", "011843") == second["document"]
    for field in FIELDS[1:]:
        assert first["expected"][field] == second["expected"][field]
    assert "duplicate_looking" in first["tags"] and "duplicate_looking" in second["tags"]
    assert masked_template(first) == masked_template(second)
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == SUPPLEMENT_SHA256
    manifest = read_json(ROOT / "data/duplicate-looking-manifest.json")
    assert manifest["files"][relative]["sha256"] == SUPPLEMENT_SHA256
    assert manifest["files"][relative]["case_count"] == 2
    assert manifest["construction_stage"] == (
        "supplemental_development_only_after_primary_fixture_construction"
    )
    evaluation = dataset("evaluation")["cases"]
    assert {family(first), family(second)}.isdisjoint(family(case) for case in evaluation)
    for supplement in data["cases"]:
        for case in evaluation:
            assert SequenceMatcher(None, masked_template(supplement), masked_template(case),
                                   autojunk=False).ratio() < 0.80
