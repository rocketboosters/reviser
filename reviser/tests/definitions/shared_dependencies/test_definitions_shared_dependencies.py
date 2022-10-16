import argparse
import pathlib
from unittest.mock import MagicMock

from reviser import definitions


def test_definitions_shared_dependencies():
    """Should load the configuration into a context."""
    directory = pathlib.Path(__file__).parent.resolve()
    connection = MagicMock(aws_account_id="123")
    context = definitions.Context.load_from_file(
        arguments=argparse.Namespace(),
        path=str(directory),
        connection=connection,
    )
    c = context.configuration
    assert len(c.targets) == 4
    assert "all" in c.shared_dependencies
    assert c.targets[0].dependencies == c.shared_dependencies["all"]
