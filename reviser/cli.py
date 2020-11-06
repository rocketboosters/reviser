import os
import pathlib
import subprocess
import sys
import typing

from reviser import parsing


def main(arguments: typing.List[str] = None):
    """Start the shell container based on the command line arguments."""
    print(f"\n[DIRECTORY]: {os.path.realpath(os.curdir)}")
    args = parsing.create_parser(False).parse_args(args=arguments)

    credentials_directory = pathlib.Path(args.aws_directory).absolute()
    deploy_directory = pathlib.Path(args.root_directory).absolute()
    folder_name = deploy_directory.name
    version = args.image_tag_version

    command = [
        "docker",
        "run",
        "-it",
        "--rm",
        "-v",
        "{}:/root/.aws".format(str(credentials_directory).replace("\\", "/")),
        "-v",
        "{}:/project/{}".format(str(deploy_directory), folder_name),
        "--workdir=/project/{}".format(folder_name),
        f"swernst/reviser:{version}-{args.runtime}",
        *[a.replace("\\", "/") for a in (arguments or sys.argv)[1:]],
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
