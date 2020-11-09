import argparse
import dataclasses
import pathlib
import typing

import yaml

from reviser.definitions import aws
from reviser.definitions import configurations
from reviser.definitions import enumerations
from reviser.definitions import selections


@dataclasses.dataclass(frozen=True)
class SelectedTargets:
    """
    Container for selected target results that have been filtered
    down from the entire list of targets stored in the parent
    configuration.
    """

    targets: typing.List["configurations.Target"]

    @property
    def function_targets(self) -> typing.List["configurations.Target"]:
        """List of function targets in the selection."""
        return [
            t
            for t in (self.targets or [])
            if t.kind == enumerations.TargetType.FUNCTION
        ]

    @property
    def layer_targets(self) -> typing.List["configurations.Target"]:
        """List of layer targets in the selection."""
        return [
            t for t in (self.targets or []) if t.kind == enumerations.TargetType.LAYER
        ]


@dataclasses.dataclass(frozen=True)
class Context:
    """Execution context for the current invocation."""

    arguments: argparse.Namespace
    configuration: "configurations.Configuration"
    connection: "aws.AwsConnection"

    @property
    def command_queue(self) -> typing.Optional[typing.List[str]]:
        """
        A list of commands to process within the execution shell
        and then exit instead of running interactively. These are
        loaded from `run:` configuration command group definitions
        in the loaded configuration object if a `--run` argument
        specifies the command group definition to execute. Otherwise,
        this will be None.
        """

        name = self.arguments.command_group_name
        return self.configuration.get_as_list("run", name) or None

    def get_selected_targets(
        self, selection: "selections.Selection"
    ) -> "SelectedTargets":
        """
        Creates a modified configuration filtered down to the specified
        selection criteria.
        """
        return SelectedTargets(
            targets=[
                ts
                for t in self.configuration.targets
                if (ts := dataclasses.replace(t, selection=selection)).names
            ]
        )

    @classmethod
    def load_from_file(
        cls,
        arguments: argparse.Namespace,
        path: typing.Union[str, pathlib.Path] = None,
        connection: "aws.AwsConnection" = None,
    ) -> "Context":
        """
        Loads a context from a configuration path target. Loads files
        using the `lambda.yaml` file by default as this is the preferred
        extension: https://yaml.org/faq.html
        """
        target = pathlib.Path(path or "./lambda.yaml").absolute()
        if target.is_dir():
            target = target.joinpath("lambda.yaml")

        aws_connection = connection or aws.AwsConnection()
        contents = target.read_text()
        return cls(
            arguments=arguments,
            configuration=configurations.Configuration(
                directory=target.parent,
                data=yaml.safe_load(contents),
                connection=aws_connection,
            ),
            connection=aws_connection,
        )
