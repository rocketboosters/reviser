"""
Uploads the bundled contents to the upload S3 bucket and then publishes
a new version of each of the lambda targets with that new bundle and
any modified settings between the current configuration and that target's
existing configuration.
"""
import argparse
import os
import string
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
    description = (
        string.Template(ex.args.get('description') or '')
        .substitute(os.environ)
    )
    print('\n\n')
    deployed_targets = deploying.deploy(
        context=ex.shell.context,
        selection=ex.shell.selection,
        description=description,
        dry_run=ex.args.get('dry_run'),
    )
    print('\n')
    return ex.finalize(
        status='DEPLOYED',
        message='Selected items have been deployed.',
        info={
            'dry_run': ex.args.get('dry_run'),
            'items': [n for t in deployed_targets for n in t.names],
            'description': description,
        },
        echo=True,
    )
