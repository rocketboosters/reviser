"""
Displays help information on the commands available within the
shell. Additional help on each command can be found using the
--help flag on the command in question.
"""
import argparse
import typing

from lambda_deployer import commands
from lambda_deployer import interactivity
from lambda_deployer import templating


def get_completions(
        completer: 'interactivity.ShellCompleter',
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return []


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    pass


def run(ex: 'interactivity.Execution') -> 'interactivity.Execution':
    """Displays basic command help for the available shell commands."""
    command_docs = {
        name: docs
        for name, command_module in commands.COMMANDS.items()
        if (docs := command_module.__doc__)
    }
    templating.printer(
        'commands/helper/help.jinja2',
        commands=list(sorted(command_docs.items(), key=lambda x: x[0])),
    )
    return ex.finalize(
        status='HELPED',
        message='Help displayed.'
    )
