import os
import pathlib
import subprocess
import sys
import typing

import reviser
from reviser import parsing


def main(arguments: typing.List[str] = None):
    """Start the shell container based on the command line arguments."""
    print(f'\n[DIRECTORY]: {os.path.realpath(os.curdir)}')
    args = parsing.create_parser(False).parse_args(args=arguments)

    credentials_directory = pathlib.Path(args.aws_directory).absolute()
    deploy_directory = pathlib.Path(args.root_directory).absolute()
    folder_name = deploy_directory.name

    command = [
        'docker', 'run',
        '-it', '--rm',
        '-v', '{}:/root/.aws'.format(credentials_directory),
        '-v', '{}:/project/{}'.format(deploy_directory, folder_name),
        '--workdir=/project/{}'.format(folder_name),
        f'swernst/reviser:{reviser.__version__}-{args.runtime}',
        *(arguments or sys.argv)[1:],
    ]

    display = ' '.join(command).replace(' -', '\n        -')
    print(f'[RUN]: {display}\n')

    try:
        subprocess.check_call(command)
        return True
    except subprocess.CalledProcessError:
        return False


if __name__ == '__main__':
    main()
