"""Image configuration data structures and IO module."""

import dataclasses
import typing

from reviser.definitions import abstracts
from reviser.definitions import configurations
from reviser.definitions import enumerations


@dataclasses.dataclass(frozen=True)
class Image(abstracts.Specification):
    """Define the function image config that will be generated."""

    target: "configurations.Target"

    @property
    def configured(self) -> bool:
        """Determine if URIs are configured."""
        return (
            bool(self.get("uri"))
            and self.target.kind == enumerations.TargetType.FUNCTION
        )

    def get_region_uri(self, region: str) -> typing.Optional[str]:
        """Get the uri of the image to use in the lambda."""
        uri = self.get("uri")
        if isinstance(uri, dict):
            return uri.get(region)
        return uri

    @property
    def entrypoint(self) -> typing.Optional[typing.List[str]]:
        """
        Get the custom entrypoint of the image.

        If not specified the default of the image will be used.
        """
        custom_entrypoint = self.get("entrypoint")
        if isinstance(custom_entrypoint, str):
            custom_entrypoint = [custom_entrypoint]
        return custom_entrypoint if self.configured is not None else None

    @property
    def cmd(self) -> typing.Optional[typing.List[str]]:
        """
        Get the custom command of the image.

        If not specified the default of the image will be used.
        """
        custom_cmd = self.get("cmd")
        if isinstance(custom_cmd, str):
            custom_cmd = [custom_cmd]
        return custom_cmd if self.configured is not None else None

    @property
    def workingdir(self) -> typing.Optional[str]:
        """
        Get the custom workdir of the image.

        If not specified the default of the image will be used.
        """
        return self.get("workingdir") if self.configured is not None else None

    def serialize(self) -> dict:
        """Serialize the object for output representation."""
        return {
            "uri_map": self.get("uri"),
            "entrypoint": self.entrypoint,
            "cmd": self.cmd,
            "workingdir": self.workingdir,
        }
