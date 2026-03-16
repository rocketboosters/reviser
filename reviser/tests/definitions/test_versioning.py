"""Unit tests for the get_package_version utility."""

import pathlib

from reviser.definitions.configurations import versioning


def test_pep621_version(tmp_path: pathlib.Path):
    """Should return the version from [project] (PEP 621)."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.2.3"\n', encoding="utf-8"
    )
    assert versioning.get_package_version(tmp_path) == "1.2.3"


def test_poetry_fallback_version(tmp_path: pathlib.Path):
    """Should return the version from [tool.poetry] when [project] is absent."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.poetry]\nversion = "2.0.0"\n', encoding="utf-8"
    )
    assert versioning.get_package_version(tmp_path) == "2.0.0"


def test_pep621_takes_priority_over_poetry(tmp_path: pathlib.Path):
    """Should prefer [project].version over [tool.poetry].version."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "3.0.0"\n\n[tool.poetry]\nversion = "2.0.0"\n',
        encoding="utf-8",
    )
    assert versioning.get_package_version(tmp_path) == "3.0.0"


def test_missing_pyproject_returns_default(tmp_path: pathlib.Path):
    """Should return '0.0.0' when pyproject.toml does not exist."""
    assert versioning.get_package_version(tmp_path) == "0.0.0"


def test_no_version_keys_returns_default(tmp_path: pathlib.Path):
    """Should return '0.0.0' when pyproject.toml has no version keys."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "--tb=short"\n', encoding="utf-8"
    )
    assert versioning.get_package_version(tmp_path) == "0.0.0"


def test_invalid_toml_returns_default(tmp_path: pathlib.Path):
    """Should return '0.0.0' without raising when pyproject.toml is malformed."""
    (tmp_path / "pyproject.toml").write_text(
        "NOT: valid::: TOML [[[\n", encoding="utf-8"
    )
    assert versioning.get_package_version(tmp_path) == "0.0.0"
