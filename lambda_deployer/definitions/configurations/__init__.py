import dataclasses
import typing

from lambda_deployer.definitions import abstracts
from lambda_deployer.definitions import enumerations
from .bundling import Bundle
from .depending import Dependency
from .depending import PipDependency
from .depending import PipperDependency
from .enviromentals import EnvironmentVariable
from .layering import AttachedLayer
from .targeting import Target


@dataclasses.dataclass(frozen=True)
class Configuration(abstracts.Specification):
    """Configuration Settings data structure."""

    @property
    def targets(self) -> typing.List['Target']:
        """Build and deploy targets."""
        return [
            Target(
                directory=self.directory,
                data=item,
                connection=self.connection,
                configuration=self,
            )
            for item in self.get('targets', default=[])
        ]

    @property
    def function_targets(self) -> typing.List['Target']:
        """Build and deploy function targets."""
        return [
            t for t in self.targets
            if t.kind == enumerations.TargetType.FUNCTION
        ]

    @property
    def layer_targets(self) -> typing.List['Target']:
        """Build and deploy layer targets."""
        return [
            t for t in self.targets
            if t.kind == enumerations.TargetType.LAYER
        ]

    @property
    def bucket(self) -> typing.Optional[str]:
        """Retrieves the bucket to use for uploading to S3."""
        buckets = self.get(
            'buckets',
            default=self.get('bucket', default=None),
        )

        if not buckets:
            return None

        if isinstance(buckets, str):
            return buckets

        return buckets[self.connection.aws_account_id]

    @property
    def aws_region(self) -> str:
        """Name of the region that this configuration is targeting."""
        return (
            self.get('region')
            or self.connection.session.region_name
            or 'us-east-1'
        )

    def get_function(self, name: str) -> typing.Optional['Target']:
        """Retrieves the target with the matching name."""
        return next((t for t in self.function_targets if name in t.names), None)

    def get_layer(self, name: str) -> typing.Optional['Target']:
        """Retrieves the target with the matching name."""
        return next((t for t in self.layer_targets if name in t.names), None)

    def serialize(self) -> dict:
        """Serializes the object for output representation."""
        return {
            'bucket': self.bucket,
            'region': self.aws_region,
            'function_targets': [t.serialize() for t in self.function_targets],
            'layer_targets': [t.serialize() for t in self.layer_targets],
        }
