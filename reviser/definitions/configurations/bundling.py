"""Bundle configuration data structures and IO module."""
import dataclasses
import glob
import pathlib
import shutil
import typing

from reviser.definitions import abstracts
from reviser.definitions import configurations
from reviser.definitions import enumerations


def _get_paths(patterns: typing.Set[pathlib.Path]) -> typing.Set[pathlib.Path]:
    """Convert a set of file/directory patterns into a list of matching files."""
    raw = [
        pathlib.Path(item)
        for pattern in patterns
        for item in glob.iglob(str(pattern), recursive=True)
    ]
    files = [p for p in raw if not p.is_dir()]
    output = files + [
        child
        for p in raw
        for item in glob.iglob(f"{p}/**/*", recursive=True)
        if p.is_dir() and not (child := pathlib.Path(item)).is_dir()
    ]
    return set(output)


@dataclasses.dataclass(frozen=True)
class CopyPath:
    """Data structure for a file path copy from source to target."""

    source: pathlib.Path
    destination: pathlib.Path

    def copy(self) -> bool:
        """Copy the file from source to destination."""
        if not self.source.exists():
            return False
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            src=str(self.source.absolute()),
            dst=str(self.destination.absolute()),
        )
        return True


@dataclasses.dataclass(frozen=True)
class Bundle(abstracts.Specification):
    """
    Define the function or layer bundle that will be generated.

    That is this defines the function or layer that will be built and deployed as a
    zipped artifact to the lambda function or layer target.
    """

    target: "configurations.Target"

    @property
    def handler(self) -> typing.Optional[str]:
        """
        Get the function handler in the format `filename.function_name`.

        If not specified explicitly, it will default to the lambda function default
        value of `lambda_function.lambda_handler`.
        """
        if self.target.kind == enumerations.TargetType.LAYER:
            return None
        return self.get("handler", default="lambda_function.lambda_handler")

    @property
    def handler_filename(self) -> typing.Optional[str]:
        """Get the python filename associated with the specified handler."""
        if handler := self.handler:
            return "{}.py".format(handler.rsplit(".", 1)[0])
        return None

    @property
    def handler_function(self) -> typing.Optional[str]:
        """Get the python entrypoint function name for the specified handler."""
        if handler := self.handler:
            return handler.rsplit(".", 1)[-1]
        return None

    @property
    def omitted_packages(self) -> typing.List[str]:
        """
        List site-packages to skip with creating the bundle.

        This is especially useful when package dependencies are installed
        in both a function and layer definition and should be omitted from
        one such that they are not duplicated in the final lambda function
        environment.
        """
        omissions = self.get("omit_packages", default=self.get("omit_package"))
        if isinstance(omissions, str):
            return [omissions]

        return omissions or []

    @property
    def file_include_patterns(self) -> typing.Set[pathlib.Path]:
        """
        List file matching patterns that will be copied into the bundled artifact.

        These should be defined relative the root directory defined by the location of
        the configuration file and stored in the directory value of this object.
        """
        includes = [
            pathlib.Path(p)
            for p in self.get_as_list("includes", default=self.get_as_list("include"))
        ]
        if isinstance(includes, str):
            includes = [includes]

        add_default_package = (
            not includes and self.target.kind == enumerations.TargetType.FUNCTION
        )
        if add_default_package:
            # If the user hasn't specified any includes, look for python
            # packages in the root directory and include those by default
            # for functions. By default, layers should include nothing.
            includes = [
                pathlib.Path(item).parent.absolute()
                for item in glob.iglob(
                    str(self.directory.joinpath("*/__init__.py")),
                    recursive=True,
                )
            ]

        if filename := self.handler_filename:
            # The handler file should always be included if set.
            includes.append(self.directory.joinpath(filename))

        return set([self.directory.joinpath(item).absolute() for item in includes])

    @property
    def file_exclude_patterns(self) -> typing.Set[pathlib.Path]:
        """
        List file matching patterns that will be skipped when copying sources.

        These should be defined relative the root directory defined by the location of
        the configuration file and stored in the directory value of this object. Note
        that exclusions are applied to the inclusion results after so only need to
        specify things to remove from the inclusion list, e.g. a `tests` folder.
        """
        excludes = self.get("excludes", default=self.get("exclude")) or []
        if isinstance(excludes, str):
            excludes = [excludes]

        # Exclude Python and OS cache files by default.
        excludes += ["**/__pycache__", "**/*.pyc", "**/.DS_Store"]

        return set([self.directory.joinpath(item).absolute() for item in excludes])

    @property
    def file_package_exclude_patterns(self) -> typing.Set[pathlib.Path]:
        """
        List file matching patterns that will be skipped when bundling dependencies.

        These should be defined relative the site packages directory in which the
        dependencies are resolved. This is used to remove portions of a site package
        if they are not needed. This could be because they are already installed in
        a layer and do not need to be duplicated. Or they could be bloated elements
        of a package to remove and save on the bundle size. Either way, use with
        care as these could cause corruption in the site packages.
        """
        excludes = self.get(
            "package_excludes", default=self.get("package_exclude") or []
        )
        if isinstance(excludes, str):
            excludes = [excludes]

        return set(
            [
                self.target.site_packages_directory.joinpath(item).resolve()
                for item in excludes
            ]
        )

    def get_include_paths(
        self,
        relative: bool = False,
    ) -> typing.Set[pathlib.Path]:
        """Generate a list of file paths matching the bundle includes."""
        items = _get_paths(self.file_include_patterns)
        if filename := self.handler_filename:
            items.add(self.directory.joinpath(filename))
        if relative:
            return set([item.relative_to(self.directory) for item in items])
        return items

    def get_exclude_paths(
        self,
        relative: bool = False,
    ) -> typing.Set[pathlib.Path]:
        """Generate a list of file paths matching the bundle excludes."""
        items = _get_paths(self.file_exclude_patterns)
        if relative:
            return set([item.relative_to(self.directory) for item in items])
        return items

    def get_paths(
        self,
        relative: bool = False,
    ) -> typing.Set[pathlib.Path]:
        """Generate a list of file paths matching the bundle excludes."""
        return self.get_include_paths(relative=relative) - self.get_exclude_paths(
            relative=relative
        )

    def get_copy_paths(self) -> typing.List["CopyPath"]:
        """
        List paths to copy where each maps source to destination for bundling.

        Each item returned contains an included (and not excluded) mapping from the
        source paths to their respective destination path in the bundle directory.
        """
        return [
            CopyPath(
                source=self.directory.joinpath(p),
                destination=self.target.bundle_directory.joinpath(p),
            )
            for p in self.get_paths(relative=True)
        ]

    def get_site_package_paths(self) -> typing.Set[pathlib.Path]:
        """
        List paths in the target bundle site packages directory to include in bundles.

        Omitted packages will be excluded from this list if any are specified in
        the bundle. Also, user-defined package_excludes paths will also be omitted.
        """
        directory = self.target.site_packages_directory
        exclusions = []
        for package in self.omitted_packages:
            exclusions += [
                directory.joinpath(package, "**", "*"),
                directory.joinpath(f"{package}.*"),
                directory.joinpath(f"{package}-*"),
                directory.joinpath(f"{package}-*", "**", "*"),
            ]
        omitted_paths = _get_paths(
            set(exclusions).union(self.file_package_exclude_patterns)
        )

        paths = _get_paths({directory.joinpath("**", "*")})
        return paths - omitted_paths

    def serialize(self) -> dict:
        """Serialize the object for output representation."""
        return {
            "handler": self.handler,
            "handler_filename": self.handler_filename,
            "handler_function": self.handler_function,
            "omitted_packages": self.omitted_packages,
            "file_include_patterns": [str(p) for p in self.file_include_patterns],
            "file_exclude_patterns": [str(p) for p in self.file_exclude_patterns],
        }
