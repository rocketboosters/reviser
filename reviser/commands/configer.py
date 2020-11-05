"""
Displays the configs loaded from the lambda.yaml file and fully
populated with defaults and dynamic values. Use this to inspect
and validate that the loaded configuration meets expectations
when parsed into the reviser shell.
"""
import argparse
import typing

import yaml

from reviser import interactivity


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return []


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    pass


def run(ex: "interactivity.Execution") -> "interactivity.Execution":
    """Execute a bundle operation on the selected function/layer targets."""
    print(yaml.safe_dump(ex.shell.context.configuration.serialize()))
    return ex.finalize(status="SUCCESS", message="Configuration displayed.")
