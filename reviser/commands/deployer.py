"""
Uploads the bundled contents to the upload S3 bucket and then publishes
a new version of each of the lambda targets with that new bundle and
any modified settings between the current configuration and that target's
existing configuration. This command will fail if a target being deployed
has not already been bundled.
"""
import argparse
import os
import string
import typing

from reviser import deploying
from reviser import interactivity


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return ["--description", "--dry-run"]


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    parser.add_argument(
        "--description",
        help="""
        Specify a message to assign to the version published by
        the deploy command.
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="""
        If set, the deploy operation will be exercised without
        actually carrying out the actions. This can be useful to
        validate the deploy process without side effects.
        """,
    )


def run(ex: "interactivity.Execution"):
    """Execute a bundle operation on the selected function/layer targets."""
    description = string.Template(ex.args.get("description") or "").substitute(
        os.environ
    )
    print("\n\n")
    deployed_targets = deploying.deploy(
        context=ex.shell.context,
        selection=ex.shell.selection,
        description=description,
        dry_run=ex.args.get("dry_run") or False,
    )
    print("\n")
    return ex.finalize(
        status="DEPLOYED",
        message="Selected items have been deployed.",
        info={
            "dry_run": ex.args.get("dry_run"),
            "items": [n for t in deployed_targets for n in t.names],
            "description": description,
        },
        echo=True,
    )
