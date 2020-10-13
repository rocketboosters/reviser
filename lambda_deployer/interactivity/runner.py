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
            are not set as an overriding alternative.
            """
    )
    parser.add_argument(
        '--run',
        dest='command_group_name',
        help="""
            Specifies a run command group to execute in a new shell
            session that exits after the commands have been executed.
            These command groups are useful for defining common operations
            to execute in a single command without opening a persistent
            shell. They are also useful for CI purposes. The value here
            must be specified in the lambda.yaml file under the top-level
            run key and must be a list of shell commands to execute.
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
    session = boto3.Session()
    context = definitions.Context.load_from_file(
        arguments=args,
        path=directory,
        connection=definitions.AwsConnection(session),
    )
    return interactivity.Shell(context)


def run_shell(
        arguments: typing.List[str] = None,
        command_queue: typing.List[str] = None,
) -> 'interactivity.Shell':
    """
    Start the shell process after loading configuration from the target
    directory determined by the command line arguments.
    """
    shell = create_shell(arguments)
    shell.command_queue += (
        command_queue
        or shell.context.command_queue
        or []
    )
    shell.run()
    return shell
