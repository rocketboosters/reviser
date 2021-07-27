"""Configurations definitions package containing data structures and IO for configs."""
import dataclasses
import typing

from reviser import utils
from reviser.definitions import abstracts
from reviser.definitions import enumerations
from .bundling import Bundle  # noqa: F401
from .depending import Dependency  # noqa: F401
from .depending import PipDependency  # noqa: F401
from .depending import PipperDependency  # noqa: F401
from .depending import PoetryDependency  # noqa: F401
from .enviromentals import EnvironmentVariable  # noqa: F401
from .layering import AttachedLayer  # noqa: F401
from .targeting import Target  # noqa: F401


@dataclasses.dataclass(frozen=True)
class Configuration(abstracts.Specification):
    """Configuration Settings data structure."""

    @property
    def targets(self) -> typing.List["Target"]:
        """Get the duild and deploy targets."""
        return [
            Target(
                directory=self.directory,
                data=item,
                connection=self.connection,
                configuration=self,
            )
            for item in self.get("targets", default=[])
        ]

    @property
    def function_targets(self) -> typing.List["Target"]:
        """Get the build and deploy function targets."""
        return [t for t in self.targets if t.kind == enumerations.TargetType.FUNCTION]

    @property
    def layer_targets(self) -> typing.List["Target"]:
        """Get the build and deploy layer targets."""
        return [t for t in self.targets if t.kind == enumerations.TargetType.LAYER]

    @property
    def bucket(self) -> typing.Optional[str]:
        """Retrieve the bucket to use for uploading to S3."""
        return utils.get_matching_bucket(
            buckets=self.get_first(["buckets"], ["bucket"]),
            aws_region=self.aws_region,
            aws_account_id=self.connection.aws_account_id,
        )

    @property
    def aws_region(self) -> str:
        """Get the name of the region that this configuration is targeting."""
        return self.get("region") or self.connection.session.region_name or "us-east-1"

    def get_function(self, name: str) -> typing.Optional["Target"]:
        """Retrieve the target with the matching name."""
        return next((t for t in self.function_targets if name in t.names), None)

    def get_layer(self, name: str) -> typing.Optional["Target"]:
        """Retrieve the target with the matching name."""
        return next((t for t in self.layer_targets if name in t.names), None)

    def serialize(self) -> dict:
        """Serialize the object for output representation."""
        return {
            "bucket": self.bucket,
            "run": self.get("run"),
            "region": self.aws_region,
            "function_targets": [t.serialize() for t in self.function_targets],
            "layer_targets": [t.serialize() for t in self.layer_targets],
        }
