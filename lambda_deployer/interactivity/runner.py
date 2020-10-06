import argparse
import os
import pathlib
import typing

import boto3

from lambda_deployer import definitions
from lambda_deployer import interactivity


def _parse(arguments: typing.List[str] = None) -> argparse.Namespace:
    """Parse command line arguments to start the shell process."""
    parser = argparse.ArgumentParser(prog='lambda_deployer')
    parser.add_argument(
        '-d', '--directory',
        dest='root_directory',
        default=os.path.realpath(os.curdir),
        help="""
            The root directory where the lambda shell executions will
            take place. By default it is the current directory at the
            time the shell is started. 
            """
    )
    parser.add_argument(
        '-p', '--profile',
        dest='aws_profile_name',
        help="""
            The profile name for the AWS session that will be used to
            interact with lambda during the deployment process. If not
            set the default profile will be used if environment variables
            are not set as an alternative.
            """
    )
    return parser.parse_args(args=arguments)


def create_shell(arguments: typing.List[str] = None) -> 'interactivity.Shell':
    """
    Creates a shell for interactive or queued command execution based on
    the specified command line arguments, which default to sys.argv if no
    arguments are specified.
    """
    args = _parse(arguments)
    directory = pathlib.Path(args.root_directory).absolute()
    session = boto3.Session(profile_name=args.aws_profile_name)
    context = definitions.Context.load_from_file(
        path=directory,
        connection=definitions.AwsConnection(session)
    )
    return interactivity.Shell(context)


def run_shell(
        arguments: typing.List[str] = None,
        command_queue: typing.List[str] = None
) -> 'interactivity.Shell':
    """
    Start the shell process after loading configuration from the target
    directory determined by the command line arguments.
    """
    shell = create_shell(arguments)
    if command_queue:
        shell.process(command_queue)
    else:
        shell.loop()
    return shell
