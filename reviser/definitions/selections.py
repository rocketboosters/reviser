"""Selection data structures module."""
import dataclasses
import typing


@dataclasses.dataclass(frozen=True)
class Selection:
    """Data structure defining a selection of targets on which to act."""

    bundle_all: bool = True
    function_needles: typing.List[str] = dataclasses.field(default_factory=lambda: [])
    function_names: typing.List[str] = dataclasses.field(default_factory=lambda: [])
    layer_needles: typing.List[str] = dataclasses.field(default_factory=lambda: [])
    layer_names: typing.List[str] = dataclasses.field(default_factory=lambda: [])
