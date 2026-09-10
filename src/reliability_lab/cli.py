"""Offline command-line evaluation with explicit quality and execution exits."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from .contracts import read_json
from .reporting import (
    clear_reports_only,
    quoted,
    render_report,
    report_paths,
    write_reports,
)
from .resources import resource_candidates, resource_path


def _demo_resources(scenario: str) -> list[Path]:
    """Locate every bundled demo input that can be located, for collision protection.

    Best-effort by design: one resource failing to resolve, for any reason, must not
    stop the others from being protected, because a failed lookup is not evidence the
    file is absent. The strict resolution in `main` still reports the real error.
    """
    protected: list[Path] = []
    for relative in ("data/evaluation.json", f"data/predictions/{scenario}.json",
                     "policy.json", "data/predictions/baseline.json"):
        try:
            protected.extend(resource_candidates(relative))
        except Exception:
            pass
        try:
            protected.append(resource_path(relative))
        except Exception:
            continue
    return protected


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


def _warn(message: str) -> None:
    """Emit a diagnostic. A diagnostic must never become the run's outcome."""
    try:
        if sys.stderr is not None:
            sys.stderr.write(f"{message}\n")
            sys.stderr.flush()
    except (OSError, UnicodeError, ValueError):
        pass


def _present(report: dict, json_path: Path, markdown_path: Path, status: int) -> int:
    """Display a published report. A display failure never unpublishes it."""
    if sys.stdout is None:
        # The process was started with the descriptor closed; there is nowhere to show it.
        return status
    text = (f"{render_report(report)}\n"
            f"JSON: {quoted(json_path.resolve())}\n"
            f"Markdown: {quoted(markdown_path.resolve())}\n")
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except (OSError, UnicodeError, ValueError) as exc:
        _warn(f"Warning: the report was published but could not be displayed: {quoted(exc)}")
    return status


def main(argv: Sequence[str] | None = None) -> int:
    """Return 0 for accepted quality, 1 for rejected quality, 2 for input/execution errors.

    Unusable arguments and `--help` are handled by argparse before any of that, so an
    in-process caller sees `SystemExit` there rather than a return value; the process
    exit status is still 2 for a bad argument and 0 for `--help`.
    """
    args = _parser().parse_args(argv)
    # Resolved from arguments alone so a failure while locating inputs can still
    # reserve, and clear, the output names this invocation would have written.
    # Taken verbatim, including an empty --name, which report_paths must reject.
    if args.command == "demo":
        name = args.scenario
    elif args.command == "evaluate":
        name = args.name
    else:
        name = "comparison"
    outputs: tuple[Path, Path] | None = None
    inputs: list[Path] = []
    try:
        if args.command == "demo":
            # Protect what exists before any strict lookup can abort the run.
            inputs = _demo_resources(name)
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
        # Same rule as the failure path: reserve the names, but do not remove a file
        # that is not recognisably a report. A successful run republishes over it.
        clear_reports_only(outputs)
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
                retained = clear_reports_only(outputs)
                if retained:
                    kept = ", ".join(quoted(path) for path in retained)
                    cleanup_note = (" These reserved outputs were left in place, because they "
                                    f"are not recognisable as reports written here: {kept}.")
            except Exception as cleanup_error:
                # Cleanup is best effort; a failure here reports itself but must
                # never replace the execution error that is the run's real result.
                cleanup_note = f" Could not remove old outputs: {quoted(cleanup_error)}."
        _warn(f"Error: {quoted(exc)}\nNo fresh report was produced.{cleanup_note}")
        return 2
    # Publication is complete and irreversible from here; only display can still fail.
    return _present(report, json_path, markdown_path, status)


def _detach(descriptor: int) -> None:
    """Point a descriptor at the null device so a pending flush can complete.

    `os.open` hands back the lowest free descriptor, which is the one just closed
    when a caller did `1>&-`; closing that as a stray would undo the repair.
    """
    try:
        sink = os.open(os.devnull, os.O_WRONLY)
    except OSError:
        return
    try:
        if sink != descriptor:
            os.dup2(sink, descriptor)
    except OSError:
        pass
    finally:
        if sink != descriptor:
            try:
                os.close(sink)
            except OSError:
                pass


def run(argv: Sequence[str] | None = None) -> int:
    """Console-script entry point: `main`, plus the stream care only a process may take.

    A reader that hung up makes the interpreter's exit-time flush raise, which would
    replace the verdict with status 120. Detaching a descriptor is a process-wide act,
    so it belongs here and never inside the importable `main`.
    """
    try:
        return main(argv)
    finally:
        # Also runs when argparse exits: `--help` and an unusable argument have their
        # own statuses, and a hung-up reader must not turn either into 120 either.
        for stream, descriptor in ((sys.stdout, 1), (sys.stderr, 2)):
            if stream is None:
                continue
            try:
                stream.flush()
            except (OSError, ValueError):
                _detach(descriptor)
                try:
                    stream.flush()
                except (OSError, ValueError):
                    pass


if __name__ == "__main__":
    raise SystemExit(run())
