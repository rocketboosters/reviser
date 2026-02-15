"""Dependency configuration data structures and IO module."""

import dataclasses
import json
import pathlib
import subprocess
import sys
import tempfile
import typing

from reviser import utils
from reviser.definitions import abstracts
from reviser.definitions import aws
from reviser.definitions import configurations
from reviser.definitions import enumerations


def parse_dependencies(
    directory: pathlib.Path,
    connection: "aws.AwsConnection",
    dependency_data: typing.List[typing.Dict[str, typing.Any]],
    is_shared: bool = False,
):
    """Parse configuration dependency data into a tuple of Dependency objects."""
    output = []

    dependency_types = enumerations.DependencyType
    mappings = typing.cast(
        typing.Dict[str, typing.Any],
        {
            dependency_types.PIP.value: PipDependency,
            dependency_types.PIPPER.value: PipperDependency,
            dependency_types.POETRY.value: PoetryDependency,
            dependency_types.POETRY_COMMAND.value: PoetryCommandDependency,
            dependency_types.UV.value: UvDependency,
            dependency_types.UV_COMMAND.value: UvCommandDependency,
        },
    )
    for data in dependency_data:
        kind = data.get("kind", dependency_types.PIP.value)
        constructor = typing.cast(
            typing.Any,
            mappings.get(kind, configurations.PipDependency),
        )
        output.append(
            constructor(
                directory=directory,
                data=data,
                connection=connection,
                is_shared=is_shared,
            )
        )

    return tuple(output)


@dataclasses.dataclass(frozen=True)
class DependencyGroup(abstracts.Specification):
    """Group of package dependencies."""

    configuration: "configurations.Configuration"
    target: typing.Optional["configurations.Target"] = None
    name: typing.Optional[str] = None

    @property
    def is_shared(self) -> bool:
        """Whether the dependency group is shared, or specific to a target."""
        return self.target is None

    @property
    def site_packages_directory(self) -> pathlib.Path:
        """Get the temporary location where site packages will be installed."""
        if self.target:
            return self.target.site_packages_directory
        return pathlib.Path(tempfile.gettempdir()).joinpath(self.uuid)

    @property
    def sources(self) -> typing.Tuple["Dependency", ...]:
        """Parse configuration dependency data into a tuple of Dependency objects."""
        output = []

        dependency_types = enumerations.DependencyType
        mappings = typing.cast(
            typing.Dict[str, typing.Any],
            {
                dependency_types.PIP.value: PipDependency,
                dependency_types.PIPPER.value: PipperDependency,
                dependency_types.POETRY.value: PoetryDependency,
                dependency_types.POETRY_COMMAND.value: PoetryCommandDependency,
                dependency_types.UV.value: UvDependency,
                dependency_types.UV_COMMAND.value: UvCommandDependency,
            },
        )
        for data in self.get_as_list("sources") or []:
            kind = data.get("kind", dependency_types.PIP.value)
            constructor = typing.cast(
                typing.Any, mappings.get(kind, configurations.PipDependency)
            )
            output.append(
                constructor(
                    directory=self.directory,
                    data=data,
                    connection=self.connection,
                    group=self,
                )
            )

        return tuple(output)

    def serialize(self) -> dict:
        """Serialize the object for output representation."""
        return {"sources": [d.serialize() for d in self.sources]}


