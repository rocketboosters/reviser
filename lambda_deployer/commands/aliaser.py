"""
Creates and assigns an alias to the specified version of the selected or
specified lambda function, or reassigns an existing alias to a different
version.
"""
import typing
from argparse import ArgumentParser

from lambda_deployer import interactivity


def get_completions(
        completer: 'interactivity.ShellCompleter',
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return ['--function', '--yes', '--create']


def populate_subparser(parser: ArgumentParser):
    """Add alias subcommand to supplied parser"""
    parser.add_argument('alias')
    parser.add_argument('version')
    parser.add_argument('--function')
    parser.add_argument('--yes', action='store_true')
    parser.add_argument('--create', action='store_true')


def run(ex: 'interactivity.Execution') -> 'interactivity.Execution':
    """Execute the command invocation."""
    selected = ex.shell.context.get_selected_targets(ex.shell.selection)
    is_ambiguous = not ex.args.get('function') and (
        0 < len(selected.targets) > 1
        or len(selected.targets[0].names) > 1
    )
    if is_ambiguous:
        return ex.finalize(
            status='ERROR',
            message="""
                Ambiguous alias assignment. Only one function can be assigned
                at a time. Either modify the selection or use the --function
                flag to specify the target function for the alias change.
                """,
            echo=True,
        )

    name = ex.args.get('function') or selected.targets[0].names[0]
    client = ex.shell.context.connection.session.client('lambda')
    alias = ex.args.get('alias')
    version = ex.args.get('version')
    create = ex.args.get('create')
    yes = ex.args.get('yes')

    request = dict(
        FunctionName=name,
        Name=alias,
        FunctionVersion=version,
    )

    prefix = f'Create {alias} at' if create else f'Move {alias} to'
    message = f'\n{prefix} {name}:{version} [y/N]? '
    if not yes and not (input(message) or '').strip().lower().startswith('y'):
        return ex.finalize(
            status='ABORTED',
            message='No alias changes made.',
            echo=True,
        )

    if create:
        client.create_alias(**request)
    else:
        client.update_alias(**request)

    return ex.finalize(
        status='SUCCESS',
        message='Alias change has been applied.',
        info={'function': name, 'alias': alias, 'version': version},
        echo=True,
    )
