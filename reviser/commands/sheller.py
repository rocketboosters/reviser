"""
Special command to use in run command groups/macros to start interactive
command mode for the terminal. Useful when in scenarios where you wish
to prefix an interactive session with commonly executed commands. For
example, if you want to select certain targets with the select command
as part of starting the shell, you could create a run command
group/macro in your lambda.yaml that executes the select command
and then executes the shell command. This would updated the selection
and then with the shell command, start the shell in interactive mode.
Without specifying the shell command here, the run command group/macro
would just set a selection and then exit.
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
    ex.shell.is_interactive = True
    return ex.finalize(
        status="SHELL",
        message="Switching to interactive shell execution.",
        echo=True,
    )
