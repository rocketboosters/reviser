import dataclasses
import pathlib
import typing
import uuid

from lambda_deployer.definitions import aws


@dataclasses.dataclass(frozen=True)
class Specification:
    """Base class for data loaded from the configuration."""

    #: Root directory in which the project being operated on resides.
    directory: pathlib.Path
    #: Specification data loaded from a configuration file that represents
    #: the data for this object.
    data: dict
    #: Connection object that represents the AWS session and account data
    #: associated with the context in which this configuration resides.
    connection: 'aws.AwsConnection'

    def __post_init__(self):
        """
        Add an internal uuid to the object's data dictionary after creation
        if it has not already been set.
        """
        if not self.has('_uuid'):
            self.update('_uuid', value=str(uuid.uuid4()), overwrite=False)

    @property
    def uuid(self) -> str:
        """An internal unique identifier for the configuration object."""
        return self.get('_uuid')

    def get(self, *args: str, default: typing.Any = None) -> typing.Any:
        """Fetches the value from the data dictionary."""
        value = self.data or {}
        for k in args:
            if k not in value:
                return default
            value = value[k]
        return value

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

    def serialize(self) -> dict:
        """Serializes the object for output representation."""
        return {}
