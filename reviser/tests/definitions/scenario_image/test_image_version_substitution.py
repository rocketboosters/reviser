"""Integration tests for PACKAGE_VERSION substitution in image URI."""

import pathlib
from unittest.mock import MagicMock

from reviser.definitions import configurations


def _make_image(directory: pathlib.Path, uri) -> configurations.Image:
    """Build a minimal Image object rooted at the given directory."""
    connection = MagicMock()
    configuration = configurations.Configuration(
        directory=directory,
        data={"targets": []},
        connection=connection,
    )
    target = configurations.Target(
        directory=directory,
        data={"kind": "function", "names": ["test-fn"], "image": {"uri": uri}},
        connection=connection,
        configuration=configuration,
    )
    return configurations.Image(
        directory=directory,
        data={"uri": uri},
        connection=connection,
        target=target,
    )


def test_version_substitution_pep621(tmp_path: pathlib.Path):
    """URI placeholder should be replaced with version from [project] (PEP 621)."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.2.3"\n', encoding="utf-8"
    )
    image = _make_image(
        tmp_path, "123.dkr.ecr.us-east-1.amazonaws.com/repo:{PACKAGE_VERSION}"
    )
    assert (
        image.get_region_uri("us-east-1")
        == "123.dkr.ecr.us-east-1.amazonaws.com/repo:1.2.3"
    )


def test_version_substitution_poetry(tmp_path: pathlib.Path):
    """URI placeholder should be replaced with version from [tool.poetry]."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.poetry]\nversion = "2.0.0"\n', encoding="utf-8"
    )
    image = _make_image(
        tmp_path, "123.dkr.ecr.us-east-1.amazonaws.com/repo:{PACKAGE_VERSION}"
    )
    assert (
        image.get_region_uri("us-east-1")
        == "123.dkr.ecr.us-east-1.amazonaws.com/repo:2.0.0"
    )


def test_version_substitution_no_pyproject(tmp_path: pathlib.Path):
    """URI placeholder should be replaced with '0.0.0' when pyproject.toml is absent."""
    image = _make_image(
        tmp_path, "123.dkr.ecr.us-east-1.amazonaws.com/repo:{PACKAGE_VERSION}"
    )
    assert (
        image.get_region_uri("us-east-1")
        == "123.dkr.ecr.us-east-1.amazonaws.com/repo:0.0.0"
    )


def test_version_substitution_missing_version_keys(tmp_path: pathlib.Path):
    """URI placeholder should be replaced with '0.0.0' when no version key exists."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "--tb=short"\n', encoding="utf-8"
    )
    image = _make_image(
        tmp_path, "123.dkr.ecr.us-east-1.amazonaws.com/repo:{PACKAGE_VERSION}"
    )
    assert (
        image.get_region_uri("us-east-1")
        == "123.dkr.ecr.us-east-1.amazonaws.com/repo:0.0.0"
    )


def test_version_substitution_no_placeholder(tmp_path: pathlib.Path):
    """URI without {PACKAGE_VERSION} should be returned unchanged."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "5.0.0"\n', encoding="utf-8"
    )
    uri = "123.dkr.ecr.us-east-1.amazonaws.com/repo:latest"
    image = _make_image(tmp_path, uri)
    assert image.get_region_uri("us-east-1") == uri


def test_version_substitution_region_dict(tmp_path: pathlib.Path):
    """Region-keyed URI dict should also have PACKAGE_VERSION substituted."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "3.1.4"\n', encoding="utf-8"
    )
    uri_map = {
        "us-east-1": "111.dkr.ecr.us-east-1.amazonaws.com/repo:{PACKAGE_VERSION}",
        "us-west-2": "222.dkr.ecr.us-west-2.amazonaws.com/repo:{PACKAGE_VERSION}",
    }
    image = _make_image(tmp_path, uri_map)
    assert (
        image.get_region_uri("us-east-1")
        == "111.dkr.ecr.us-east-1.amazonaws.com/repo:3.1.4"
    )
    assert (
        image.get_region_uri("us-west-2")
        == "222.dkr.ecr.us-west-2.amazonaws.com/repo:3.1.4"
    )


def test_custom_var_substitution(tmp_path: pathlib.Path):
    """Custom --var variables should be substituted into the URI."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.0.0"\n', encoding="utf-8"
    )
    image = _make_image(
        tmp_path,
        "123456.dkr.ecr.us-east-1.amazonaws.com/foo:bar-{ENV}-{PACKAGE_VERSION}",
    )
    result = image.get_region_uri("us-east-1", {"ENV": "test"})
    assert result == "123456.dkr.ecr.us-east-1.amazonaws.com/foo:bar-test-1.0.0"


def test_custom_var_overrides_package_version(tmp_path: pathlib.Path):
    """A custom --var=PACKAGE_VERSION value should override the auto-detected one."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.0.0"\n', encoding="utf-8"
    )
    image = _make_image(
        tmp_path,
        "123456.dkr.ecr.us-east-1.amazonaws.com/repo:{PACKAGE_VERSION}",
    )
    result = image.get_region_uri("us-east-1", {"PACKAGE_VERSION": "2.0.0"})
    assert result == "123456.dkr.ecr.us-east-1.amazonaws.com/repo:2.0.0"


def test_missing_var_raises_value_error(tmp_path: pathlib.Path):
    """A URI placeholder with no matching var should raise a descriptive ValueError."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.0.0"\n', encoding="utf-8"
    )
    image = _make_image(
        tmp_path,
        "123456.dkr.ecr.us-east-1.amazonaws.com/foo:{ENV}-{PACKAGE_VERSION}",
    )
    try:
        image.get_region_uri("us-east-1")
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "ENV" in str(error)
        assert "--var=ENV=<value>" in str(error)


def test_multiple_custom_vars(tmp_path: pathlib.Path):
    """Multiple custom vars should all be substituted."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "3.0.0"\n', encoding="utf-8"
    )
    image = _make_image(
        tmp_path,
        "123456.dkr.ecr.us-east-1.amazonaws.com/{REPO}:{ENV}-{PACKAGE_VERSION}",
    )
    result = image.get_region_uri("us-east-1", {"REPO": "myapp", "ENV": "prod"})
    assert result == "123456.dkr.ecr.us-east-1.amazonaws.com/myapp:prod-3.0.0"
