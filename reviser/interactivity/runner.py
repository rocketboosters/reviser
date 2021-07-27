"""Shell execution module."""
import pathlib
import typing
import sys

import boto3

from reviser import definitions
from reviser import interactivity
from reviser import parsing


def create_shell(arguments: typing.List[str] = None) -> "interactivity.Shell":
    """
    Create a shell for interactive or queued command execution.

    The type of shell is based on the specified command line arguments, which default
    to sys.argv if no arguments are specified.
    """
    args = parsing.create_parser(True).parse_args(arguments)
    directory = pathlib.Path(args.root_directory).absolute()
    session = boto3.Session(
        profile_name=args.aws_profile_name,
        region_name=args.aws_region_name,
    )
    context = definitions.Context.load_from_file(
        arguments=args,
        path=directory,
        connection=definitions.AwsConnection(session),
    )
    return interactivity.Shell(context)


def run_shell(
    arguments: typing.List[str] = None,
    command_queue: typing.List[str] = None,
) -> "interactivity.Shell":
    """
    Start the shell process.

    The shell is started after first loading configuration from the target
    directory determined by the command line arguments.
    """
    shell = create_shell(arguments)
    shell.command_queue += command_queue or shell.context.command_queue or []
    shell.run()
    return shell


def main_shell() -> None:  # pragma: no cover
    """Execute entrypoint for the local shell cli."""
    shell = run_shell()
    sys.exit(1 if shell.error else 0)
