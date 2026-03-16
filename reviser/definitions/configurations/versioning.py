"""Package version resolution from pyproject.toml for image URI substitution."""

import pathlib
import tomllib
import typing


def get_package_version(directory: pathlib.Path) -> str:
    """
    Read the package version from pyproject.toml in the given directory.

    Supports PEP 621 (`project.version`) with a fallback to Poetry
    (`tool.poetry.version`). Returns ``"0.0.0"`` without raising an error
    if the file is absent, the relevant keys are missing, or any other
    problem is encountered while parsing.
    """
    try:
        pyproject = directory / "pyproject.toml"
        if not pyproject.is_file():
            return "0.0.0"
        data: typing.Dict[str, typing.Any] = tomllib.loads(pyproject.read_text())
        # PEP 621 takes priority.
        pep621_version = data.get("project", {}).get("version")
        if pep621_version is not None:
            return str(pep621_version)
        # Fall back to Poetry.
        poetry_version = data.get("tool", {}).get("poetry", {}).get("version")
        if poetry_version is not None:
            return str(poetry_version)
        return "0.0.0"
    except Exception:
        return "0.0.0"
