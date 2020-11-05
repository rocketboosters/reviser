"""
Lists versions of the specified lambda targets with
info about each version.
"""
import typing
from argparse import ArgumentParser

from reviser import interactivity
from reviser import servicer


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return []


def populate_subparser(parser: ArgumentParser):
    """Configure the command arguments for this command."""
    pass


def run(ex: "interactivity.Execution") -> "interactivity.Execution":
    """Execute the listing command."""
    selected = ex.shell.context.get_selected_targets(ex.shell.selection)

    for target in selected.function_targets:
        client = target.client("lambda")
        servicer.echo_function_versions(client, target.names)

    for target in selected.layer_targets:
        client = target.client("lambda")
        function_names = [
            name
            for t in selected.function_targets
            for name in t.names
            if t.aws_region == target.aws_region
        ]
        servicer.echo_layer_versions(client, target.names, function_names)

    return ex.finalize(
        status="LISTED",
        message="Items have been listed.",
        echo=False,
    )
