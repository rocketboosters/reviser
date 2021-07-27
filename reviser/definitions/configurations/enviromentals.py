"""Data structure and IO module for environment variables definitions."""
import dataclasses
import fnmatch
import typing

from reviser.definitions import abstracts
from reviser.definitions import configurations


@dataclasses.dataclass(frozen=True)
class EnvironmentVariable(abstracts.Specification):
    """Data structure for function environment variables."""

    target: "configurations.Target"

    @property
    def name(self) -> str:
        """Get the name for the environment variable."""
        if (name := self.get("name")) is not None:
            return name

        if (arg := self.get("arg")) is not None:
            return arg.split("=")[0]

        return "unknown-environment-variable"

    @property
    def preserve(self) -> bool:
        """
        Specify whether or not the environment variable should be preserved.

        Preserved environment variables will not be changed during updates. Useful for
        variables that are managed or assigned by other systems.
        """
        return self.get("preserve", default=False)

    @property
    def restrictions(self) -> typing.List[str]:
        """List lambda functions to attach this environment variable to."""
        value = self.get("only", default=[])
        if isinstance(value, str):
            return [value]
        return value

    @property
    def exclusions(self) -> typing.List[str]:
        """List lambda functions not to attach this environment variable to."""
        value = self.get("except", default=[])
        if isinstance(value, str):
            return [value]
        return value

    def _get_raw_value_for_function(self, function_name: str) -> typing.Optional[str]:
        """Get raw environment variable for the specified function name."""
        if not self.has("value") and (arg := self.get("arg")):
            value = arg.split("=", 1)[1]
        else:
            value = self.get("value")

        if isinstance(value, dict):
            selector = (
                v
                for pattern, v in value.items()
                if fnmatch.fnmatch(function_name, pattern)
            )
            value = next(selector, None)

        return value

    def _get_is_included(self, function_name: str) -> bool:
        """
        Determine if the env var is included in the specified function.

        This will return true for cases where no inclusion restrictions have been
        applied. Otherwise, it will return True only if the function name matches one
        of the inclusion restriction patterns.
        """
        includer = (
            True
            for pattern in self.restrictions
            if fnmatch.fnmatch(function_name, pattern)
        )
        return next(includer, not self.restrictions)

    def _get_is_excluded(self, function_name: str) -> bool:
        """Determine if the env var is excluded from the specified function."""
        excluder = (True for e in self.exclusions if fnmatch.fnmatch(function_name, e))
        return next(excluder, False)

    def get_value(self, function_name: str) -> typing.Optional[str]:
        """Retrieve the environment variable value for the given function name."""
        is_applicable = self._get_is_included(
            function_name
        ) and not self._get_is_excluded(function_name)
        if is_applicable:
            return self._get_raw_value_for_function(function_name)
        return None

    def serialize(self) -> dict:
        """Serialize for logging and debugging purposes."""
        if self.preserve:
            kwargs = {}
        else:
            kwargs = {
                "values": {
                    n: v
                    for n in self.target.names
                    if (v := self.get_value(n)) is not None
                },
            }

        return {
            "name": self.name,
            "only": self.restrictions,
            "except": self.exclusions,
            "preserve": self.preserve,
            **kwargs,
        }
