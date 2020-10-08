"""
Allows for selecting subsets of the targets within the loaded configuration.
The subsets are fuzzy-matched unless the --exact flag is used.
"""
import argparse
import typing

from lambda_deployer import interactivity
from ..commands import bundler
from ..commands import deployer


def get_completions(
        completer: 'interactivity.ShellCompleter',
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return (
        bundler.get_completions(completer)
        + deployer.get_completions(completer)
    )


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    bundler.populate_subparser(parser)
    deployer.populate_subparser(parser)


def run(ex: 'interactivity.Execution') -> 'interactivity.Execution':
    """Execute a bundle operation on the selected function/layer targets."""
    out = bundler.run(ex)
    if out.result.status != 'BUNDLED':
        return out
    return deployer.run(ex)