@dataclasses.dataclass(frozen=True)
class Dependency(abstracts.Specification):
    """Package dependency data structure."""

    group: "DependencyGroup"

    @property
    def kind(self) -> "enumerations.DependencyType":
        """Get the kind of dependency."""
        return enumerations.DependencyType(
            value=self.get(
                "kind",
                default=enumerations.DependencyType.PIP.value,
            )
        )

    @property
    def file(self) -> typing.Optional[pathlib.Path]:
        """Get the optionally-specified path used to load dependencies."""
        if value := self.get("file"):
            return self.directory.joinpath(value).absolute()

        if self.get("packages") is not None:
            return None

        default = self.directory.joinpath(
            enumerations.DefaultFile.from_dependency_type(self.kind).value
        )
        return default if default.exists() else None

    @property
    def packages(self) -> typing.List[str]:
        """Get the explicitly defined packages."""
        return self.get_first_as_list(["packages"], ["package"], default=[])

    @property
    def skip_packages(self) -> typing.List[str]:
        """Get packages that should be skipped during the installation process."""
        return self.get_first_as_list(["skips"], ["skip"], default=[])

    @property
    def arguments(self) -> typing.Dict[str, str]:
        """Gets arguments that should be passed during the installation process."""
        return self.get_first_as_dict(["arguments"], default={})

    @property
    def command_args(self) -> typing.List[str]:
        """List command arguments for a command-based execution."""
        return self.get_as_list("args") or []

    def get_package_names(self) -> typing.List[str]:
        """List package names to install from the various package sources."""
        return []

    def execute_command(self):
        """Execute installation command specified in the configuration."""
        pass


@dataclasses.dataclass(frozen=True)
class PipDependency(Dependency):
    """Pip package dependency data structure."""

    def get_package_names(self) -> typing.List[str]:
        """List of package names to install collected from the various sources."""
        packages = self.packages.copy()
        if self.file:
            packages += [
                item
                for line in (self.file.read_text() or "").split("\n")
                if (item := line.strip())
            ]
        return [
            p
            for p in packages
            if utils.extract_package_name(p) not in self.skip_packages
        ]

    def serialize(self) -> dict:
        """Serialize the object for output representation."""
        return {
            "kind": self.kind.value,
            "packages": self.get_package_names(),
        }


@dataclasses.dataclass(frozen=True)
class PipperDependency(Dependency):
    """Pipper package dependency data structure."""

    @property
    def prefix(self) -> typing.Optional[str]:
        """Get the custom S3 key prefix in the bucket where the repository resides."""
        return self.get("prefix")

    @property
    def bucket(self) -> typing.Optional[str]:
        """Get the S3 bucket where the pipper repository resides."""
        return utils.get_matching_bucket(
            buckets=self.get_first(["buckets"], ["bucket"]),
            aws_region=self.group.configuration.aws_region,
            aws_account_id=self.connection.aws_account_id,
        )

    def get_package_data(self) -> typing.Optional[dict]:
        """Get the  data stored in the specified package file."""
        if self.file:
            return json.loads(self.file.read_text())
        return None

    def get_package_names(self) -> typing.List[str]:
        """List collected package names to install from various definition sources."""
        packages = self.packages.copy()
        if data := self.get_package_data():
            packages += data.get("dependencies") or []
        return [
            p
            for p in packages
            if utils.extract_package_name(p) not in self.skip_packages
        ]

    def serialize(self) -> dict:
        """Serialize the object for output representation."""
        return {
            "kind": self.kind.value,
            "prefix": self.prefix,
            "bucket": self.bucket,
            "packages": self.get_package_names(),
        }


def _find_poetry_executable() -> str:
    """Find the poetry executable path, or raise an error if not found."""
    directories = [
        pathlib.Path("~/.local/bin").expanduser(),
        pathlib.Path(sys.prefix).joinpath("bin"),
        pathlib.Path(sys.executable).parent,
    ]
    directories = [d for d in directories if d.exists()]

    finder = (
        str(p)
        for d in directories
        for p in d.iterdir()
        if p.name == "poetry" or p.name.startswith("poetry.")
    )
    try:
        return next(finder)
    except StopIteration:
        raise RuntimeError(
            "Unable to find poetry installation in current Python environment."
        )


