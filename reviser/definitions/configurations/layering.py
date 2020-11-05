import dataclasses
import typing
import fnmatch

from reviser.definitions import abstracts
from reviser.definitions import configurations


@dataclasses.dataclass(frozen=True)
class AttachedLayer(abstracts.Specification):
    """Data structure for layer attachments to function targets."""

    target: "configurations.Target"

    @property
    def name(self) -> str:
        """Name of the layer attachment."""
        value = self.get("name", default=self.get("arn", default=""))
        if not value.startswith("arn:aws:lambda:"):
            return value.split(":")[0]
        return value.split(":")[6]

    @property
    def version(self) -> typing.Optional[int]:
        """Explicit version of the layer for the attachment."""
        if (version := self.get("version")) is not None:
            return int(version)

        value = self.get("arn", default="")
        try:
            return int(value.split(":")[-1])
        except ValueError:
            pass

        value = self.get("name", default="")
        try:
            return int(value.split(":")[-1])
        except ValueError:
            return None

    @property
    def arn(self) -> str:
        """Fully qualified ARN for the layer attachment."""
        if (arn := self.get("arn")) is not None:
            return arn

        value: str = self.get("name", default="")
        if value.startswith("arn:aws:lambda:"):
            return value

        account_id = self.connection.aws_account_id
        region = self.target.aws_region
        name = self.name
        arn = f"arn:aws:lambda:{region}:{account_id}:layer:{name}"
        if (version := self.version) is not None:
            return f"{arn}:{version}"
        return arn

    @property
    def restrictions(self) -> typing.List[str]:
        """Only attach to functions matching values in this list."""
        return self.get_as_list("only", default=[]) or []

    @property
    def exclusions(self) -> typing.List[str]:
        """Don't attach to functions matching values in this list."""
        return self.get_as_list("except", default=[]) or []

    def is_attachable(self, function_name: str) -> bool:
        """
        Specifies whether or not to attach this layer to the function
        with the specified name.
        """
        includer = (
            True
            for pattern in self.restrictions
            if fnmatch.fnmatch(function_name, pattern)
        )
        if not next(includer, not self.restrictions):
            return False

        excluder = (False for e in self.exclusions if fnmatch.fnmatch(function_name, e))
        return next(excluder, True)

    def serialize(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "arn": self.arn,
            "only": self.restrictions,
            "except": self.exclusions,
            "functions": [n for n in self.target.names if self.is_attachable(n)],
        }
