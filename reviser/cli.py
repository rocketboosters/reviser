import os
import pathlib
import subprocess
import sys
import typing

from reviser import parsing


def _remove_arg(
    source: typing.List[str],
    flag: str,
    has_value: bool,
) -> typing.List[str]:
    """
    Searches for the specified flag within the source arguments and removes it
    and its optional value if has_value is specified, returning a copy of the source
    list with those elements removed. If the flag is not found an unaltered copy of
    the source list is returned instead. This is used in the CLI command to prevent
    certain flags from being used in both the host and container invocation contexts.
    """
    try:
        index = source.index(flag)
        offset = 1 if has_value else 0
        next_index = index + 1 + offset
        return source[:index] + source[next_index:]
    except ValueError:
        pass

    if not flag.startswith("--"):
        return source.copy()

    try:
        finder = (i for i, x in enumerate(source) if x.startswith(f"{flag}="))
        index = next(finder)
        next_index = index + 1
        return source[:index] + source[next_index:]
    except StopIteration:
        pass

    return source.copy()


def main(arguments: typing.List[str] = None) -> bool:
    """Start the shell container based on the command line arguments."""
    print(f"\n[DIRECTORY]: {os.path.realpath(os.curdir)}")
    args = parsing.create_parser(False).parse_args(args=arguments)

    credentials_directory = pathlib.Path(args.aws_directory).absolute()
    deploy_directory = pathlib.Path(args.root_directory).absolute()
    folder_name = deploy_directory.name
    version = args.image_tag_version

    container_args = [a.replace("\\", "/") for a in (arguments or sys.argv[1:])]
    container_args = _remove_arg(container_args, "-d", True)
    container_args = _remove_arg(container_args, "--directory", True)
    container_args = _remove_arg(container_args, "--tag-version", True)

    command = [
        "docker",
        "run",
        "-it",
        "--rm",
        "-v",
        "{}:/root/.aws".format(str(credentials_directory).replace("\\", "/")),
        "-v",
        "{}:/project/{}".format(str(deploy_directory).replace("\\", "/"), folder_name),
        "--workdir=/project/{}".format(folder_name),
        f"swernst/reviser:{version}-{args.runtime}",
        *container_args,
    ]

    display = " ".join(command).replace(" -", "\n        -")
    print(f"[RUN]: {display}\n")

    try:
        subprocess.check_call(command)
        return True
    except subprocess.CalledProcessError:
        return False


if __name__ == "__main__":
    main()
