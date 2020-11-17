import dataclasses
import json
import pathlib
import subprocess
import sys
import typing

from reviser.definitions import abstracts
from reviser.definitions import configurations
from reviser.definitions import enumerations


@dataclasses.dataclass(frozen=True)
class Dependency(abstracts.Specification):
    """Package dependency data structure."""

    target: "configurations.Target"

    @property
    def kind(self) -> "enumerations.DependencyType":
        """Kind of dependency"""
        return enumerations.DependencyType(
            value=self.get(
                "kind",
                default=enumerations.DependencyType.PIP.value,
            )
        )

    @property
    def file(self) -> typing.Optional[pathlib.Path]:
        """Optionally specified path used to load dependencies."""
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
        """Explicitly defined packages."""
        return self.get_first_as_list(["packages"], ["package"], default=[])

    def get_package_names(self) -> typing.List[str]:
        """
        Returns a list of package names to install collected from
        the various ways packages can be specified.
        """
        return []


@dataclasses.dataclass(frozen=True)
class PipDependency(Dependency):
    """Pip package dependency data structure."""

    def get_package_names(self) -> typing.List[str]:
        """
        Returns a list of package names to install collected from
        the various ways packages can be specified.
        """
        packages = self.packages.copy()
        if self.file:
            packages += [
                item
                for line in (self.file.read_text() or "").split("\n")
                if (item := line.strip())
            ]
        return packages

    def serialize(self) -> dict:
        """Serializes the object for output representation."""
        return {
            "kind": self.kind.value,
            "packages": self.get_package_names(),
        }


@dataclasses.dataclass(frozen=True)
class PipperDependency(Dependency):
    """Pipper package dependency data structure."""

    @property
    def prefix(self) -> typing.Optional[str]:
        """Custom S3 key prefix in the bucket where the repository resides."""
        return self.get("prefix")

    @property
    def bucket(self) -> typing.Optional[str]:
        """S3 bucket where the pipper repository resides."""
        buckets = self.get("buckets", default=self.get("bucket", default=None))

        if not buckets and self.file:
            return (self.get_package_data() or {}).get("bucket") or None

        if isinstance(buckets, str):
            return buckets

        return buckets[self.connection.aws_account_id]

    def get_package_data(self) -> typing.Optional[dict]:
        """Returns the data stored in the specified package file."""
        if self.file:
            return json.loads(self.file.read_text())
        return None

    def get_package_names(self) -> typing.List[str]:
        """
        Returns a list of package names to install collected from
        the various ways packages can be specified.
        """
        packages = self.packages.copy()
        if data := self.get_package_data():
            packages += data.get("dependencies") or []
        return packages

    def serialize(self) -> dict:
        """Serializes the object for output representation."""
        return {
            "kind": self.kind.value,
            "prefix": self.prefix,
            "bucket": self.bucket,
            "packages": self.get_package_names(),
        }


@dataclasses.dataclass(frozen=True)
class PoetryDependency(Dependency):
    """Poetry package dependency data structure."""

    @property
    def extras(self) -> typing.List[str]:
        """List of extra packages to install."""
        return self.get_as_list("extras", default=self.get_as_list("extra")) or []

    def get_package_names(self) -> typing.List[str]:
        """
        Returns a list of package names to install collected from
        the various ways packages can be specified.
        """
        packages = self.packages.copy()
        if not self.file:
            return packages

        directories = [
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
        executable = next(finder, None)
        if executable is None:
            raise RuntimeError(
                "Unable to find poetry installation in current Python environment."
            )

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

        return packages

    def serialize(self) -> dict:
        """Serializes the object for output representation."""
        return {
            "kind": self.kind.value,
            "packages": self.get_package_names(),
        }
