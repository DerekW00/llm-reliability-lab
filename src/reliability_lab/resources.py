"""Locate bundled inputs in editable installs and ordinary wheel installations."""

from importlib.resources import files
from pathlib import Path

from .contracts import InputError


def resource_candidates(relative: str) -> list[Path]:
    """Both locations resource_path considers, whether or not a file is at either.

    A caller protecting a bundled input cannot depend on a successful lookup: a
    failed lookup means the file was not found, not that no file is at stake.
    """
    part = Path(relative)
    if part.is_absolute() or ".." in part.parts:
        raise InputError("Resource path must remain within bundled resources")
    # Wheels are installed unpacked. Hatch's editable install points at source.
    return [Path(str(files("reliability_lab"))) / "resources" / part,
            Path(__file__).resolve().parents[2] / part]


def resource_path(relative: str) -> Path:
    bundled, editable = resource_candidates(relative)
    if bundled.is_file():
        return bundled
    source_root = Path(__file__).resolve().parents[2]
    if (source_root / "pyproject.toml").is_file() and editable.is_file():
        return editable
    raise InputError(f"Missing bundled resource: {relative}")
