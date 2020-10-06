import contextlib
import os
import pathlib
import shutil
import typing

import yaml

from lambda_deployer import definitions
from lambda_deployer import interactivity
from lambda_deployer.tests.scenarios.supports import mocking


class ScenarioRunner:
    """
    Execution runner for scenario testing, which works as a ContextManager
    within tests to carry out the specified scenario and return an object
    with results of the execution for assertion validation.
    """

    def __init__(self, slug: str):
        self.slug: str = slug
        self.scenario = yaml.safe_load(self.path.read_text())
        self.shell: typing.Optional['interactivity.Shell'] = None
        self.error: typing.Optional[Exception] = None
        self.patches: typing.Optional[mocking.Patches] = None

    @property
    def context(self) -> typing.Optional['definitions.Context']:
        """Context object created for the given scenario."""
        return self.shell.context if self.shell else None

    @property
    def configuration(self) -> typing.Optional['definitions.Configuration']:
        """Configuration object created for the given scenario."""
        return self.shell.context.configuration if self.shell else None

    @property
    def path(self) -> pathlib.Path:
        """Returns the scenario definition path."""
        return (
            pathlib.Path(__file__)
            .parent.parent
            .joinpath(self.slug)
            .absolute()
        )

    @property
    def directory(self) -> pathlib.Path:
        """Returns the directory in which the scenario definition resides."""
        return self.path.parent.absolute()

    def run(self) -> 'ScenarioRunner':
        """
        Executes the scenario, loading it if it has not already been loaded
        via a call to the load method.
        """
        start_directory = pathlib.Path()
        os.chdir(self.directory)
        arguments = self.scenario.get('arguments') or []

        try:
            with contextlib.ExitStack() as stack:
                # Create a stack object that will collect all of the
                # patches needed to isolate the tests from external
                # environments.
                self.patches = mocking.Patches(self, stack)
                # Process the shell commands specified in the scenario
                # in a non-interactive fashion.
                self.shell = interactivity.create_shell(arguments)
                self.shell.process(self.scenario['commands'])
        except Exception as error:
            self.error = error
        finally:
            os.chdir(start_directory)

        return self

    def cleanup(self) -> 'ScenarioRunner':
        """Cleans up temporary data after a test."""
        for t in self.shell.context.configuration.targets:
            if t.bundle_directory.exists():
                shutil.rmtree(t.bundle_directory)

            if t.bundle_zip_path.exists():
                os.remove(t.bundle_zip_path)

        return self

    def check_success(self):
        """Raises an error if the execution process raised an error."""
        error = self.error or getattr(self.shell, 'error', None)
        if error is not None:
            raise AssertionError('Command execution failed') from error

    def __enter__(self) -> 'ScenarioRunner':
        return self.run()

    def __exit__(self, exc_type, exc_val, exc_tb) -> typing.NoReturn:
        self.cleanup()
