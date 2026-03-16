"""
Upload the bundled contents to the upload S3 bucket and then publish a new version.

This will be carried out for each of the lambda targets with that new bundle and
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
    """Get shell auto-completes for this command."""
    return ["--description", "--dry-run", "--var"]


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
    parser.add_argument(
        "--var",
        action="append",
        dest="var",
        metavar="KEY=VALUE",
        help="""
        Specify a KEY=VALUE substitution variable to be applied to
        the image URI template at deploy time. For example,
        --var=ENV=prod will replace {ENV} in the image URI with
        'prod'. May be specified multiple times for multiple
        variables. Custom variables override built-in ones such
        as PACKAGE_VERSION.
        """,
    )


def _parse_image_vars(
    raw_vars: typing.Optional[typing.List[str]],
) -> typing.Dict[str, str]:
    """Parse a list of KEY=VALUE strings into a substitution dictionary."""
    result = {}
    for item in raw_vars or []:
        key, _, value = item.partition("=")
        result[key.strip()] = value
    return result


def run(ex: "interactivity.Execution"):
    """Execute a bundle operation on the selected function/layer targets."""
    description = string.Template(ex.args.get("description") or "").substitute(
        os.environ
    )
    image_vars = _parse_image_vars(ex.args.get("var"))
    print("\n\n")
    deployed_targets = deploying.deploy(
        context=ex.shell.context,
        selection=ex.shell.selection,
        description=description,
        dry_run=ex.args.get("dry_run") or False,
        image_vars=image_vars,
    )
    print("\n")
    return ex.finalize(
        status="DEPLOYED",
        message="Selected items have been deployed.",
        info={
            "dry_run": ex.args.get("dry_run"),
            "items": [n for t in deployed_targets for n in t.names],
            "description": description,
            "image_vars": image_vars,
        },
        echo=True,
    )
