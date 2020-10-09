import argparse
import dataclasses
import datetime
import io
import shlex
import textwrap
import typing

import colorama
import prompt_toolkit
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
        self._prompt_session: typing.Optional[prompt_toolkit.PromptSession] \
            = None
        self.context = context
        self.selection = selection or definitions.Selection()
        self.shutdown = False
        #: Stores uncaught exceptions for reference when a command fails.
        self.error: typing.Optional[Exception] = None
        self._shell_completer = completions.ShellCompleter(self)
        self.command_queue: typing.List[str] = []
        #: Explicitly specifies if the command
        self._is_interactive: typing.Optional[bool] = None

    @property
    def is_active(self) -> bool:
        """
        Whether or not the shell should continue running or not as
        determined by whether or not it is running interactively or
        there are queued commands to still process.
        """
        return not self.shutdown and (
            bool(self.command_queue)
            or self._is_interactive
        )

    def execute(self, line: str):
        """Executes the specified input command."""
        if len(line.strip()) < 1:
            return False

        try:
            raw_args = shlex.split(line)
            action = raw_args[0]
            raw_args = raw_args[1:]
        except Exception as error:
            self.error = error
            templating.print_error(
                error=error,
                message=f'An error occurred parsing "{line}".',
            )
            return False

        action_module = commands.COMMANDS.get(action, None)

        print('\n')
        if action in ('?', 'help'):
            show_help()
            return False
        elif action == 'exit':
            self.shutdown = True
            return True
        elif action == 'shell':
            self._is_interactive = True
            return False
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

    def preloop(self):
        """Initialization before entering the command loop."""
        print('\n\nLambda Deployer Shell\n')
        colorama.init()

        history = InMemoryHistory()
        for line in self.command_history:
            history.append_string(line)

        try:
            self._prompt_session = prompt_toolkit.PromptSession(history=history)
        except io.UnsupportedOperation:
            self._is_interactive = False

        # If no queued commands have been specified at the start of the
        # loop, consider the loop to be running in interactive mode.
        self._is_interactive = not bool(self.command_queue)

    def postloop(self):
        """Teardown after exiting the command loop."""
        print('\n\n')
        colorama.deinit()
        self.shutdown = True
        self.command_queue = []
        self._is_interactive = False
        self._prompt_session = None

    def loop(self) -> typing.NoReturn:
        """Launches the command execution loop."""
        self.preloop()

        try:
            while not self.shutdown and self.is_active:
                if line := self.get_next_command():
                    self.execute(line)
        except KeyboardInterrupt:
            print('\n[INTERRUPTED]: Shutting down terminal.')
        except Exception as error:
            self.error = error
            templating.print_error(
                error=error,
                message='An unexpected command error occurred.',
            )

        self.postloop()

    def get_next_command(self) -> str:
        """
        Prompts user for input and returns that for command execution
        unless there is a queued command, in which case that is returned
        without a prompt instead.
        """
        prompt = f'{colorama.Fore.GREEN}>{colorama.Style.RESET_ALL} '

        if self.command_queue:
            line = self.command_queue.pop(0)
            print(f'{prompt}{line}')
        else:
            context = self.context
            templating.printer(
                'interactivity/shells/prompt.jinja2',
                profile=context.connection.session.profile_name or 'default',
                user_slug=context.connection.user_slug,
                selected=context.get_selected_targets(self.selection),
            )

            # noinspection PyTypeChecker
            line = self._prompt_session.prompt(
                message=ANSI(prompt),
                completer=self._shell_completer,
                complete_while_typing=True
            )

        return line.strip()


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
