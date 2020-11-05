"""
Allows for selecting subsets of the targets within the loaded configuration.
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
    """Shell auto-completes for this command."""
    return ["*", "function", "layer", "--exact"]


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for the select command."""
    parser.add_argument(
        "kind",
        choices=[
            definitions.TargetType.FUNCTION.value,
            definitions.TargetType.LAYER.value,
            "*",
        ],
        help="""
            Specify the type of objects to select or use * to
            select both types.
            """,
    )
    parser.add_argument(
        "name",
        nargs="?",
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
    kind: str,
    names: typing.List[str],
    selection: "definitions.Selection",
) -> "definitions.Selection":
    """Create a new selection object updated with the specified exact match."""
    layer_names = []
    if kind in ("*", "layer"):
        layer_names = list(names)

    function_names = []
    if kind in ("*", "function"):
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
    selection: "definitions.Selection",
) -> "definitions.Selection":
    """Create a new selection object updated with the specified fuzzy match."""
    layer_needles = []
    if kind in ("*", "layer"):
        layer_needles = list(names)

    function_needles = []
    if kind in ("*", "function"):
        function_needles = list(names)

    return dataclasses.replace(
        selection,
        function_names=[],
        function_needles=function_needles,
        layer_names=[],
        layer_needles=layer_needles,
        bundle_all=False,
    )


def run(ex: "interactivity.Execution"):
    """Specify the target function(s) and/or layer(s) to target."""
    selection: "definitions.Selection" = ex.shell.selection
    is_exact = ex.args.get("exact", False)
    kind = ex.args["kind"]

    names = ex.args.get("name") or "*"
    if names and isinstance(names, str):
        names = [names]
    else:
        names = list(names)

    if kind == "*" and names == ["*"]:
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
        ex.shell.selection = _update_exact_selection(kind, names, selection)
    else:
        status = "MATCH"
        message = "Matching items have been selected."
        ex.shell.selection = _update_fuzzy_selection(kind, names, selection)

    targets = ex.shell.context.get_selected_targets(ex.shell.selection)
    functions = [n for t in targets.function_targets for n in t.names]
    layers = [n for t in targets.layer_targets for n in t.names]
    return ex.finalize(
        status=status,
        message=message,
        echo=True,
        info={
            "functions": functions or "None",
            "layers": layers or "None",
        },
    )
