"""
Allow for selecting subsets of the targets within the loaded configuration.

The subsets are fuzzy-matched unless the --exact flag is used.
"""
import argparse
import dataclasses
import typing

from reviser import definitions
from reviser import interactivity


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Get shell auto-completes for this command."""
    return ["*", "--exact", "--functions", "--layers"]


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for the select command."""
    parser.add_argument(
        "--functions",
        "--function",
        "--func",
        "-f",
        dest="functions",
        action="store_true",
        help="""
        When specified, functions will be selected. This will default to true if
        neither of --functions or --layers is specified. Will default to false if
        --layers is specified.
        """,
    )
    parser.add_argument(
        "--layers",
        "--layer",
        "-l",
        dest="layers",
        action="store_true",
        help="""
        When specified, layers will be selected. This will default to true if
        neither of --functions or --layers is specified. Will default to false if
        --functions is specified.
        """,
    )
    parser.add_argument(
        "name",
        nargs="*",
        help="""
        Specifies the value to match against the function
        and layer target names available from the configuration.
        This can include shell-style wildcards and will also
        match against partial strings. If the --exact flag is
        specified, this value must exactly match one of the targets
        instead of the default fuzzy matching behavior.
        """,
    )
    parser.add_argument(
        "--exact",
        action="store_true",
        help="Forces the match to be exact instead of fuzzy.",
    )


def _update_exact_selection(
    names: typing.List[str],
    functions: bool,
    layers: bool,
    selection: "definitions.Selection",
) -> "definitions.Selection":
    """Create a new selection object updated with the specified exact match."""
    both = not functions and not layers

    layer_names = []
    if layers or both:
        layer_names = list(names)

    function_names = []
    if functions or both:
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
    names: typing.List[str],
    functions: bool,
    layers: bool,
    selection: "definitions.Selection",
) -> "definitions.Selection":
    """Create a new selection object updated with the specified fuzzy match."""
    both = not functions and not layers

    layer_needles = []
    if layers or both:
        layer_needles = list(names)

    function_needles = []
    if functions or both:
        function_needles = list(names)

    return dataclasses.replace(
        selection,
        function_names=[],
        function_needles=function_needles,
        layer_names=[],
        layer_needles=layer_needles,
        bundle_all=False,
    )


def _get_names(ex: "interactivity.Execution") -> typing.List[str]:
    """Get selection names to use as filters."""
    names: typing.Union[str, typing.List[str]] = ex.args.get("name") or "*"
    if names and isinstance(names, str):
        return [names]

    return list(names)


def _to_names(
    targets: typing.List["definitions.Target"],
) -> typing.Union[str, typing.List[str]]:
    """Convert list of targets to a list of target names for output."""
    if not targets:
        return "None"

    return [n for t in targets for n in t.names]


def run(ex: "interactivity.Execution"):
    """Specify the target function(s) and/or layer(s) to target."""
    selection: "definitions.Selection" = ex.shell.selection
    is_exact = ex.args.get("exact", False)
    functions = ex.args.get("functions", False)
    layers = ex.args.get("layers", False)
    both = not functions and not layers
    names = _get_names(ex)

    if both and names == ["*"]:
        status = "ALL"
        message = "Selection has been cleared. All items are now selected."
        ex.shell.selection = dataclasses.replace(
            selection,
            function_needles=["*"],
            layer_needles=["*"],
            bundle_all=True,
        )
    elif is_exact:
        status = "EXACT"
        message = "Exact selection has been applied."
        ex.shell.selection = _update_exact_selection(
            names=names,
            functions=functions,
            layers=layers,
            selection=selection,
        )
    else:
        status = "MATCH"
        message = "Matching items have been selected."
        ex.shell.selection = _update_fuzzy_selection(
            names=names,
            functions=functions,
            layers=layers,
            selection=selection,
        )

    targets = ex.shell.context.get_selected_targets(ex.shell.selection)
    return ex.finalize(
        status=status,
        message=message,
        echo=True,
        info={
            "functions": _to_names(targets.function_targets),
            "layers": _to_names(targets.layer_targets),
        },
    )
