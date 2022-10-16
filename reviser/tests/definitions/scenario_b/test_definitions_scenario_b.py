import argparse
import pathlib
from unittest.mock import MagicMock

from reviser import definitions


def test_scenario_b():
    """Should load the configuration into a context."""
    directory = pathlib.Path(__file__).parent.absolute()
    context = definitions.Context.load_from_file(
        arguments=argparse.Namespace(),
        path=str(directory),
        connection=MagicMock(),
    )
    c = context.configuration
    assert c.directory == directory
    assert c.bucket == "upload-bucket"
    assert len(c.targets) == 1

    target = c.layer_targets[0]
    assert target.kind.value == "layer"
    assert len(target.names) == 1
    deps = target.dependencies.sources[0]
    assert deps.kind.value == "pip"
    assert deps.packages == []
    assert deps.file is None
    deps = target.dependencies.sources[1]
    assert deps.kind.value == "pipper"
    assert deps.packages == []
    assert deps.file is None
