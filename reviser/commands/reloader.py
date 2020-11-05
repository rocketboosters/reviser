"""
Reloads the lambda.yaml configuration file from disk.
"""
import argparse
import typing

import yaml

from reviser import definitions
from reviser import interactivity


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return []


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    pass


def _merge_target_uuids(
    before: "definitions.Target",
    after: "definitions.Target",
):
    """
    Adds matching UUIDs from the before to the after targets and children
    for continuity.
    """
    after.data["_uuid"] = before.uuid
    after.bundle.data["_uuid"] = before.bundle.uuid

    mapping = {
        f"{d.kind}:{p}": d for d in before.dependencies for p in d.get_package_names()
    }

    for dependency in after.dependencies:
        keys = [f"{dependency.kind}:{p}" for p in dependency.get_package_names()]
        match: typing.Optional[definitions.Dependency] = next(
            (d for k, d in mapping.items() if k in keys), None
        )
        if match:
            dependency.data["_uuid"] = match.uuid


def _merge_uuids(
    before: "definitions.Configuration",
    after: "definitions.Configuration",
):
    """Adds matching UUIDs from before to the after for continuity."""
    after.data["_uuid"] = before.uuid

    mapping = {name: target for target in before.targets for name in target.names}

    for target in after.targets:
        match: typing.Optional[definitions.Target] = next(
            (t for n, t in mapping.items() if n in target.names),
            None,
        )
        if match:
            _merge_target_uuids(match, target)


def run(ex: "interactivity.Execution") -> "interactivity.Execution":
    """Execute a bundle operation on the selected function/layer targets."""
    before = ex.shell.context
    directory = before.configuration.directory
    connection = before.connection
    after = definitions.Context.load_from_file(
        arguments=before.arguments,
        path=str(directory),
        connection=connection,
    )
    _merge_uuids(before.configuration, after.configuration)
    ex.shell.context = after

    print(yaml.safe_dump(ex.shell.context.configuration.serialize()))
    return ex.finalize(
        status="SUCCESS",
        message="Configuration file has been reloaded from disk.",
        echo=True,
        data={"before": before, "after": after},
    )
