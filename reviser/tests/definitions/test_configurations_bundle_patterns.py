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
