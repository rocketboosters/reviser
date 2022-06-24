import argparse
import pathlib
from unittest.mock import MagicMock

from reviser import definitions


def test_scenario():
    """Should load the configuration into a context."""
    directory = pathlib.Path(__file__).parent.absolute()
    connection = MagicMock(aws_account_id="123")
    context = definitions.Context.load_from_file(
        arguments=argparse.Namespace(),
        path=str(directory),
        connection=connection,
    )
    c = context.configuration
    assert c.directory == directory
    assert len(c.targets) == 1

    target = c.function_targets[0]
    assert target.kind.value == "function"
    assert len(target.names) == 1
    assert target.image.uri == "123456789012.dkr.ecr.us-west-2.amazonaws.com/repo:tag"
    assert target.image.entrypoint == ["/my/entrypoint"]
    assert target.image.cmd == ["params", "to", "entrypoint"]
    assert target.image.workingdir == "/the/working/dir"
