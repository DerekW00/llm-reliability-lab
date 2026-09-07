"""Offline command-line evaluation with explicit quality and execution exits."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from .contracts import read_json
from .reporting import clear_reports, render_report, report_paths, safe_text, write_reports
from .resources import resource_path


def _evaluate(*args: object, **kwargs: object) -> dict:
    from .evaluation import evaluate

    return evaluate(*args, **kwargs)


def _compare(baseline: dict, candidate: dict) -> dict:
    from .gate import compare_reports

    return compare_reports(baseline, candidate)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reliability-lab",
        description="Offline invoice extraction evaluation. Bundled demos use synthetic "
        "fixtures, not live models. Exit codes: 0 accepted, 1 quality rejection, 2 error.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Evaluate bundled synthetic fixture predictions")
    demo.add_argument("--scenario", required=True, choices=("baseline", "regression", "repaired"))
    demo.add_argument("--output-dir", type=Path, default=Path("reports"))
    evaluate = commands.add_parser("evaluate", help="Evaluate complete user-supplied JSON inputs")
    for name, description in (
        ("dataset", "Dataset JSON: every case with its document, labels and evidence"),
        ("predictions", "Predictions JSON: exactly one record per dataset case"),
        ("policy", "Policy JSON: the thresholds this evaluation is judged against"),
    ):
        evaluate.add_argument(f"--{name}", required=True, type=Path, help=description)
    evaluate.add_argument("--baseline", type=Path,
                          help="A previously written evaluation REPORT JSON to compare against, "
                               "such as reports/baseline.json; not a predictions file")
    evaluate.add_argument("--output-dir", type=Path, default=Path("reports"),
                          help="Directory for the written report pair (default: reports)")
    evaluate.add_argument("--name", default="evaluation", help="Safe filename stem (no paths)")
    compare = commands.add_parser("compare", help="Recompute and compare two report artifacts")
    compare.add_argument("baseline_report", type=Path,
                         help="An accepted evaluation REPORT JSON, not a predictions file")
    compare.add_argument("candidate_report", type=Path,
                         help="The candidate evaluation REPORT JSON to judge against it")
    compare.add_argument("--output-dir", type=Path, default=Path("reports"),
                         help="Directory for the written comparison pair (default: reports)")
    return parser


def _discard_stdout() -> None:
    """Stop the interpreter's exit-time flush from retrying a failed stdout write."""
    try:
        with open(os.devnull, "w") as sink:
            os.dup2(sink.fileno(), sys.stdout.fileno())
    except (OSError, ValueError):
        pass


def _present(report: dict, json_path: Path, markdown_path: Path, status: int) -> int:
    """Display a published report. A display failure never unpublishes it."""
    text = (f"{render_report(report)}\n"
            f"JSON: {safe_text(json_path.resolve())}\n"
            f"Markdown: {safe_text(markdown_path.resolve())}\n")
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except (OSError, UnicodeError, ValueError) as exc:
        _discard_stdout()
        print(f"Warning: the report was published but could not be displayed: {safe_text(exc)}",
              file=sys.stderr)
    return status


def main(argv: Sequence[str] | None = None) -> int:
    """Return 0 for accepted quality, 1 for rejected quality, 2 for input/execution errors."""
    args = _parser().parse_args(argv)
    # Resolved from arguments alone so a failure while locating inputs can still
    # reserve, and clear, the output names this invocation would have written.
    name = {"demo": getattr(args, "scenario", None),
            "evaluate": getattr(args, "name", None)}.get(args.command) or "comparison"
    outputs: tuple[Path, Path] | None = None
    inputs: list[Path] = []
    try:
        if args.command == "demo":
            dataset_path = resource_path("data/evaluation.json")
            predictions_path = resource_path(f"data/predictions/{name}.json")
            policy_path = resource_path("policy.json")
            baseline_path = resource_path("data/predictions/baseline.json")
            inputs = [dataset_path, predictions_path, policy_path, baseline_path]
        elif args.command == "evaluate":
            dataset_path, predictions_path, policy_path = args.dataset, args.predictions, args.policy
            inputs = [dataset_path, predictions_path, policy_path]
            if args.baseline is not None:
                inputs.append(args.baseline)
        else:
            inputs = [args.baseline_report, args.candidate_report]

        outputs = report_paths(args.output_dir, name, input_paths=inputs)
        clear_reports(outputs)
        if args.command == "compare":
            report = _compare(read_json(args.baseline_report), read_json(args.candidate_report))
        else:
            dataset = read_json(dataset_path)
            predictions = read_json(predictions_path)
            policy = read_json(policy_path)
            if args.command == "demo" and name != "baseline":
                baseline = _evaluate(dataset, read_json(baseline_path), policy)
                report = _evaluate(dataset, predictions, policy, baseline=baseline)
            elif args.command == "evaluate" and args.baseline is not None:
                report = _evaluate(dataset, predictions, policy, baseline=read_json(args.baseline))
            else:
                report = _evaluate(dataset, predictions, policy)
        json_path, markdown_path = write_reports(report, args.output_dir, name, input_paths=inputs)
        status = 0 if report["gate"]["accepted"] else 1
    except Exception as exc:
        # Keep errors at the command boundary concise. Invalid inputs never become scores.
        if outputs is None:
            # The failure preceded the reservation; reserve now so an earlier
            # acceptance cannot be mistaken for this failed run's result.
            try:
                outputs = report_paths(args.output_dir, name, input_paths=inputs)
            except Exception:
                outputs = None
        cleanup_note = ""
        if outputs is not None:
            try:
                clear_reports(outputs)
            except OSError as cleanup_error:
                cleanup_note = f" Could not remove old outputs: {safe_text(cleanup_error)}."
        print(f"Error: {safe_text(exc)}\nNo fresh report was produced.{cleanup_note}", file=sys.stderr)
        return 2
    # Publication is complete and irreversible from here; only display can still fail.
    return _present(report, json_path, markdown_path, status)


if __name__ == "__main__":
    raise SystemExit(main())
