"""Checks on the frozen synthetic corpus, separate from evaluator unit tests."""

from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from pathlib import Path

import pytest

from reliability_lab.contracts import FIELDS, read_json, validate_dataset

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
