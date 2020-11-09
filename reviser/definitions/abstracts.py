import dataclasses
import pathlib
import typing
import uuid

from reviser.definitions import aws


@dataclasses.dataclass(frozen=True)
class DataWrapper:
    """Base class for data loaded and stored in a dynamic dictionary."""

    #: Data that represents the dynamic representation that is being
    #: wrapped by this object.
    data: dict

    def get(self, *args: str, default: typing.Any = None) -> typing.Any:
        """Fetches the value from the data dictionary."""
        value = self.data or {}
        for k in args:
            if k not in value:
                return default
            value = value[k]
        return value

    def get_first(
        self,
        *args: typing.Iterable[str],
        default: typing.Any = None,
    ) -> typing.Any:
        """
        Fetches the value from the data dictionary in the key-grouped
        order, returning the default value if none of the key-group args
        exist in the data dictionary.
        """
        found_args = next((a for a in args if self.has(*a)), None)
        if found_args is None:
            return default
        return self.get(*found_args, default=default)

    def get_as_list(
        self,
        *args: str,
        default: typing.Any = None,
    ) -> typing.List[typing.Any]:
        """
        Fetches the value from the data dictionary as a list.
        None values will be returned as an empty list. Values that are
        not lists will be wrapped into single-length lists when returned.
        If the nested key does not exist, the default will be returned
        instead, but if the key is explicitly defined as `null` an empty
        list is returned instead fo the default.
        """
        if self.has(*args):
            value = self.get(*args, default=default)
        else:
            value = default

        if value is None:
            return []

        if isinstance(value, list):
            return value
        return [value]

    def get_first_as_list(
        self,
        *args: typing.Iterable[str],
        default: typing.Any = None,
    ) -> typing.Any:
        """
        Fetches the value from the data dictionary in the key-grouped
        order, returning the default value if none of the key-group args
        exist in the data dictionary. If a match is found it will be returned
        as a list in the same fashion as the get_as_list function.
        """
        found_args = next((a for a in args if self.has(*a)), None)
        if found_args is None:
            return default
        return self.get_as_list(*found_args, default=default)

    def has(self, *args: str) -> bool:
        """Determines whether or not the nested key exists."""
        value = self.data or {}
        for k in args:
            if k not in value:
                return False
            value = value[k]
        return True

    def update(self, *args, value: typing.Any = None, overwrite: bool = False):
        """
        Updates the data object if the key is not found to be set already.
        """
        container = self.data or {}
        for k in args[:-1]:
            if k not in container:
                container[k] = {}
            container = container[k]

        if overwrite or args[-1] not in container:
            container[args[-1]] = value


@dataclasses.dataclass(frozen=True)
class Specification(DataWrapper):
    """Base class for data loaded from the configuration."""

    #: Root directory in which the project being operated on resides.
    directory: pathlib.Path
    #: Specification data loaded from a configuration file that represents
    #: the data for this object.
    data: dict
    #: Connection object that represents the AWS session and account data
    #: associated with the context in which this configuration resides.
    connection: "aws.AwsConnection"

    def __post_init__(self):
        """
        Add an internal uuid to the object's data dictionary after creation
        if it has not already been set.
        """
        if not self.has("_uuid"):
            self.update("_uuid", value=str(uuid.uuid4()), overwrite=False)

    @property
    def uuid(self) -> str:
        """An internal unique identifier for the configuration object."""
        return self.get("_uuid")

    def serialize(self) -> dict:
        """Serializes the object for output representation."""
        return {}
