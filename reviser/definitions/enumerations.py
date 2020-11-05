import enum
import typing
import sys


RUNTIME_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"


class TargetType(enum.Enum):
    """Enumerations of target types."""

    FUNCTION = "function"
    LAYER = "layer"


class DependencyType(enum.Enum):
    """Enumeration of dependency types, i.e. package managers."""

    PIP = "pip"
    PIPPER = "pipper"


class DefaultFile(enum.Enum):
    """Enumeration of default files for each dependency type."""

    PIP = "requirements.txt"
    PIPPER = "pipper.json"

    @classmethod
    def from_dependency_type(
        cls,
        dependency_type: typing.Union["DependencyType", str],
    ) -> typing.Optional["DefaultFile"]:
        """Lookup default file from a dependency type."""
        key = getattr(dependency_type, "value", dependency_type)
        return {
            DependencyType.PIP.value: DefaultFile.PIP,
            DependencyType.PIPPER.value: DefaultFile.PIPPER,
        }.get(key, None)