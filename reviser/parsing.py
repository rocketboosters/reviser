import argparse
import os
import pathlib
import sys

import reviser


def _suppress(condition: bool, help_doc: str) -> str:
    """Returns the help status based on the suppression condition."""
    if condition:
        return argparse.SUPPRESS
    return help_doc


def _get_auth_directory() -> pathlib.Path:
    """Finds the first valid and specified AWS credentials directory."""
    if creds_path := os.environ.get("AWS_SHARED_CREDENTIALS_FILE"):
        return pathlib.Path(creds_path).expanduser().parent.absolute()

    if config_path := os.environ.get("AWS_CONFIG_FILE"):
        return pathlib.Path(config_path).expanduser().parent.absolute()

    return pathlib.Path("~/.aws").expanduser().absolute()


def create_parser(internal_parser: bool) -> argparse.ArgumentParser:
    """..."""
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        prog="reviser",
    )

    # These are arguments from the wrapping command line interface that
    # may bleed through into the execution and should be ignored here
    # but not lead to a parsing error for unknown arguments. These also
    # serve to prevent conflicting arguments from being created here in
    # the future as these are reserved for the wrapping command execution.
    info = sys.version_info
    parser.add_argument(
        "--runtime",
        default=f"{info.major}.{info.minor}",
        help=_suppress(
            internal_parser,
            """
            Python runtime version of the lambda function(s)/layer(s)
            that will be deployed to from this shell.
            """,
        ),
    )

    parser.add_argument(
        "--tag-version",
        dest="image_tag_version",
        default=reviser.__version__,
        help=_suppress(
            internal_parser,
            """
            Image tag version prefix to use to launch the container. Defsults
            to the version of reviser used to launch the container.
            """,
        ),
    )

    parser.add_argument(
        "--aws-directory",
        default=str(_get_auth_directory()),
        help=_suppress(
            internal_parser,
            """
            Specifies the directory where AWS credentials are stored.
            This directory will be mounted as a volume into the shell
            container at launch to make credentials available within
            the running container for interacting with AWS resources.
            """,
        ),
    )

    parser.add_argument(
        "-d",
        "--directory",
        dest="root_directory",
        default=os.path.realpath(os.curdir),
        help="""
            The root directory where the lambda shell executions will
            take place. By default it is the current directory at the
            time the shell is started.
            """,
    )
    parser.add_argument(
        "-p",
        "--profile",
        dest="aws_profile_name",
        help="""
            The profile name for the AWS session that will be used to
            interact with lambda during the deployment process. If not
            set the default profile will be used if environment variables
            are not set as an overriding alternative.
            """,
    )
    parser.add_argument(
        "--run",
        dest="command_group_name",
        help="""
            Specifies a run command group to execute in a new shell
            session that exits after the commands have been executed.
            These command groups are useful for defining common operations
            to execute in a single command without opening a persistent
            shell. They are also useful for CI purposes. The value here
            must be specified in the lambda.yaml file under the top-level
            run key and must be a list of shell commands to execute.
            """,
    )

    return parser
