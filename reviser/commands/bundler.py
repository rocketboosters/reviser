"""
Install dependencies and copies includes into a zipped file ready for deployment.

The resulting zip file is structured correctly to be deployed to the lambda
function/layer target via an S3 upload and subsequent publish command.
"""

import argparse
import pathlib
import shutil
import typing

from reviser import bundling
from reviser import definitions
from reviser import interactivity


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Get shell auto-completes for this command."""
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
    parser.add_argument(
        "--output",
        "-o",
        help="Output the bundled artifacts into the specified output path.",
    )


def _copy_to_output(
    targets: typing.List["definitions.Target"], output_dir: typing.Optional[str]
):
    """Copy the outputs of the targets into the specified output directory."""
    if not output_dir:
        return
    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for target in targets:
        for name in target.names:
            shutil.copy(
                target.bundle_zip_path,
                output_path.joinpath(f"{name}-{target.kind.value}.zip"),
            )


def run(ex: "interactivity.Execution"):
    """Execute a bundle operation on the selected function/layer targets."""
    bundled_targets = bundling.create(
        context=ex.shell.context,
        selection=ex.shell.selection,
        reinstall=ex.args.get("reinstall", False),
    )
    _copy_to_output(bundled_targets.targets, ex.args.get("output"))
    print("\n\n")
    return ex.finalize(
        status="BUNDLED",
        message="Selected items have been bundled.",
        info={
            "items": [n for t in bundled_targets.targets for n in t.names],
        },
        echo=True,
    )
