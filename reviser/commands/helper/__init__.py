"""
Displays help information on the commands available within the
shell. Additional help on each command can be found using the
--help flag on the command in question.
"""
import argparse
import typing
import re

from reviser import commands
from reviser import interactivity
from reviser import templating

HEADER_REGEX = re.compile(r"#+\s+")


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return []


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    pass


def _get_command_header_doc(name: str, docs: str) -> str:
    """Returns the first paragraph of the command documentation."""
    lines = [
        line.rstrip()
        for line in (docs or "").split("\n")
        if not HEADER_REGEX.match(line)
    ]
    start_index = next((i for i, line in enumerate(lines) if line), 0)

    try:
        end_index = lines.index("", start_index) + 1
    except ValueError:
        end_index = len(lines) + 1

    aliases = ""
    if items := commands.REVERSED_ALIASES.get(name):
        aliases = "({}) ".format(", ".join(sorted(items)))

    return "{}{}".format(aliases, " ".join(lines[start_index:end_index]))


def run(ex: "interactivity.Execution") -> "interactivity.Execution":
    """Displays basic command help for the available shell commands."""
    command_docs = {
        name: _get_command_header_doc(name, docs)
        for name, command_module in commands.COMMANDS.items()
        if (docs := command_module.__doc__)
    }
    templating.printer(
        "commands/helper/help.jinja2",
        commands=list(sorted(command_docs.items(), key=lambda x: x[0])),
    )
    return ex.finalize(status="HELPED", message="Help displayed.")
