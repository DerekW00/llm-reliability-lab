"""Locate bundled inputs in editable installs and ordinary wheel installations."""

from importlib.resources import files
from pathlib import Path

from .contracts import InputError


def resource_path(relative: str) -> Path:
    part = Path(relative)
    if part.is_absolute() or ".." in part.parts:
        raise InputError("Resource path must remain within bundled resources")
    # Wheels are installed unpacked. Hatch's editable install points at source.
    bundled = Path(str(files("reliability_lab"))) / "resources" / part
    if bundled.is_file():
        return bundled
    source_root = Path(__file__).resolve().parents[2]
    editable = source_root / part
    if (source_root / "pyproject.toml").is_file() and editable.is_file():
        return editable
    raise InputError(f"Missing bundled resource: {relative}")
