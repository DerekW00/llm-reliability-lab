"""Readable reports and guarded, atomic-per-file report publication."""

from __future__ import annotations

import html
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Iterable

from .contracts import FIELDS, InputError


def safe_text(value: object) -> str:
    """Make supplied text inert in a terminal, including ANSI and bidi controls.

    Escapes are unambiguous: a fixed width per prefix, and a literal backslash is
    escaped too, so distinct inputs never render as the same inspectable text.
    """
    pieces = []
    for char in str(value):
        code = ord(char)
        if char == "\\":
            pieces.append("\\\\")
        elif unicodedata.category(char).startswith("C") or char in "\u2028\u2029":
            if code <= 0xFF:
                pieces.append(f"\\x{code:02x}")
            elif code <= 0xFFFF:
                pieces.append(f"\\u{code:04x}")
            else:
                pieces.append(f"\\U{code:08x}")
        else:
            pieces.append(char)
    return "".join(pieces)


def _md(value: object) -> str:
    text = html.escape(safe_text(value), quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|~>-])", r"\\\1", text)


def _value(value: object) -> str:
    return _md(json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True))


def _seconds(value: object) -> str:
    """Validation admits any finite JSON number here, including ints too big for a float."""
    try:
        return f"{float(value):.6f}"
    except (OverflowError, TypeError, ValueError):
        return safe_text(value)


def _rate(value: float | None, numerator: int, denominator: int) -> str:
    if value is None:
        return f"null (undefined; {numerator}/{denominator})"
    return f"{value:.4%} ({numerator}/{denominator})"


def _rates(counts: dict) -> tuple[str, str, str]:
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    return (
        _rate(counts["precision"], tp, tp + fp),
        _rate(counts["recall"], tp, tp + fn),
        _rate(counts["f1"], 2 * tp, 2 * tp + fp + fn),
    )


def _remediation(diff: dict) -> str:
    category = diff["category"]
    field = diff["field"]
    if category == "identifier_format":
        return "Keep invoice IDs as strings through postprocessing; preserve leading zeros."
    if category == "unsupported_value":
        return "Return null when the document does not determine this value; avoid guessing."
    if category == "missed_value":
        return "Recover the explicit source value and cite its line instead of abstaining."
    if field == "supplier_name":
        return "Check supplier selection and spelling against the cited source."
    return f"Check {field} against the cited source and the field normalization rules."


