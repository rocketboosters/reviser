import contextlib
from unittest.mock import MagicMock
from unittest.mock import patch

from lambda_deployer.tests.scenarios.supports import running


class Patches:
    """
    Wrapper class for patching external system interfaces within the
    lambda_deployer package for general scenario testing.
    """

    def __init__(
            self,
            runner: 'running.ScenarioRunner',
            stack: contextlib.ExitStack,
    ):
        self.runner = runner
        self.stack = stack
        self.boto3_session: MagicMock = self._add_boto_session()
        self.time_sleep: MagicMock = self._patch('time.sleep')
        self.install_pip_package: MagicMock = self._patch(
            'lambda_deployer.bundling._installer._install_pipper_package'
        )
        self.install_pipper_package: MagicMock = self._patch(
            'lambda_deployer.bundling._installer._install_pip_package'
        )

    def _add(self, context_manager):
        """
        Add the context manager to the exit stack stored within this object.
        These context managers will be exited when the `with` block in which
        the stack has been entered is exited.
        """
        return self.stack.enter_context(context_manager)

    def _patch(self, target, *args, **kwargs):
        """Add a patch to the context manager stack."""
        return self._add(patch(target, *args, **kwargs))

    def _add_boto_session(self) -> MagicMock:
        """Creates a patch for boto3.Session() constructors."""
        aws = self.runner.scenario.get('aws') or {}
        session = MagicMock(region_name=aws.get('region_name', 'us-east-1'))
        mock_client = AwsClient(self.runner.scenario)
        session.client = mock_client
        return self._patch('boto3.Session', return_value=session)


class AwsClient:
    """
    Mocks AWS boto3.client behaviors that pull response data from
    the loaded scenario dictionary.
    """

    def __init__(self, scenario: dict):
        """Populate with the loaded scenario data."""
        self._scenario = scenario
        self._identifier = None
        self._calls = []

    def __call__(self, identifier: str, *args, **kwargs):
        """Simulates the creation of a boto3.client."""
        self._identifier = identifier
        return self

    def __getattr__(self, item: str):
        """
        Retrieves response data for the given client call from the
        scenario data that defines the execution.
        """
        aws = self._scenario.get('aws') or {}
        client_data = aws.get(self._identifier) or {}
        response = client_data.get(item) or {}
        if isinstance(response, list):
            response = response.pop(0)
        return lambda *args, **kwargs: response


def create_session(scenario: dict):
    """
    Creates a mock boto3 session that will use scenario data to
    respond to client requests.
    """
    aws = scenario.get('aws') or {}
    session = MagicMock(region_name=aws.get('region_name', 'us-east-1'))
    mock_client = AwsClient(scenario)
    session.client = mock_client
    return session
