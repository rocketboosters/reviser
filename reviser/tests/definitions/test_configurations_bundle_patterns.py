import pathlib
from unittest.mock import MagicMock

import reviser
from reviser.definitions import configurations

directory = pathlib.Path(reviser.__file__).parent

target = configurations.Target(
    directory=directory,
    data={},
    connection=MagicMock(),
    configuration=MagicMock(),
)


def test_bundle_file_matching():
    """Should select the correct files."""
    bundle = configurations.Bundle(
        directory=directory,
        data={
            "includes": ["commands", "definitions/aws.py", "**/__init__.py"],
            "excludes": ["**/__init__.py"],
        },
        connection=MagicMock(),
        target=target,
    )

    includes = bundle.get_include_paths()
    excludes = bundle.get_exclude_paths()
    paths = bundle.get_paths()

    assert all([p.is_file() or p.suffix == ".py" for p in paths])
    assert paths <= includes
    assert excludes == (excludes - paths)

    filenames = [p.name for p in paths]
    assert "__init__.py" not in filenames
    assert "aws.py" in filenames
    assert "selector.py" in filenames


def test_bundle_default_file_matching():
    """Should select the correct files by default."""
    bundle = configurations.Bundle(
        directory=directory.parent,
        data={},
        connection=MagicMock(),
        target=target,
    )

    paths = bundle.get_paths()
    assert directory.joinpath("__init__.py") in paths, """
        Expected the reviser package directory to be
        included by default.
        """


def test_bundle_excludes_venv_directories():
    """Should exclude .venv and venv directories by default."""
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = pathlib.Path(tmpdir)

        # Create a mock target for this test
        test_target = configurations.Target(
            directory=test_dir,
            data={},
            connection=MagicMock(),
            configuration=MagicMock(),
        )

        # Create .venv and venv directories with files
        venv_a = test_dir / ".venv"
        venv_a.mkdir()
        (venv_a / "lib").mkdir()
        (venv_a / "lib" / "python3.11").mkdir()
        (venv_a / "lib" / "python3.11" / "site-packages").mkdir()
        (venv_a / "lib" / "python3.11" / "site-packages" / "package.py").write_text(
            "# package"
        )

        venv_b = test_dir / "venv"
        venv_b.mkdir()
        (venv_b / "bin").mkdir()
        (venv_b / "bin" / "python").write_text("#!/usr/bin/env python")

        # Create a regular Python file that should be included
        (test_dir / "main.py").write_text("# main")
        (test_dir / "config.json").write_text("{}")

        bundle = configurations.Bundle(
            directory=test_dir,
            data={"includes": ["*.py", "*.json"]},
            connection=MagicMock(),
            target=test_target,
        )

        exclude_patterns = bundle.file_exclude_patterns
        paths = bundle.get_paths()

        # Verify .venv and venv are in the exclude patterns
        exclude_names = [p.name for p in exclude_patterns]
        assert ".venv" in exclude_names or any(
            ".venv" in str(p) for p in exclude_patterns
        )
        assert "venv" in exclude_names or any(
            "venv" in str(p) for p in exclude_patterns
        )

        # Verify .venv and venv files are not in the final paths
        path_strings = [str(p) for p in paths]
        assert not any(
            ".venv" in p for p in path_strings
        ), "Files in .venv should be excluded"
        assert not any(
            f"venv{os.sep}" in p for p in path_strings
        ), "Files in venv should be excluded"

        # Verify regular files are still included
        assert test_dir / "main.py" in paths
        assert test_dir / "config.json" in paths


def test_bundle_default_excludes_include_pycache_and_venv():
    """Should have default excludes for cache files and virtual environments."""
    bundle = configurations.Bundle(
        directory=directory,
        data={},
        connection=MagicMock(),
        target=target,
    )

    exclude_patterns = bundle.file_exclude_patterns
    exclude_strings = [str(p) for p in exclude_patterns]

    # Check for expected default exclusions
    assert any("__pycache__" in s for s in exclude_strings)
    assert any(".pyc" in s for s in exclude_strings)
    assert any(".DS_Store" in s for s in exclude_strings)
    assert any(".venv" in s for s in exclude_strings)
    assert any("venv" in s for s in exclude_strings)
