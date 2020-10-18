import argparse
import pathlib
import typing
from unittest.mock import MagicMock

from prompt_toolkit.document import Document
from pytest import mark

from reviser import commands
from reviser import definitions
from reviser import interactivity


@mark.parametrize('command_module', commands.COMMANDS.values())
def test_completions_works(command_module):
    """Should get completions without error."""
    completer = interactivity.ShellCompleter(MagicMock())
    assert command_module.get_completions(completer) is not None


SCENARIOS = {
    'bun': {'bundle'},
    'deploy --desc': {'--description'},
    'select * foo-': {'foo-function', 'foo-layer'},
}


@mark.parametrize('text, expected', SCENARIOS.items())
def test_completion(text: str, expected: typing.List[str]):
    """Should return the expected completions."""
    path = (
        pathlib.Path(__file__)
        .parent.parent
        .joinpath('scenarios/complex/lambda.yaml')
    )
    context = definitions.Context.load_from_file(
        arguments=argparse.Namespace(),
        path=str(path),
        connection=MagicMock(),
    )
    completer = interactivity.ShellCompleter(MagicMock(context=context))
    document = Document(text=text)
    observed = {
        c.text
        for c in completer.get_completions(document, MagicMock())
    }
    assert observed == expected
