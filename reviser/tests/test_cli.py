import fnmatch
import pathlib
from unittest.mock import MagicMock
from unittest.mock import patch

from reviser import cli


@patch("subprocess.check_call")
def test_cli(subprocess_check_call: MagicMock):
    """Should execute the cli command with the expected arguments."""
    path = str(pathlib.Path("/foo/bar").absolute()).replace("\\", "/")
    assert cli.main(["-d", path, "--tag-version=10.11.12"])

    command = subprocess_check_call.call_args.args[0]
    assert f"{path}:/project/bar" in command
    assert "-d" not in command
    assert "/foo/bar" not in command
    assert any(
        [fnmatch.fnmatch(item, "swernst/reviser:10.11.12-*") for item in command]
    )
