"""Remove old function and/or layer versions for the selected targets."""
import argparse
import textwrap
import typing

from botocore.client import BaseClient

from reviser import definitions
from reviser import interactivity
from reviser import servicer


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Get shell auto-completes for this command."""
    return ["--start", "--end", "--dry-run"]


def populate_subparser(parser: argparse.ArgumentParser):
    """Add subcommand options for this command."""
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="""
            Keep versions lower (earlier/before) this one. A negative value can be
            specified for relative indexing in the same fashion as Python lists.
            """,
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="""
            Do not prune versions higher than this value. A negative value can be
            specified for relative indexing in the same fashion as Python lists.
            """,
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


def _resolve_version(
    versions: typing.Union[
        typing.List[definitions.LambdaLayer],
        typing.List[definitions.LambdaFunction],
    ],
    value: int = None,
) -> typing.Optional[int]:
    """
    Normalize specified versions by making them absolute, positive version integers.

    Leaves None and positive integer values alone, but will convert relative negative
    integers into their positive integer equivalents based on the available versions
    included in the version argument.

    :param versions:
        List of function or layer versions that currently exist, which will be used
        to resolve relative, negative values.
    :param value:
        Value to resolve.
    """
    if value is None or value >= 0:
        return value

    highest_version = max(
        [int(v.version or 0) for v in versions if "$" not in str(v.version)]
    )
    return max(0, highest_version + value)


def _is_within_range(
    function: "definitions.LambdaFunction",
    start_value: typing.Optional[int],
    end_value: typing.Optional[int],
) -> bool:
    """Determine if the function version is within the start and end range."""
    return (start_value is None or start_value <= int(function.version or 0)) and (
        end_value is None or int(function.version or 0) <= end_value
    )


def _get_function_removal_versions(
    lambda_client: BaseClient,
    function_name: str,
    start: int = None,
    end: int = None,
):
    """Get ARNs for the function that should be pruned."""
    versions = servicer.get_function_versions(lambda_client, function_name)
    start_value = _resolve_version(versions, start)
    end_value = _resolve_version(versions, end)
    return [
        v.arn
        for v in versions
        if v.version != "$LATEST"
        and v.arn
        and _is_within_range(v, start_value, end_value)
        and not v.aliases
    ]


def _prune_function(
    lambda_client: BaseClient,
    function_name: str,
    start: int = None,
    end: int = None,
    dry_run: typing.Optional[bool] = False,
    confirm: typing.Optional[bool] = True,
):
    """
    Execute a pruning operation on the given lambda functions.

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
    removal_arns = _get_function_removal_versions(
        lambda_client=lambda_client,
        function_name=function_name,
        start=start,
        end=end,
    )

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


def _get_layer_removal_versions(
    lambda_client: BaseClient,
    layer_name: str,
    start: int = None,
    end: int = None,
):
    """Get ARNs for the layer that should be pruned."""
    versions = servicer.get_layer_versions(lambda_client, layer_name)
    start_value = _resolve_version(versions, start)
    end_value = _resolve_version(versions, end)
    removals = [
        version
        for version in versions[:-1]
        if (start_value is None or start_value <= int(version.version or 0))
        and (end_value is None or int(version.version or 0) <= end_value)
    ]
    return [r.arn for r in removals if r.arn]


def _prune_layer(
    lambda_client: BaseClient,
    layer_name: str,
    start: int = None,
    end: int = None,
    dry_run: typing.Optional[bool] = False,
    confirm: typing.Optional[bool] = True,
):
    """
    Execute a pruning operation on the given lambda layers.

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
    removal_arns = _get_layer_removal_versions(
        lambda_client=lambda_client,
        layer_name=layer_name,
        start=start,
        end=end,
    )

    print("\nARN Versions to be removed:")
    print(
        textwrap.indent(
            "\n".join(removal_arns or []),
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
        print(f"[PRUNING]: {arn}")
        servicer.remove_layer_version(lambda_client, arn)

    return removal_arns


def run(ex: "interactivity.Execution") -> "interactivity.Execution":
    """Execute the pruning operation on the selected or specified targets."""
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
