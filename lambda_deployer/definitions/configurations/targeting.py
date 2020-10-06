import dataclasses
import fnmatch
import pathlib
import re
import tempfile
import typing

from lambda_deployer.definitions import abstracts
from lambda_deployer.definitions import configurations
from lambda_deployer.definitions import enumerations
from lambda_deployer.definitions import selections


def _is_selected_match(
        target: 'Target',
        name: str,
):
    """
    Determines whether or not the target name is a match for the
    current selection set on the target object.
    """
    if not target.selection:
        return True

    if exacts := getattr(target.selection, f'{target.kind.value}_names'):
        return name in exacts

    needles = getattr(target.selection, f'{target.kind.value}_needles')
    any_needles = (
        bool(target.selection.function_needles)
        or bool(target.selection.layer_needles)
    )

    return (
        # Match everything if `--all` was specified.
        target.selection.bundle_all
        # No needles specified.
        or not any_needles
        # Identical match.
        or name in needles
        # Shell-style wildcard matches.
        or any([fnmatch.fnmatch(name, n) for n in needles])
        # Partial character matches.
        or any([n.lower() in name.lower() for n in needles])
    )


@dataclasses.dataclass(frozen=True)
class Target(abstracts.Specification):
    """
    Function or layer definition data structure where a target can
    represent one or more functions or one or more layers in the same
    definition for cases where function/layer duplication is desirable.
    A target, however, is of a homogeneous kind, meaning it will only
    be a function or layer.
    """

    configuration: 'configurations.Configuration'
    selection: 'selections.Selection' = None

    @property
    def aws_region(self) -> str:
        """AWS region name where this target resides."""
        return self.get('region', default=self.configuration.aws_region)

    @property
    def bundle(self) -> 'configurations.Bundle':
        """Bundle object associated with this target configuration."""
        return configurations.Bundle(
            directory=self.directory,
            data=self.get('bundle', default={}),
            connection=self.connection,
            target=self,
        )

    @property
    def layer_attachments(self) -> typing.List['configurations.AttachedLayer']:
        """
        List of layers that should be attached to functions in this target.
        This will always be an empty list for layer targets.
        """
        if self.kind == enumerations.TargetType.LAYER:
            return []
        values = self.get('layers', default=[])
        if isinstance(values, str):
            values = [values]
        values = [{'name': v} if isinstance(v, str) else v for v in values]
        return [
            configurations.AttachedLayer(
                directory=self.directory,
                data=v,
                connection=self.connection,
                target=self,
            )
            for v in values
        ]

    @property
    def variables(self) -> typing.List['configurations.EnvironmentVariable']:
        """
        List of environment variables that will be applied during
        function configuration updates within the deploy action. This
        will always be an empty list for layer targets that don't support
        environment variables.
        """
        if self.kind == enumerations.TargetType.LAYER:
            return []
        values = self.get('variables', default=[])
        if isinstance(values, str):
            values = [values]
        values = [{'arg': v} if isinstance(v, str) else v for v in values]
        return [
            configurations.EnvironmentVariable(
                directory=self.directory,
                data=v,
                connection=self.connection,
                target=self,
            )
            for v in values
        ]

    @property
    def ignores(self) -> typing.List[str]:
        """
        Items that should be skipped when modifying function configurations
        during the deployment process.
        """
        ignores = self.get('ignores', default=[])
        if isinstance(ignores, str):
            return [ignores]
        return [i.lower() for i in ignores]

    @property
    def bundle_directory(self) -> pathlib.Path:
        """Temporary location where the target will be assembled."""
        return pathlib.Path(tempfile.gettempdir()).joinpath(self.uuid)

    @property
    def bundle_zip_path(self) -> pathlib.Path:
        """Temporary location where the target zip bundle will be saved."""
        return pathlib.Path(tempfile.gettempdir()).joinpath(f'{self.uuid}.zip')

    @property
    def site_packages_directory(self) -> pathlib.Path:
        """Temporary location where site packages will be installed."""
        if self.kind == enumerations.TargetType.LAYER:
            return self.bundle_directory.joinpath('python')
        return self.bundle_directory.joinpath('site_packages')

    @property
    def kind(self) -> 'enumerations.TargetType':
        """Target type as one of 'function' or 'layer'."""
        # noinspection PyArgumentList
        return enumerations.TargetType(value=self.get(
            'kind',
            default=enumerations.TargetType.FUNCTION.value,
        ))

    @property
    def names(self) -> typing.List[str]:
        """Names of the targets associated with this definition."""
        names = self.get('names', default=self.get('name', default=[]))
        names = [names] if isinstance(names, str) else names
        return [str(n) for n in names if n and _is_selected_match(self, n)]

    @property
    def timeout(self) -> typing.Optional[int]:
        """
        Timeout, in seconds, after which the function stops executing. This
        will always be None for layers.
        """
        value = self.get('timeout')
        if not value or self.kind == enumerations.TargetType.LAYER:
            return None

        try:
            return int(value)
        except ValueError:
            regex = re.compile(r'^(?P<value>\d+).*')
            return int(regex.match(value).groupdict()['value'])

    @property
    def memory(self) -> typing.Optional[int]:
        """
        Memory, in MB, available to the function when executing. This
        will always be None for layers.
        """
        value = self.get('memory')
        if not value or self.kind == enumerations.TargetType.LAYER:
            return None

        try:
            return int(value)
        except ValueError:
            regex = re.compile(r'^(?P<value>\d+).*')
            return int(regex.match(value).groupdict()['value'])

    @property
    def dependencies(self) -> typing.List['configurations.Dependency']:
        """Dependencies for this function definition."""
        output = []

        for data in self.get('dependencies', default=[]):
            if data.get('kind') == enumerations.DependencyType.PIPPER.value:
                dependency = configurations.PipperDependency(
                    directory=self.directory,
                    data=data,
                    connection=self.connection,
                    target=self,
                )
            else:
                dependency = configurations.PipDependency(
                    directory=self.directory,
                    data=data,
                    connection=self.connection,
                    target=self,
                )
            output.append(dependency)

        return output

    def ignores_any(self, *args: str) -> bool:
        """True if any of the specified args appear in the ignores list."""
        ignores = self.ignores
        finder = (True for a in args if a in ignores)
        return next(finder, False)

    def serialize(self) -> dict:
        """Serializes the object for output representation."""
        if self.kind == enumerations.TargetType.FUNCTION:
            values = {
                'layers': [a.serialize() for a in self.layer_attachments],
                'variables': [v.serialize() for v in self.variables],
                'memory': self.memory,
                'timeout': self.timeout,
            }
        else:
            values = {}

        return {
            'kind': self.kind.value,
            'names': self.names,
            'region': self.aws_region,
            'bundle_directory': str(self.bundle_directory),
            'bundle_zip_path': str(self.bundle_zip_path),
            'site_packages_directory': str(self.site_packages_directory),
            'bundle': self.bundle.serialize(),
            'dependencies': [d.serialize() for d in self.dependencies],
            'ignores': self.ignores,
            **values,
        }
