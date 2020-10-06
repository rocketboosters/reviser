"""
Creates and assigns an alias to the specified version of the selected or
specified lambda function, or reassigns an existing alias to a different
version.
"""
from argparse import ArgumentParser

from lambda_deployer import interactivity
from lambda_deployer import servicer
import typing

def get_completions(
        completer: 'interactivity.ShellCompleter',
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return ['--function', '--yes']


def populate_subparser(parser: ArgumentParser):
    """Add alias subcommand to supplied parser"""
    parser.add_argument('alias')
    parser.add_argument('version')
    parser.add_argument('--function')
    parser.add_argument('--yes')


def run(ex: 'interactivity.Execution'):
    """Execute the command invocation."""
    name = ex.args.get('function')
    selected = ex.shell.context.get_selected_targets(ex.shell.selection)
    is_ambiguous = not name and (
        0 < len(selected.targets) > 1
        or len(selected.targets[0].names) > 0
    )
    if is_ambiguous:
        raise ValueError('Cannot assign with multiple function names.')

    client = ex.shell.context.connection.session.client('lambda')
    versions = servicer.get_function_versions(client, name)
    aliases = [a.name for v in versions for a in v.aliases]

    alias = ex.args.get('alias')
    version = ex.args.get('version')

    if alias in aliases:
        message = f'\nAssign {alias} to {name}:{version} [y/N]? '
    else:
        message = f'\nCreate {alias} pointing to {name}:{version} [y/N]? '

    if ex.args.get('yes') or input(message).strip().lower().startswith('y'):
        servicer.assign_alias(client, name, alias, version)
    else:
        print(f'[ABORTED]: {alias} assignment')