def render_report(report: dict) -> str:
    """Render evaluator output; all supplied text is escaped for Markdown/terminals."""
    summary = report["summary"]
    gate = report["gate"]
    synthetic = report["mode"] == "synthetic_fixture"
    lines = ["# LLM Reliability Lab", ""]
    if synthetic:
        lines += [
            "**SYNTHETIC FIXTURE EVALUATION**",
            "Authored fixtures, no live model calls. These scores are not model accuracy "
            "or production evidence.",
        ]
    else:
        lines += [
            "**EXTERNAL PREDICTION EVALUATION**",
            "User-supplied predictions; no live model calls were made by this evaluator.",
        ]
    lines += [
        "",
        f"**Decision: {'ACCEPTED' if gate['accepted'] else 'REJECTED'}**",
        f"Dataset: {_md(report['dataset_id'])}; split: {_md(report['split'])}; "
        f"scenario: {_md(report['scenario'])}.",
        "",
        "## Coverage and metrics",
        "",
        f"Cases: {summary['case_count']}; predictions: {summary['prediction_count']}; "
        f"complete coverage: {str(summary['coverage_complete']).lower()}; "
        f"schema valid: {str(summary['schema_valid']).lower()}.",
        "",
        "Rates show numerator/denominator. A zero denominator is null (undefined). "
        "Wrong non-null values count as both FP and FN. TP = correct values; "
        "FP = wrong or invented values; FN = wrong or missed values; TN = correct nulls.",
        "",
        "| Scope | TP | FP | FN | TN | Precision | Recall | F1 |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for name, counts in [("micro", summary["micro"]), *report["fields"].items()]:
        precision, recall, f1 = _rates(counts)
        lines.append(
            f"| {_md(name)} | {counts['tp']} | {counts['fp']} | {counts['fn']} | "
            f"{counts['tn']} | {precision} | {recall} | {f1} |"
        )
    lines += [
        "",
        "Exact-record accuracy: "
        + _rate(summary["exact_record_accuracy"], summary["exact_record_count"],
                summary["case_count"])
        + ".",
        f"Critical failures: **{summary['critical_failure_count']} field mismatches** "
        "(not a count of records).",
        "",
        "| Abstention measure | Count |",
        "| --- | ---: |",
    ]
    for key in ("expected_null", "predicted_null", "correct_abstention", "missed_value",
                "unsupported_value"):
        lines.append(f"| {key.replace('_', ' ')} | {summary['abstentions'][key]} |")
    lines += ["", "## Gate checks", ""]
    if gate["reasons"]:
        lines.append("Failed rules:")
        lines.append("")
        lines += [f"- {_md(reason)}" for reason in gate["reasons"]]
        lines.append("")
    else:
        lines += ["All required policy checks passed.", ""]
    lines += [
        "| Rule | Result | Actual | Required |",
        "| --- | --- | --- | --- |",
    ]
    for check in gate["checks"]:
        lines.append(
            f"| {_md(check['name'])} | {'PASS' if check['passed'] else 'FAIL'} | "
            f"{_value(check['actual'])} | {_value(check['required'])} |"
        )
    diffs = sorted(report["diffs"], key=lambda diff: (
        not diff["critical"], diff["case_id"], FIELDS.index(diff["field"])
    ))
    shown = diffs[:10]
    lines += ["", "## Representative differences", ""]
    if not diffs:
        lines.append("No normalized field differences.")
    else:
        lines += [
            f"Showing {len(shown)} of {len(diffs)} field differences, critical first. "
            "The JSON report contains every difference.",
            "",
        ]
        for diff in shown:
            severity = "CRITICAL" if diff["critical"] else "noncritical"
            lines += [
                f"### {_md(diff['case_id'])} / {_md(diff['field'])} ({severity})",
                "",
                f"Category: {_md(diff['category'])}. Expected: {_value(diff['expected'])}; "
                f"actual: {_value(diff['actual'])}.",
                "",
                f"Action: {_md(_remediation(diff))}",
                "",
            ]
            for side in ("expected", "actual"):
                references = diff["evidence"][side]
                lines.append(f"- {side.capitalize()} evidence lines: {_value(references)}.")
                for excerpt in diff["document_excerpts"][side]:
                    lines.append(f"  - Line {excerpt['line']}: {_md(excerpt['text'])}")
            lines.append("")
    provenance = report["provenance"]
    lines += [
        "",
        "## Reproducibility and limits",
        "",
        f"Timestamp (UTC): {_md(provenance['timestamp_utc'])}.",
        f"Code revision: {_value(provenance['code_revision'])}; "
        f"working tree dirty: {_value(provenance['working_tree_dirty'])}; "
        f"Python: {_md(provenance['python_version'])}.",
        f"Evaluation time: {_seconds(provenance['evaluation_seconds'])} seconds "
        f"({_md(provenance['timing_kind'])}); this is not model latency.",
        "",
    ]
    for key in ("dataset_sha256", "predictions_sha256", "policy_sha256"):
        lines.append(f"- {_md(key)}: {_md(provenance[key])}")
    lines += [
        "",
        "The JSON embeds validated inputs and any comparison baseline. Reports support "
        "reproduction; they are not signed evidence or secure attestations. Evidence "
        "line references aid inspection and do not prove semantic entailment. "
        "Policy thresholds are illustrative, not calibrated production guarantees.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def report_paths(
    output_dir: str | Path, name: str, *, input_paths: Iterable[str | Path] = ()
) -> tuple[Path, Path]:
    """Validate report destinations before any existing report is removed."""
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", name) is None:
        raise InputError("Report name must be 1-100 letters, digits, underscores or hyphens, "
                         "starting with a letter or digit; paths are not allowed")
    directory = Path(output_dir)
    paths = (directory / f"{name}.json", directory / f"{name}.md")
    protected = [Path(path) for path in input_paths]
    for path in paths:
        if path.is_symlink():
            raise InputError(f"Refusing a symlink report destination: {path}")
        if path.exists() and not path.is_file():
            raise InputError(f"Report destination is not a regular file: {path}")
        for source in protected:
            same = path.resolve() == source.resolve()
            if not same and path.exists() and source.exists():
                same = path.samefile(source)
            if same:
                raise InputError(f"Report destination would overwrite an input: {path}")
    return paths


def clear_reports(paths: Iterable[Path]) -> None:
    """Discard output names reserved by this invocation, including stale passes."""
    for path in paths:
        path.unlink(missing_ok=True)


def write_reports(
    report: dict, output_dir: str | Path, name: str, *,
    input_paths: Iterable[str | Path] = (),
) -> tuple[Path, Path]:
    """Publish strict JSON and Markdown, clearing either output if writing fails."""
    paths = report_paths(output_dir, name, input_paths=input_paths)
    temporary: list[Path] = []
    try:
        payloads = (
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
            render_report(report),
        )
        paths[0].parent.mkdir(parents=True, exist_ok=True)
        for path, payload in zip(paths, payloads, strict=True):
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent, prefix=f".{name}-",
                suffix=".tmp", delete=False,
            ) as handle:
                temporary.append(Path(handle.name))
                handle.write(payload)
        for path, temp in zip(paths, temporary, strict=True):
            os.replace(temp, path)
    except BaseException:
        # Also rolls back on KeyboardInterrupt between the two renames, which
        # would otherwise leave a published JSON with no Markdown beside it.
        clear_reports(paths)
        raise
    finally:
        for temp in temporary:
            temp.unlink(missing_ok=True)
    return paths
