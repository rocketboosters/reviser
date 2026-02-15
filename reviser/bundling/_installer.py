"""_installer functionality module."""

import copy
import os
import pathlib
import shutil
import subprocess
import typing

from reviser import definitions


def _install_pip_package(
    name: str,
    site_packages: pathlib.Path,
    arguments: typing.Optional[typing.List[str]] = None,
):
    """Install the specified pip package."""
    cmd = [
        "python",
        "-m",
        "pip",
        "install",
        "--upgrade",
        name,
        "-t",
        f'"{site_packages}"',
        *(arguments or []),
    ]
    print(" ".join(cmd).replace(" -", "\n  -"))
    os.system(" ".join(cmd))


def _install_pipper_package(
    name: str,
    site_packages: pathlib.Path,
    env: dict,
    arguments: typing.Optional[typing.List[str]] = None,
):
    """Install the specified pipper package."""
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
    """Install poetry dependencies in the target's site packages."""
    arguments = [f"{k}={v}" for k, v in dependency.arguments.items() if v is not None]
    for package in dependency.get_package_names() or []:
        print(f'\n[INSTALLING]: "{package}" poetry package')
        _install_pip_package(
            package, dependency.group.site_packages_directory, arguments
        )
        print(f'\n[INSTALLED]: "{package}" poetry package')


def _install_uv(dependency: "definitions.UvDependency"):
    arguments = [f"{k}={v}" for k, v in dependency.arguments.items() if v is not None]
    for package in dependency.get_package_names() or []:
        print(f'\n[INSTALLING]: "{package}" uv package')
        _install_pip_package(
            package, dependency.group.site_packages_directory, arguments
        )
        print(f'\n[INSTALLED]: "{package}" uv package')


def _install_command(
    dependency: "definitions.UvCommandDependency | definitions.PoetryCommandDependency",
):
    """Install dependencies via command and copy from .venv to target site packages."""
    dependency.execute_command()

    # Find the .venv site-packages directory
    venv_dir = dependency.directory.joinpath(".venv")
    if not venv_dir.exists():
        print(
            f"\n[WARNING] .venv directory not found at {venv_dir}. "
            "Skipping package copy."
        )
        return

    # Find the site-packages directory within .venv
    # Structure is typically .venv/lib/python3.X/site-packages
    lib_dir = venv_dir.joinpath("lib")
    if not lib_dir.exists():
        print(
            f"\n[WARNING] lib directory not found in .venv at {lib_dir}. "
            "Skipping package copy."
        )
        return

    site_packages_dirs = list(lib_dir.glob("python*/site-packages"))
    if not site_packages_dirs:
        print(
            f"\n[WARNING] No site-packages directory found in {lib_dir}. "
            "Skipping package copy."
        )
        return

    source_site_packages = site_packages_dirs[0]
    target_site_packages = dependency.group.site_packages_directory

    print(
        f"\n[COPYING] Packages from {source_site_packages} "
        f"to {target_site_packages}"
    )

    # Ensure target directory exists
    target_site_packages.mkdir(parents=True, exist_ok=True)

    # Copy all packages from .venv site-packages to target site-packages
    for item in source_site_packages.iterdir():
        source_item = source_site_packages.joinpath(item.name)
        target_item = target_site_packages.joinpath(item.name)

        if source_item.is_dir():
            if target_item.exists():
                shutil.rmtree(target_item)
            shutil.copytree(source_item, target_item)
        else:
            shutil.copy2(source_item, target_item)

    print("\n[COPIED] Successfully copied packages from .venv to bundle directory")


def _install_pip(dependency: "definitions.PipDependency"):
    """Install poetry dependencies in the target's site packages."""
    arguments = [f"{k}={v}" for k, v in dependency.arguments.items() if v is not None]
    for package in dependency.get_package_names() or []:
        print(f'\n[INSTALLING]: "{package}" pip package')
        _install_pip_package(
            package, dependency.group.site_packages_directory, arguments
        )
        print(f'\n[INSTALLED]: "{package}" pip package')


def _install_pipper(dependency: "definitions.PipperDependency"):
    """
    Install any pipper dependencies alongside the standard pip site packages.

    This is carried out at the specified bundle site packages directory location.
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
    additional_kwargs = {
        "--bucket": dependency.bucket,
        "--prefix": dependency.prefix,
    }
    arguments = [
        f"{k}={v}"
        for k, v in {**additional_kwargs, **dependency.arguments}.items()
        if v is not None
    ]

    for package in dependency.get_package_names():
        print(f'\n[INSTALLING]: "{package}" pipper package')
        _install_pipper_package(
            package,
            dependency.group.site_packages_directory,
            typing.cast(dict, env),
            arguments,
        )
        print(f'\n[INSTALLED]: "{package}" pipper package')


def copy_shared_dependencies(target: "definitions.Target"):
    """Copy installed shared dependencies into the target site packages folder."""
    if not target.dependencies.is_shared:
        return

    if target.site_packages_directory.exists():
        print("\n[REPLACING] Site packages directory with latest shared version.")
        shutil.rmtree(target.site_packages_directory)
    print("\n[COPYING] Shared site packages directory to target.")
    shutil.copytree(
        src=target.dependencies.site_packages_directory,
        dst=target.site_packages_directory,
    )


def install_dependencies(target: "definitions.Target"):
    """Install the dependencies for the specified target."""
    if target.dependencies.site_packages_directory.exists():
        print("\n[RESET] Site packages directory exists and is being reset.")
        shutil.rmtree(
            str(target.site_packages_directory),
            ignore_errors=True,
        )

    target.dependencies.site_packages_directory.mkdir(exist_ok=True, parents=True)

    callers: typing.Any = {
        definitions.DependencyType.PIPPER: _install_pipper,
        definitions.DependencyType.PIP: _install_pip,
        definitions.DependencyType.POETRY: _install_poetry,
        definitions.DependencyType.POETRY_COMMAND: _install_command,
        definitions.DependencyType.UV: _install_uv,
        definitions.DependencyType.UV_COMMAND: _install_command,
    }

    for dependency in target.dependencies.sources:
        # noinspection PyTypeChecker
        callers[dependency.kind](dependency)

    copy_shared_dependencies(target)
