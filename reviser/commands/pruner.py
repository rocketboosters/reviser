"""
Removes old function and/or layer versions for the selected targets.
"""
import textwrap
import argparse
import typing

from botocore.client import BaseClient

from reviser import definitions
from reviser import interactivity
from reviser import servicer


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return ["--start", "--end", "--dry-run"]


def populate_subparser(parser: argparse.ArgumentParser):
    """Add subcommand options for this command."""
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Keep versions lower (earlier/before) this one.",
    )

    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="Do not prune versions higher than this value.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Echo pruning operation without actually executing it.",
    )

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Run the prune process without reviewing first.",
    )


def _prune_function(
    lambda_client: BaseClient,
    function_name: str,
    start: int = None,
    end: int = None,
    dry_run: typing.Optional[bool] = False,
    confirm: typing.Optional[bool] = True,
):
    """
    Executes a pruning operation on the given lambda functions.

    :param lambda_client:
        Boto3 client interface for the lambda service
    :param function_name:
        Name of the function to prune
    :param start:
        First version of the lambda function to prune. Versions below
        that will be retained.
    :param end:
        Inclusive end version of the lambda function to prune. Versions
        above that will be retained.
    :param dry_run:
        If true, only print out what would happen and don't actually prune
        the versions.
    :param confirm:
        Whether or not to ask before proceeding with the prune operation.
    """
    versions = servicer.get_function_versions(lambda_client, function_name)
    removal_arns = [
        v.arn
        for v in versions
        if v.version != "$LATEST"
        and v.arn
        and (start is None or start <= int(v.version or 0))
        and (end is None or int(v.version or 0) <= end)
        and not v.aliases
    ]

    print("\nARN Versions to be removed:")
    print(
        textwrap.indent(
            "\n".join(removal_arns),
            prefix="  - ",
        )
    )

    if dry_run:
        print("\n[DRY RUN]: Skipped removal process.")
        return

    abort = confirm and not (
        input("\nExecute prune action [y/N]? ") or ""
    ).lower().startswith("y")
    if abort:
        print("\n[ABORTED]: Skipped removal process.")
        return

    for arn in removal_arns:
        servicer.remove_function_version(lambda_client, arn)

    return removal_arns


def _prune_layer(
    lambda_client: BaseClient,
    layer_name: str,
    start: int = None,
    end: int = None,
    dry_run: typing.Optional[bool] = False,
    confirm: typing.Optional[bool] = True,
):
    """
    Executes a pruning operation on the given lambda layers.

    :param lambda_client:
        Boto3 client interface for the lambda service.
    :param layer_name:
        Name of the layer to prune
    :param start:
        First version of the lambda layer to prune. Versions below
        that will be retained.
    :param end:
        Inclusive end version of the lambda layer to prune. Versions
        above that will be retained.
    :param dry_run:
        If true, only print out what would happen and don't actually prune
        the versions.
    :param confirm:
        Whether or not to ask before proceeding with the prune operation.
    """
    versions = servicer.get_layer_versions(lambda_client, layer_name)
    removals = [
        version
        for version in versions[:-1]
        if (start is None or start <= int(version.version or 0))
        and (end is None or int(version.version or 0) <= end)
    ]
    arns = [r.arn for r in removals if r.arn]

    print("\nARN Versions to be removed:")
    print(
        textwrap.indent(
            "\n".join(arns or []),
            prefix="  - ",
        )
    )

    if dry_run:
        print("\n[DRY RUN]: Skipped removal process.")
        return

    abort = confirm and not (
        input("\nExecute prune action [y/N]? ") or ""
    ).lower().startswith("y")
    if abort:
        print("\n[ABORTED]: Skipped removal process.")
        return

    for arn in arns:
        print(f"[PRUNING]: {arn}")
        servicer.remove_layer_version(lambda_client, arn)

    return arns


def run(ex: "interactivity.Execution") -> "interactivity.Execution":
    """Runs the pruning operation on the targets."""
    selected = ex.shell.context.get_selected_targets(ex.shell.selection)
    targets = sorted(selected.targets, key=lambda t: t.kind.value)

    caller = {
        definitions.TargetType.FUNCTION: _prune_function,
        definitions.TargetType.LAYER: _prune_layer,
    }

    results = {
        name: caller[target.kind](
            target.client("lambda"),
            name,
            start=ex.args.get("start"),
            end=ex.args.get("end"),
            dry_run=ex.args.get("dry_run") or False,
            confirm=not ex.args.get("yes") or False,
        )
        for target in targets
        for name in target.names
    }

    return ex.finalize(
        status="PRUNED",
        message="Specified versions have been removed.",
        info={name: removed_arns for name, removed_arns in results.items()},
        echo=True,
    )
