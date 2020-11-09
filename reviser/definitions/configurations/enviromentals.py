import dataclasses
import typing
import fnmatch

from reviser.definitions import abstracts
from reviser.definitions import configurations


@dataclasses.dataclass(frozen=True)
class EnvironmentVariable(abstracts.Specification):
    """Data structure for function environment variables."""

    target: "configurations.Target"

    @property
    def name(self) -> str:
        """Name for the environment variable."""
        if (name := self.get("name")) is not None:
            return name

        if (arg := self.get("arg")) is not None:
            return arg.split("=")[0]

        return "unknown-environment-variable"

    @property
    def preserve(self) -> bool:
        """
        Specifies whether or not the environment variable should be
        preserved, such that changes or settings here will not be
        updated. Useful for variables that are managed or assigned by
        other systems.
        """
        return self.get("preserve", default=False)

    @property
    def restrictions(self) -> typing.List[str]:
        """Only attach to functions matching values in this list."""
        value = self.get("only", default=[])
        if isinstance(value, str):
            return [value]
        return value

    @property
    def exclusions(self) -> typing.List[str]:
        """Don't attach to functions matching values in this list."""
        value = self.get("except", default=[])
        if isinstance(value, str):
            return [value]
        return value

    def get_value(self, function_name: str) -> typing.Optional[str]:
        """
        Retrieves the value of the environment variable for the given
        function name.
        """
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

        includer = (
            True
            for pattern in self.restrictions
            if fnmatch.fnmatch(function_name, pattern)
        )
        if not next(includer, not self.restrictions):
            return None

        excluder = (value for e in self.exclusions if fnmatch.fnmatch(function_name, e))
        return next(excluder, value)

    def serialize(self) -> dict:
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
