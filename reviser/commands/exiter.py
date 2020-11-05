"""
Exits the shell and returns to the parent terminal.
"""
import argparse
import typing

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
    """Exits the shell."""
    ex.shell.shutdown = True
    return ex.finalize(
        status="EXIT",
        message="Shutting down the shell.",
        echo=True,
    )
