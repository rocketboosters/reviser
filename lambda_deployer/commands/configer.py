"""
Displays the configs.
"""
import argparse
import typing

import yaml

from lambda_deployer import bundling
from lambda_deployer import interactivity


def get_completions(
        completer: 'interactivity.ShellCompleter',
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return []


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    pass


def run(ex: 'interactivity.Execution'):
    """Execute a bundle operation on the selected function/layer targets."""
    print('\n\n')
    print(yaml.safe_dump(ex.shell.context.configuration.serialize()))
