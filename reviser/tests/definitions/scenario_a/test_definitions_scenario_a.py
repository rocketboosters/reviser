import argparse
import pathlib
from unittest.mock import MagicMock

from reviser import definitions


def test_scenario_a():
    """Should load the configuration into a context."""
    directory = pathlib.Path(__file__).parent.absolute()
    connection = MagicMock(aws_account_id='123')
    context = definitions.Context.load_from_file(
        arguments=argparse.Namespace(),
        path=str(directory),
        connection=connection,
    )
    c = context.configuration
    assert c.directory == directory
    assert c.bucket == 'bucket-123'
    assert len(c.targets) == 2

    target = c.function_targets[0]
    assert target.kind.value == 'function'
    assert len(target.names) == 2
    assert target.bundle.omitted_packages == ['ham']
    assert len(target.dependencies) == 1
    deps = target.dependencies[0]
    assert deps.kind.value == 'pip'
    assert deps.packages == ['spam']
    assert deps.file is None

    target = c.layer_targets[0]
    assert target.kind.value == 'layer'
    assert len(target.names) == 1
    assert target.bundle.omitted_packages == []
    assert len(target.dependencies) == 2
    deps = target.dependencies[0]
    assert deps.kind.value == 'pip'
    assert deps.packages == []
    assert deps.file == directory.joinpath('requirements.txt')
    deps = target.dependencies[1]
    assert deps.kind.value == 'pipper'
    assert deps.packages == []
    assert deps.file == directory.joinpath('pipper.json')