@dataclasses.dataclass(frozen=True)
class PoetryDependency(Dependency):
    """Poetry package dependency data structure."""

    @property
    def extras(self) -> typing.List[str]:
        """List extra packages to install."""
        return self.get_as_list("extras", default=self.get_as_list("extra")) or []

    def get_package_names(self) -> typing.List[str]:
        """List collected package names to install from various definition sources."""
        packages = self.packages.copy()
        if not self.file:
            return packages

        executable = _find_poetry_executable()

        # Ensure that a lock file exists and is up-to-date before proceeding.
        command = [executable, "lock"]
        subprocess.run(command, stdout=subprocess.PIPE, check=True)

        command = [
            executable,
            "export",
            "--format=requirements.txt",
            "--without-hashes",
        ]

        for group in self.extras:
            command.append(f"--extras={group}")

        result = subprocess.run(command, stdout=subprocess.PIPE, check=True)

        packages += [
            item
            for line in result.stdout.decode().strip().split("\n")
            if (item := line.split(";")[0].strip())
        ]

        return [
            p
            for p in packages
            if utils.extract_package_name(p) not in self.skip_packages
        ]

    def serialize(self) -> dict:
        """Serialize the object for output representation."""
        return {
            "kind": self.kind.value,
            "packages": self.get_package_names(),
        }


def _find_uv_executable() -> str:
    """Find the uv executable path, or raise an error if not found."""
    result = subprocess.run(
        ["uv", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode == 0:
        return "uv"

    directories = [
        pathlib.Path("~/.local/bin").expanduser(),
        pathlib.Path(sys.prefix).joinpath("bin"),
        pathlib.Path(sys.executable).parent,
    ]
    directories = [d for d in directories if d.exists()]

    finder = (
        str(p)
        for d in directories
        for p in d.iterdir()
        if p.name == "uv" or p.name.startswith("uv.")
    )
    try:
        return next(finder)
    except StopIteration:
        raise RuntimeError(
            "Unable to find uv installation in current Python environment."
        )


@dataclasses.dataclass(frozen=True)
class UvDependency(Dependency):
    """UV package dependency data structure."""

    @property
    def extras(self) -> typing.List[str]:
        """List extra packages to install."""
        return self.get_as_list("extras", default=self.get_as_list("extra")) or []

    def get_package_names(self) -> typing.List[str]:
        """List collected package names to install from various definition sources."""
        packages = self.packages.copy()
        if not self.file:
            return packages

        executable = _find_uv_executable()

        # Ensure that a lock file exists and is up-to-date before proceeding.
        command = [executable, "lock"]
        subprocess.run(command, stdout=subprocess.PIPE, check=True)

        command = [
            executable,
            "pip",
            "--format=requirements.txt",
            "--no-hashes",
            "--no-annotate",
        ]

        for group in self.extras:
            command.append(f"--extras={group}")

        result = subprocess.run(command, stdout=subprocess.PIPE, check=True)

        packages += [
            item
            for line in result.stdout.decode().strip().split("\n")
            if (item := line.split(";")[0].strip())
        ]

        return [
            p
            for p in packages
            if utils.extract_package_name(p) not in self.skip_packages
        ]

    def serialize(self) -> dict:
        """Serialize the object for output representation."""
        return {
            "kind": self.kind.value,
            "packages": self.get_package_names(),
        }


@dataclasses.dataclass(frozen=True)
class UvCommandDependency(Dependency):
    """UV command-based package dependency data structure."""

    @property
    def extras(self) -> typing.List[str]:
        """List extra packages to install."""
        return []

    def get_package_names(self) -> typing.List[str]:
        """List collected package names to install from various definition sources."""
        return []

    def execute_command(self):
        """Execute installation command specified in the configuration."""
        executable = _find_uv_executable()
        command = [executable, *self.command_args]
        subprocess.run(command, stdout=subprocess.PIPE, check=True)

    def serialize(self) -> dict:
        """Serialize the object for output representation."""
        return {
            "kind": self.kind.value,
        }


@dataclasses.dataclass(frozen=True)
class PoetryCommandDependency(Dependency):
    """Poetry command-based package dependency data structure."""

    @property
    def extras(self) -> typing.List[str]:
        """List extra packages to install."""
        return []

    def get_package_names(self) -> typing.List[str]:
        """List collected package names to install from various definition sources."""
        return []

    def execute_command(self):
        """Execute installation command specified in the configuration."""
        executable = _find_poetry_executable()
        command = [executable, *self.command_args]
        subprocess.run(command, stdout=subprocess.PIPE, check=True)

    def serialize(self) -> dict:
        """Serialize the object for output representation."""
        return {
            "kind": self.kind.value,
        }
