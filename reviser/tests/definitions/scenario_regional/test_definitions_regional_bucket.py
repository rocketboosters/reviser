import argparse
import pathlib
from unittest.mock import MagicMock

from reviser import definitions


def test_scenario_regional():
    """Should load the configuration into a context."""
    connection = MagicMock()
    connection.session.region_name = None

    directory = pathlib.Path(__file__).parent.absolute()
    context = definitions.Context.load_from_file(
        arguments=argparse.Namespace(),
        path=str(directory),
        connection=connection,
    )
    c = context.configuration

    assert c.aws_region == "us-east-1", "Expect defaulted region."
    assert c.bucket == "upload-bucket-us-east-1"

    c.data["region"] = "us-west-2"
    assert c.aws_region == "us-west-2", "Expect region to be overridden."
    assert c.bucket == "upload-bucket-us-west-2"
