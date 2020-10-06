"""
Allows for selecting subsets of the targets within the loaded configuration.
The subsets are fuzzy-matched unless the --exact flag is used.
"""
import argparse
import typing

from lambda_deployer import bundling
from lambda_deployer import interactivity


def get_completions(
        completer: 'interactivity.ShellCompleter',
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return ['--reinstall']


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    parser.add_argument('--reinstall', action='store_true')


def run(ex: 'interactivity.Execution'):
    """Execute a bundle operation on the selected function/layer targets."""
    print('\n\n')
    bundling.create(
        context=ex.shell.context,
        selection=ex.shell.selection,
        reinstall=ex.args.get('reinstall', False),
    )
