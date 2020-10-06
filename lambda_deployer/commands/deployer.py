"""
Uploads the bundled contents to the upload S3 bucket and then publishes
a new version of each of the lambda targets with that new bundle and
any modified settings between the current configuration and that target's
existing configuration.
"""
import argparse
import typing

from lambda_deployer import deploying
from lambda_deployer import interactivity


def get_completions(
        completer: 'interactivity.ShellCompleter',
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return ['--description', '--dry-run']


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    parser.add_argument('--description')
    parser.add_argument('--dry-run', action='store_true')


def run(ex: 'interactivity.Execution'):
    """Execute a bundle operation on the selected function/layer targets."""
    print('\n\n')
    deploying.deploy(
        context=ex.shell.context,
        selection=ex.shell.selection,
        description=ex.args.get('description', ''),
        dry_run=ex.args.get('dry_run'),
    )
