"""
Lists versions of the specified lambda targets with
info about each version.
"""
import typing
from argparse import ArgumentParser

from lambda_deployer import interactivity
from lambda_deployer import servicer


def get_completions(
        completer: 'interactivity.ShellCompleter',
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return []


def populate_subparser(parser: ArgumentParser):
    """Configure the command arguments for this command."""
    pass


def run(ex: 'interactivity.Execution') -> 'interactivity.Execution':
    """Execute the listing command."""
    selected = ex.shell.context.get_selected_targets(ex.shell.selection)
    client = ex.shell.context.connection.session.client('lambda')

    function_names = [
        name
        for target in selected.function_targets
        for name in target.names
    ]
    servicer.echo_function_versions(client, function_names)

    if not selected.layer_targets:
        return ex.finalize(
            status='LISTED',
            message='Functions have been listed.',
            echo=True,
        )

    layer_names = [
        name
        for target in selected.layer_targets
        for name in target.names
    ]
    servicer.echo_layer_versions(client, layer_names, function_names)

    return ex.finalize(
        status='LISTED',
        message='Items have been listed.',
        echo=False,
    )
