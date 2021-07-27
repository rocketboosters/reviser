"""Status and information data structures module."""
import dataclasses
import datetime
import typing

from reviser import utils


@dataclasses.dataclass(frozen=True)
class Status:
    """Data structure containing lambda status information."""

    state: typing.Optional[str]
    reason: typing.Optional[str]
    code: typing.Optional[str]

    def to_dict(self) -> dict:
        """Create a sparse dictionary containing only the non-None key/value pairs."""
        return {
            key: value
            for key in ["state", "reason", "code"]
            if (value := getattr(self, key)) is not None
        }


@dataclasses.dataclass(frozen=True)
class LambdaLayerReference:
    """Data structure containing reference information for a lambda layer."""

    response: dict

    @property
    def arn(self) -> typing.Optional[str]:
        """Get the versioned ARN of the layer."""
        return self.get("Arn")

    @property
    def unversioned_arn(self) -> typing.Optional[str]:
        """Get the layer's unversioned ARN."""
        if not self.arn:
            return None
        parts = self.arn.split(":")
        return ":".join(parts[:7])

    @property
    def name(self) -> str:
        """Get the name of the layer extracted from its ARN."""
        return (self.arn or "arn:???:?").rsplit(":", 2)[-2]

    @property
    def version(self) -> str:
        """Get the version for the layer extracted from its ARN."""
        return (self.arn or "arn:???:?").rsplit(":", 1)[-1]

    @property
    def size(self) -> typing.Optional[str]:
        """Get the human-readable size of the layer."""
        return utils.to_human_readable_size(self.response.get("CodeSize"))

    def get(self, key: str, default: typing.Any = None):
        """Fetch the value of the specified response key."""
        return (self.response or {}).get(key, default)


@dataclasses.dataclass(frozen=True)
class LambdaLayer:
    """Data structure for a `list_layer_version` AWS API response."""

    response: dict

    @property
    def arn(self) -> typing.Optional[str]:
        """Get the versioned ARN for the lambda layer."""
        return self.get("LayerVersionArn")

    @property
    def unversioned_arn(self) -> typing.Optional[str]:
        """Get the unversioned ARN for the lambda layer."""
        if unversioned := self.get("LayerArn"):
            return unversioned
        if not self.arn:
            return None
        parts = self.arn.split(":")
        return ":".join(parts[:7])

    @property
    def name(self) -> str:
        """Get the name of the layer extracted from its ARN."""
        return (self.arn or "arn:???:?").rsplit(":", 2)[-2]

    @property
    def version(self) -> typing.Optional[int]:
        """Get the version of the lambda layer."""
        return self.get("Version")

    @property
    def description(self) -> typing.Optional[str]:
        """Get user-specified description for the lambda layer."""
        return self.get("Description")

    @property
    def created(self) -> datetime.datetime:
        """Get the created at datetime for the lambda layer."""
        try:
            return datetime.datetime.fromisoformat(
                (self.response or {}).get("CreatedDate", "").rsplit("+", 1)[0]
            ).replace(microsecond=0)
        except Exception:
            return datetime.datetime(1900, 1, 1)

    @property
    def runtimes(self) -> typing.List[str]:
        """Get the supported runtimes for the lambda layer."""
        return self.get("CompatibleRuntimes") or []

    @property
    def size(self) -> typing.Optional[str]:
        """Get the MB size of the lambda layer in human-readable format."""
        return utils.to_human_readable_size(self.response.get("CodeSize"))

    def get(self, key: str, default: typing.Any = None):
        """Fetch the value of the specified response key."""
        return (self.response or {}).get(key, default)


@dataclasses.dataclass(frozen=True)
class FunctionAlias:
    """Data structure for lambda function aliases."""

    response: dict

    @property
    def arn(self) -> typing.Optional[str]:
        """Get the versioned ARN of the function alias."""
        return self.get("AliasArn")

    @property
    def name(self) -> typing.Optional[str]:
        """Get the name of the function alias."""
        return self.get("Name")

    @property
    def function_version(self) -> typing.Optional[str]:
        """Get the version associated with the function alias."""
        return self.get("FunctionVersion")

    @property
    def description(self) -> typing.Optional[str]:
        """Get the user-specified description of the alias if it exists."""
        return self.get("Description")

    @property
    def revision_id(self) -> typing.Optional[str]:
        """Get the revision ID associated with the alias."""
        return self.get("RevisionId")

    def get(self, key: str, default: typing.Any = None):
        """Fetch the value of the specified response key."""
        return (self.response or {}).get(key, default)


