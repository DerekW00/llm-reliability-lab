"""Regression cases from the final independent review of the repair commits."""

import copy
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

import reliability_lab
from reliability_lab import cli, reporting, resources
from reliability_lab.contracts import InputError, read_json
from reliability_lab.evaluation import evaluate

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def report():
    return evaluate(read_json(ROOT / "data/evaluation.json"),
                    read_json(ROOT / "data/predictions/baseline.json"),
                    read_json(ROOT / "policy.json"))


def offline_checker():
    spec = importlib.util.spec_from_file_location("closure_offline", ROOT / "scripts/verify_offline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("failed_child", [1, 3], ids=["regression", "compare"])
def test_each_rejecting_child_must_report_its_own_import(monkeypatch, failed_child):
    checker = offline_checker()
    calls = []

    def child(args, **options):
        index = len(calls)
        calls.append(args)
        if index == failed_child:
            # Same exit status as a quality rejection, but no CLI import happened.
            return subprocess.CompletedProcess(args, 1, "", "child died before import")
        Path(options["env"]["OFFLINE_IMPORT_ORIGIN"]).write_text(reliability_lab.__file__)
        command = args[3:]
        if command[0] == "demo":
            out = Path(command[command.index("--output-dir") + 1])
            out.mkdir(exist_ok=True)
            scenario = command[command.index("--scenario") + 1]
            (out / f"{scenario}.json").write_text(json.dumps({
                "mode": "synthetic_fixture", "provenance": {"live_calls": False, "model": None},
            }))
        return subprocess.CompletedProcess(args, 1 if index in (1, 3) else 0, "", "")

    monkeypatch.setattr(checker.subprocess, "run", child)
    with pytest.raises(checker.CheckFailed, match="never reported"):
        checker.main()
    assert len(calls) == failed_child + 1


def test_missing_produced_report_is_an_explicit_verification_failure(monkeypatch):
    checker = offline_checker()
    calls = []

    def child(args, **options):
        index = len(calls)
        calls.append(args)
        Path(options["env"]["OFFLINE_IMPORT_ORIGIN"]).write_text(reliability_lab.__file__)
        return subprocess.CompletedProcess(args, 1 if index in (1, 3) else 0, "", "")

    monkeypatch.setattr(checker.subprocess, "run", child)
    with pytest.raises(checker.CheckFailed, match="baseline: no readable JSON report"):
        checker.main()


@pytest.mark.parametrize("failure", ["serialization", "first_replace", "second_replace"])
def test_publication_failure_preserves_outputs_it_never_replaced(tmp_path, monkeypatch, report, failure):
    originals = {"evaluation.json": '{"my":"notes"}\n', "evaluation.md": "My unrelated notes.\n"}
    for name, text in originals.items():
        (tmp_path / name).write_text(text)
    if failure == "serialization":
        report["summary"]["micro"]["f1"] = float("nan")
        error = ValueError
    else:
        real_replace, calls = reporting.os.replace, []

        def replace(source, destination):
            calls.append(destination)
            if len(calls) == (1 if failure == "first_replace" else 2):
                raise OSError("injected publication failure")
            real_replace(source, destination)

        monkeypatch.setattr(reporting.os, "replace", replace)
        error = OSError
    with pytest.raises(error):
        reporting.write_reports(report, tmp_path, "evaluation")
    retained = {"evaluation.md"} if failure == "second_replace" else set(originals)
    assert {path.name for path in tmp_path.iterdir()} == retained
    for name in retained:
        assert (tmp_path / name).read_text() == originals[name]


def test_successful_publication_replaces_the_named_outputs(tmp_path, report):
    for suffix in ("json", "md"):
        (tmp_path / f"evaluation.{suffix}").write_text("Unrelated old content")
    reporting.write_reports(report, tmp_path, "evaluation")
    assert json.loads((tmp_path / "evaluation.json").read_text()) == report
    assert (tmp_path / "evaluation.md").read_text() == reporting.render_report(report)


@pytest.mark.parametrize("version,live_calls,retained", [(1, False, False), (2, False, True),
                                                       (1, True, True)])
def test_failure_cleanup_requires_both_report_markers(tmp_path, report, version, live_calls, retained):
    report["report_version"] = version
    report["provenance"]["live_calls"] = live_calls
    target = tmp_path / "evaluation.json"
    content = json.dumps(report)
    target.write_text(content)
    missing = str(tmp_path / "missing.json")
    assert cli.main(["evaluate", "--dataset", missing, "--predictions", missing,
                     "--policy", missing, "--output-dir", str(tmp_path)]) == 2
    assert target.exists() is retained
    if retained:
        assert target.read_text() == content


@pytest.mark.parametrize("field", ["dataset_id", "scenario"])
def test_supplied_report_metadata_stays_distinguishable(field):
    dataset = read_json(ROOT / "data/evaluation.json")
    supplied = read_json(ROOT / "data/predictions/baseline.json")
    policy = read_json(ROOT / "policy.json")
    headers = []
    for value in ("run-\x1b[31m", r"run-\x1b[31m"):
        data, predictions = copy.deepcopy(dataset), copy.deepcopy(supplied)
        predictions[field] = value
        if field == "dataset_id":
            data[field] = value
        rendered = reporting.render_report(evaluate(data, predictions, policy))
        headers.append(next(line for line in rendered.splitlines() if line.startswith("Dataset:")))
        assert "\x1b" not in rendered
    assert headers[0] != headers[1]


@pytest.mark.parametrize("layout", ["wheel", "editable", "both", "missing_marker"])
def test_resource_resolution_uses_the_correct_installation_layout(tmp_path, monkeypatch, layout):
    installed = tmp_path / "installed/reliability_lab"
    source = tmp_path / "source"
    bundled = installed / "resources/policy.json"
    editable = source / "policy.json"
    monkeypatch.setattr(resources, "files", lambda package: installed)
    monkeypatch.setattr(resources, "__file__", str(source / "src/reliability_lab/resources.py"))
    if layout in ("wheel", "both"):
        bundled.parent.mkdir(parents=True)
        bundled.write_text("packaged policy")
    if layout in ("editable", "both", "missing_marker"):
        source.mkdir(parents=True)
        editable.write_text("editable policy")
        if layout != "missing_marker":
            (source / "pyproject.toml").write_text("[project]\n")
    if layout == "missing_marker":
        with pytest.raises(InputError, match="Missing bundled resource"):
            resources.resource_path("policy.json")
    else:
        expected = editable if layout == "editable" else bundled
        assert resources.resource_path("policy.json") == expected


@pytest.mark.parametrize("absolute", [False, True])
def test_existing_files_outside_resources_cannot_be_selected(tmp_path, monkeypatch, absolute):
    installed = tmp_path / "installed"
    (installed / "resources").mkdir(parents=True)
    outside = installed / "outside.json"
    outside.write_text("synthetic unrelated file")
    monkeypatch.setattr(resources, "files", lambda package: installed)
    relative = str(outside) if absolute else "../outside.json"
    with pytest.raises(InputError, match="remain within bundled resources"):
        resources.resource_path(relative)
