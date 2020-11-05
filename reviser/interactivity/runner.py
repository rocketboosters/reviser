import pathlib
import typing

import boto3

from reviser import definitions
from reviser import interactivity
from reviser import parsing


def create_shell(arguments: typing.List[str] = None) -> "interactivity.Shell":
    """
    Creates a shell for interactive or queued command execution based on
    the specified command line arguments, which default to sys.argv if no
    arguments are specified.
    """
    args = parsing.create_parser(True).parse_args(arguments)
    directory = pathlib.Path(args.root_directory).absolute()
    session = boto3.Session(profile_name=args.aws_profile_name)
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
    Start the shell process after loading configuration from the target
    directory determined by the command line arguments.
    """
    shell = create_shell(arguments)
    shell.command_queue += command_queue or shell.context.command_queue or []
    shell.run()
    return shell