@dataclasses.dataclass(frozen=True)
class LambdaFunction:
    """Data structure for a `get_function_configuration` AWS API response."""

    response: dict
    alias_responses: typing.Optional[typing.List[dict]] = None

    @property
    def name(self) -> typing.Optional[str]:
        """Get the name of the lambda function."""
        return self.get("FunctionName")

    @property
    def aliases(self) -> typing.List["FunctionAlias"]:
        """Get the aliases that exist for the lambda function."""
        return [FunctionAlias(item) for item in (self.alias_responses or [])]

    @property
    def modified(self) -> typing.Optional[str]:
        """Get the last modified date string."""
        return self.get("LastModified")

    @property
    def description(self) -> typing.Optional[str]:
        """Get the user-specified description for the function if it exists."""
        return self.get("Description")

    @property
    def arn(self) -> typing.Optional[str]:
        """Get the ARN for the lambda function."""
        return self.get("FunctionArn")

    @property
    def runtime(self) -> typing.Optional[str]:
        """Get the enumerated runtime environment for the lambda function."""
        return self.get("Runtime")

    @property
    def role(self) -> typing.Optional[str]:
        """Get the exectuion role identifier attached to the lambda function."""
        return self.get("Role")

    @property
    def handler(self) -> typing.Optional[str]:
        """Get the function invocation entrypoint handler definition."""
        return self.get("Handler")

    @property
    def size(self) -> typing.Optional[str]:
        """Get the size of the lambda function's code bundle."""
        return utils.to_human_readable_size(self.get("CodeSize"))

    @property
    def timeout(self) -> typing.Optional[str]:
        """Get the length of the lambda function invocation timeout."""
        return "{}s".format(self.get("Timeout"))

    @property
    def memory(self) -> typing.Optional[str]:
        """Get the memory allocation limit for the lambda function."""
        return "{}MB".format(self.get("MemorySize"))

    @property
    def version(self) -> typing.Optional[str]:
        """Get the specific version of the lambda function of interest."""
        return self.get("Version")

    @property
    def environment(self) -> typing.Optional[str]:
        """Get the deployment stage environment name in which the lambda function."""
        return self.get("Environment")

    @property
    def revision_id(self) -> typing.Optional[str]:
        """Get the revision identifier for the lambda function."""
        return self.get("RevisionId")

    @property
    def layers(self) -> typing.List["LambdaLayerReference"]:
        """Get the layers attached to the lambda function."""
        return [LambdaLayerReference(item) for item in self.get("Layers") or []]

    @property
    def status(self) -> "Status":
        """Get the current status of the lambda function."""
        return Status(
            state=self.get("State"),
            reason=self.get("StateReason"),
            code=self.get("StateReasonCode"),
        )

    @property
    def update_status(self) -> "Status":
        """Get the last updated status for the lambda function."""
        return Status(
            state=self.get("LastUpdateStatus"),
            reason=self.get("LastUpdateStatusReason"),
            code=self.get("LastUpdateStatusReasonCode"),
        )

    def get_layer(
        self,
        name_or_arn: str,
    ) -> typing.Optional["LambdaLayerReference"]:
        """Fetch the layer reference if it exists for this function."""
        return next((v for v in self.layers if name_or_arn in (v.name, v.arn)), None)

    def get(self, key: str, default: typing.Any = None):
        """Fetch the value of the specified response key."""
        return (self.response or {}).get(key, default)


@dataclasses.dataclass(frozen=True)
class PublishedLayer:
    """Data structure containing information about a published layer."""

    #: Boto3 response returned by the layer publish operation.
    response: dict

    @property
    def arn(self) -> typing.Optional[str]:
        """Get the unversioned ARN for the layer."""
        return (self.response or {}).get("LayerArn")

    @property
    def version(self) -> typing.Optional[str]:
        """Get the version of the layer."""
        return (self.response or {}).get("Version")

    @property
    def versioned_arn(self) -> typing.Optional[str]:
        """Get the versioned ARN for the layer."""
        return (self.response or {}).get("LayerVersionArn")
