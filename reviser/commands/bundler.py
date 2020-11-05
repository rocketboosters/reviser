"""
Installs dependencies and copies includes into a zipped file that
is structured correctly to be deployed to the lambda function/layer
target.
"""
import argparse
import typing

from reviser import bundling
from reviser import interactivity


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return ["--reinstall"]


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    parser.add_argument(
        "--reinstall",
        action="store_true",
        help="""
            Add this flag to reinstall dependencies on a repeated
            bundle operation. By default, dependencies will remain
            cached for the lifetime of the shell to speed up the
            bundling process. This will force dependencies to be
            installed even if they had been installed previously.
            """,
    )


def run(ex: "interactivity.Execution"):
    """Execute a bundle operation on the selected function/layer targets."""
    bundled_targets = bundling.create(
        context=ex.shell.context,
        selection=ex.shell.selection,
        reinstall=ex.args.get("reinstall", False),
    )
    print("\n\n")
    return ex.finalize(
        status="BUNDLED",
        message="Selected items have been bundled.",
        info={
            "items": [n for t in bundled_targets.targets for n in t.names],
        },
        echo=True,
    )
