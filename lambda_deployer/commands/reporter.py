"""
Shows the current status information for each of the selected lambda targets.
"""
import argparse
import textwrap
import typing

import yaml
from botocore.client import BaseClient

from lambda_deployer import interactivity
from lambda_deployer import servicer


def get_completions(
        completer: 'interactivity.ShellCompleter',
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return []


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for the status command."""
    parser.add_argument('qualifier', nargs='?')


def _get_layer_version_info(
        client: BaseClient,
        layer_arn: str,
) -> dict:
    """Fetches layer information for display."""
    versions = servicer.get_layer_versions(client, layer_arn)
    current = next((v for v in versions if v.arn == layer_arn))
    latest = versions[-1]

    out = {
        'name': current.name,
        'version': current.version,
        'created': current.created.isoformat('T'),
        'runtimes': ', '.join(current.runtimes),
    }

    if latest != current:
        out['status'] = f'Newer version {latest.version} exists.'
    else:
        out['status'] = 'Is latest version.'

    return out


def _display_function_info(
        client: BaseClient,
        name: str,
        qualifier: str,
):
    """Displays the response lambda function information."""
    lambda_function = servicer.get_function_version(
        lambda_client=client,
        function_name=name,
        qualifier=qualifier,
    )
    data = {
        'modified': lambda_function.modified,
        'description': lambda_function.description,
        'arn': lambda_function.arn,
        'runtime': lambda_function.runtime,
        'role': lambda_function.role,
        'handler': lambda_function.handler,
        'size': lambda_function.size,
        'timeout': lambda_function.timeout,
        'memory': lambda_function.memory,
        'version': lambda_function.version,
        'environment': lambda_function.environment,
        'revision_id': lambda_function.revision_id,
        'layers': [
            {
                **_get_layer_version_info(client, item.arn),
                'size': item.size,
            }
            for item in lambda_function.layers
        ],
        'status': lambda_function.status.to_dict(),
        'update_status': lambda_function.status.to_dict(),
    }
    print(f'\n--- {lambda_function.name}:{qualifier} ---')
    print(textwrap.indent(yaml.safe_dump(data), prefix='  '))
    print('\n')


def _display_layer_info(
        client: BaseClient,
        name: str,
        qualifier: str,
):
    """Display layer version information."""
    try:
        version = int(qualifier)
    except (ValueError, TypeError):
        version = None

    if version is None:
        version = servicer.get_layer_versions(client, name)[-1].version

    layer = servicer.get_layer_version(
        lambda_client=client,
        layer_name=name,
        version=version,
    )

    print(f'\n--- {layer.name}:{qualifier} ---')
    data = {
        'arn': layer.arn,
        'version': layer.version,
        'created': layer.created.isoformat(),
        'description': layer.description,
        'size': layer.size,
        'runtimes': ', '.join(layer.runtimes),
    }
    print(textwrap.indent(yaml.safe_dump(data), prefix='  '))


def run(ex: 'interactivity.Execution') -> 'interactivity.Execution':
    """Displays the current configuration of the lambda target(s)."""
    selected = ex.shell.context.get_selected_targets(ex.shell.selection)
    qualifier = ex.args.get('qualifier')
    client = ex.shell.context.connection.session.client('lambda')

    items = [(t, n) for t in selected.function_targets for n in t.names]
    for target, name in items:
        _display_function_info(client, name, qualifier)

    items = [(t, n) for t in selected.layer_targets for n in t.names]
    for target, name in items:
        _display_layer_info(client, name, qualifier)

    return ex.finalize(
        status='SUCCESS',
        message='Status reports have been display.',
        echo=False,
    )
