import copy
import os
import pathlib
import shutil
import subprocess
import typing

from reviser import definitions


def _install_pip_package(name: str, site_packages: pathlib.Path):
    """Installs the specified pip package."""
    cmd = [
        "python",
        "-m",
        "pip",
        "install",
        "--upgrade",
        name,
        "-t",
        f'"{site_packages}"',
    ]
    print(" ".join(cmd).replace(" -", "\n  -"))
    os.system(" ".join(cmd))


def _install_pipper_package(
    name: str,
    site_packages: pathlib.Path,
    env: dict,
    arguments: typing.List[str] = None,
):
    """Installs the specified pipper package."""
    cmd = [
        "pipper",
        "install",
        name,
        "--upgrade",
        "--target",
        f'"{site_packages}"',
        *(arguments or []),
    ]
    print(" ".join(cmd).replace(" -", "\n  -"))
    subprocess.run(cmd, env=env, check=True)


def _install_poetry(dependency: "definitions.PoetryDependency"):
    """Installs poetry dependencies in the target's site packages."""
    for package in dependency.get_package_names() or []:
        print(f'\n[INSTALLING]: "{package}" poetry package')
        _install_pip_package(
            package,
            dependency.target.site_packages_directory,
        )
        print(f'\n[INSTALLED]: "{package}" poetry package')


def _install_pip(dependency: "definitions.PipDependency"):
    """Installs poetry dependencies in the target's site packages."""
    for package in dependency.get_package_names() or []:
        print(f'\n[INSTALLING]: "{package}" pip package')
        _install_pip_package(
            package,
            dependency.target.site_packages_directory,
        )
        print(f'\n[INSTALLED]: "{package}" pip package')


def _install_pipper(dependency: "definitions.PipperDependency"):
    """
    Installs any pipper dependencies alongside the standard pip site packages
    at the specified bundle site packages directory location.
    """
    credentials = dependency.connection.get_credentials()
    env_vars = {
        "PIPPER_AWS_ACCESS_KEY_ID": credentials.access_key,
        "PIPPER_AWS_SECRET_ACCESS_KEY": credentials.secret_key,
        "PIPPER_AWS_SESSION_TOKEN": credentials.token,
    }
    env = copy.copy(os.environ)
    # Depending on what type os session source is used, one or more of
    # these will be None and None values cannot be included in environment
    # variables without raising a TypeError: str expected, not NoneType.
    env.update({k: v for k, v in env_vars.items() if v is not None})

    for package in dependency.get_package_names():
        additional_kwargs = {
            "--bucket": dependency.bucket,
            "--prefix": dependency.prefix,
        }
        arguments = [f"{k}={v}" for k, v in additional_kwargs.items() if v is not None]

        print(f'\n[INSTALLING]: "{package}" pipper package')

        _install_pipper_package(
            package,
            dependency.target.site_packages_directory,
            typing.cast(dict, env),
            arguments,
        )
        print(f'\n[INSTALLED]: "{package}" pipper package')


def install_dependencies(target: "definitions.Target"):
    """Install the dependencies for the specified target."""
    if target.site_packages_directory.exists():
        print("\n[RESET]: Site packages directory exists and is being reset.")
        shutil.rmtree(
            str(target.site_packages_directory),
            ignore_errors=True,
        )

    target.site_packages_directory.mkdir(exist_ok=True, parents=True)

    callers: typing.Any = {
        definitions.DependencyType.PIPPER: _install_pipper,
        definitions.DependencyType.PIP: _install_pip,
        definitions.DependencyType.POETRY: _install_poetry,
    }

    for dependency in target.dependencies:
        # noinspection PyTypeChecker
        callers[dependency.kind](dependency)
