"""
Allows for selecting subsets of the targets within the loaded configuration.
The subsets are fuzzy-matched unless the --exact flag is used.
"""
import argparse
import dataclasses
import typing

from lambda_deployer import definitions
from lambda_deployer import interactivity


def get_completions(
        completer: 'interactivity.ShellCompleter',
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return ['*', 'function', 'layer', '--exact']


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for the select command."""
    parser.add_argument('kind', choices=[
        definitions.TargetType.FUNCTION.value,
        definitions.TargetType.LAYER.value,
        '*',
    ])
    parser.add_argument('name', nargs='?')
    parser.add_argument(
        '--exact',
        action='store_true',
        help='Forces the match to be exact instead of fuzzy.'
    )


def _update_exact_selection(
        kind: str,
        names: typing.List[str],
        selection: 'definitions.Selection',
) -> 'definitions.Selection':
    """Create a new selection object updated with the specified exact match."""
    layer_names = []
    if kind in ('*', 'layer'):
        layer_names = list(names)

    function_names = []
    if kind in ('*', 'function'):
        function_names = list(names)

    return dataclasses.replace(
        selection,
        layer_names=layer_names,
        layer_needles=[],
        function_names=function_names,
        function_needles=[],
        bundle_all=False,
    )


def _update_fuzzy_selection(
        kind: str,
        names: typing.List[str],
        selection: 'definitions.Selection',
) -> 'definitions.Selection':
    """Create a new selection object updated with the specified fuzzy match."""
    layer_needles = []
    if kind in ('*', 'layer'):
        layer_needles = list(names)

    function_needles = []
    if kind in ('*', 'function'):
        function_needles = list(names)

    return dataclasses.replace(
        selection,
        function_names=[],
        function_needles=function_needles,
        layer_names=[],
        layer_needles=layer_needles,
        bundle_all=False,
    )


def run(ex: 'interactivity.Execution'):
    """Specify the target function(s) and/or layer(s) to target."""
    selection: 'definitions.Selection' = ex.shell.selection
    is_exact = ex.args.get('exact', False)
    kind = ex.args['kind']

    names = ex.args.get('name') or '*'
    if names and isinstance(names, str):
        names = [names]
    else:
        names = list(names)

    if kind == '*' and not names:
        ex.shell.selection = dataclasses.replace(
            selection,
            function_needles=['*'],
            layer_needles=['*'],
            bundle_all=True,
        )
        return

    if is_exact:
        ex.shell.selection = _update_exact_selection(kind, names, selection)
        return

    ex.shell.selection = _update_fuzzy_selection(kind, names, selection)
