import contextlib
import pathlib
import typing
from unittest.mock import MagicMock
from unittest.mock import patch

import lobotomy

from reviser.tests.scenarios.supports import running


class Patches:
    """
    Wrapper class for patching external system interfaces within the
    reviser package for general scenario testing.
    """

    def __init__(
        self,
        runner: "running.ScenarioRunner",
        stack: contextlib.ExitStack,
    ):
        self.runner = runner
        self.stack = stack
        self.time_sleep = self._patch("time.sleep")
        self.boto3_session = self._patch_boto_session()
        self.install_pip_package = self._patch_pip_install_package()
        self.install_pipper_package = self._patch_pipper_install_package()
        self.input = self._patch_input()

    def _add(self, context_manager):
        """
        Add the context manager to the exit stack stored within this object.
        These context managers will be exited when the `with` block in which
        the stack has been entered is exited.
        """
        return self.stack.enter_context(context_manager)

    def _patch(self, target, *args, **kwargs) -> MagicMock:
        """Add a patch to the context manager stack."""
        return self._add(patch(target, *args, **kwargs))

    def _patch_input(self) -> MagicMock:
        """
        Patches the builtin input() function so that it returns the value(s)
        specified in the scenario.
        """
        mock = self._patch("builtins.input")
        values = self.runner.scenario.get_first(["inputs"], ["input"])
        if isinstance(values, str):
            mock.return_value = values
        elif values:
            mock.side_effect = values
        return mock

    def _patch_boto_session(self) -> MagicMock:
        """Creates a patch for boto3.Session() constructors."""
        lobotomized = lobotomy.Lobotomy(self.runner.scenario.get("lobotomy") or {})
        return self._patch("boto3.Session", new=lobotomized)

    def _patch_pip_install_package(self) -> MagicMock:
        """Creates a patch for installing pip packages."""
        mock = self._patch("reviser.bundling._installer._install_pip_package")
        mock.side_effect = self._mock_pip_install_package
        return mock

    def _patch_pipper_install_package(self) -> MagicMock:
        """Creates a patch for installing pipper packages."""
        mock = self._patch("reviser.bundling._installer._install_pipper_package")
        mock.side_effect = self._mock_pipper_install_package
        return mock

    @classmethod
    def _mock_pip_install_package(cls, name: str, site_packages: pathlib.Path):
        """Mock function for pipper package installation."""
        site_packages.joinpath(name).write_text("pip-installed-package")
        print(f'[MOCK]: Installed pip package "{name}"')

    @classmethod
    def _mock_pipper_install_package(
        cls,
        name: str,
        site_packages: pathlib.Path,
        *args,
        **kwargs,
    ):
        """Mock function for pipper package installation."""
        site_packages.joinpath(name).write_text("pipper-installed-package")
        print(f'[MOCK]: Installed pipper package "{name}"')


class AwsClient:
    """
    Mocks AWS boto3.client behaviors that pull response data from
    the loaded scenario dictionary.
    """

    def __init__(self, scenario: dict):
        """Populate with the loaded scenario data."""
        self._scenario = scenario
        self._identifier: typing.Optional[str] = None
        self._calls: typing.List[dict] = []
        self.exceptions = MagicMock()
        self.exceptions.ResourceNotFoundException = ValueError

    def __call__(self, identifier: str, *args, **kwargs):
        """Simulates the creation of a boto3.client."""
        self._identifier = identifier
        return self

    def _get_response(self, item: str):
        """Retrieves the response for the given object."""
        aws = self._scenario.get("aws") or {}
        client_data = aws.get(self._identifier) or {}
        response = client_data.get(item) or {}
        if isinstance(response, list):
            response = response.pop(0)
        return response

    def __getattr__(self, item: str):
        """
        Retrieves response data for the given client call from the
        scenario data that defines the execution.
        """
        response = self._get_response(item)
        return lambda *args, **kwargs: response

    def get_paginator(self, item: str):
        """Mocks a single-page paginator response."""
        paginator = MagicMock()
        paginator.paginate.return_value = [self._get_response(item)]
        return paginator
