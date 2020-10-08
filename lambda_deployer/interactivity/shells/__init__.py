import argparse
import dataclasses
import datetime
import shlex
import textwrap
import typing

import colorama
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory

from lambda_deployer import commands
from lambda_deployer import definitions
from lambda_deployer import templating
from lambda_deployer.interactivity import completions


@dataclasses.dataclass(frozen=True)
class ExecutionResult:
    """Data structure for shell command execution responses."""

    status: str
    message: str
    info: typing.Optional[dict] = None
    data: typing.Optional[dict] = None


@dataclasses.dataclass(frozen=True)
class Execution:
    """Data structure for a shell command execution."""

    action: str
    args: dict
    shell: 'Shell'
    result: typing.Optional['ExecutionResult'] = None

    executed_at: datetime.datetime = dataclasses.field(
        init=False,
        default_factory=lambda: datetime.datetime.utcnow(),
    )

    @property
    def timestamp(self) -> str:
        """A string representation of the created at datetime."""
        return self.executed_at.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    def finalize(
            self,
            status: str,
            message: str = None,
            info: dict = None,
            data: dict = None,
            echo: bool = False,
    ) -> 'Execution':
        """Copy this execution and populate it with the result."""
        return dataclasses.replace(self, result=ExecutionResult(
            status=(status or '???').upper(),
            message=message,
            info=info,
            data=data,
        )).echo_if(echo)

    def echo(self) -> 'Execution':
        """Echoes the result if set for display to the console."""
        if self.result:
            templating.printer(
                'interactivity/shells/execution_result.jinja2',
                result=self.result,
            )
        return self

    def echo_if(self, condition) -> 'Execution':
        """Echoes the result if set for display to the console."""
        if bool(condition):
            return self.echo()
        return self


class Shell:
    """
    Interactive lambda deployer interactivity class responsible for managing
    the state and interactivity for the interface.
    """

    def __init__(
            self,
            context: 'definitions.Context',
            selection: 'definitions.Selection' = None,
    ):
        """Creates a new interactivity."""
        self.command_history: typing.List[str] = []
        self.execution_history: typing.List['Execution'] = []
        self._prompt_session: typing.Optional[PromptSession] = None
        self.context = context
        self.selection = selection or definitions.Selection()
        self.shutdown = False
        #: Stores uncaught exceptions for reference when a command fails.
        self.error: typing.Optional[Exception] = None

    def execute(self, line: str):
        """Executes the specified input command."""
        if len(line.strip()) < 1:
            return False

        raw_args = shlex.split(line)
        action = raw_args[0]
        raw_args = raw_args[1:]

        action_module = commands.COMMANDS.get(action, None)

        print('\n')
        if action in ('?', 'help'):
            show_help()
            return False
        elif action == 'exit':
            self.shutdown = True
            return True
        elif action_module is None:
            templating.print_error(f'Unknown command "{action}".')
            return False

        try:
            try:
                parser = argparse.ArgumentParser(prog=action)
                action_module.populate_subparser(parser)
                args = vars(parser.parse_args(raw_args))
            except SystemExit:
                return False

            execution = Execution(action, args, self)
            self.execution_history.append(action_module.run(execution))
            self.command_history.append(line)
        except Exception as error:
            self.error = error
            templating.print_error(
                error=error,
                message='An unexpected command error occurred.',
            )
            return False
        finally:
            print('\n')

    def preloop(self, interactive: bool = True):
        """Initialization before entering the interactive command loop."""
        print('\n\nLambda Deployer Interactive Shell\n')
        colorama.init()

        if interactive:
            history = InMemoryHistory()
            for line in self.command_history:
                history.append_string(line)

            self._prompt_session = PromptSession(history=history)

    def postloop(self):
        """Teardown after exiting the command loop."""
        print('\n\n')
        colorama.deinit()
        self.shutdown = True

    def loop(self):
        """Launches the interactive loop."""
        return_code = 0
        self.preloop()
        shell_completer = completions.ShellCompleter(self)
        try:
            while not self.shutdown:
                # noinspection PyTypeChecker
                line: str = self._prompt_session.prompt(
                    message=ANSI(generate_prompt(self)),
                    completer=shell_completer,
                    complete_while_typing=True
                )
                if line.strip():
                    self.execute(line)
        except KeyboardInterrupt:
            print('\n[INTERRUPTED]: Shutting down terminal.')
        except Exception as error:
            self.error = error
            templating.print_error(
                error=error,
                message='An unexpected command error occurred.',
            )
            return_code = 1

        self.postloop()
        return return_code

    def process(self, command_queue: typing.List[str]) -> typing.NoReturn:
        """
        Emulates the command loop, except that instead of relying on user
        input, the commands are supplied as the `command_queue` argument. If
        a command fails critically for any reason, the exception will be
        raised to be handled outside of this loop.

        :param command_queue:
            A list of one or more commands to execute.
        """
        self.preloop(interactive=False)

        try:
            for line in command_queue:
                self.execute(line.strip())
                if self.shutdown:
                    raise RuntimeError(f'[SHUTDOWN]: Caused by "{line}"')
        except Exception as error:
            self.error = error
            templating.print_error(
                error=error,
                message='An unexpected command error occurred.',
            )
            self.postloop()
            raise

        self.postloop()


def generate_prompt(shell: 'Shell') -> str:
    """
    Returns an ANSI-colored prompt for user input display based
    on the current shell state and local environment.
    """
    templating.printer(
        'interactivity/shells/prompt.jinja2',
        profile=shell.context.connection.session.profile_name or 'default',
        user_slug=shell.context.connection.user_slug,
        selected=shell.context.get_selected_targets(shell.selection),
    )
    return f'{colorama.Fore.GREEN}>{colorama.Style.RESET_ALL} '


def show_help():
    """Shows commands help for all available commands."""
    for key, command_module in commands.COMMANDS.items():
        print('{}\n{}'.format(
            key,
            textwrap.indent(
                textwrap.dedent(command_module.__doc__).strip(),
                prefix='   ',
            ),
        ))
