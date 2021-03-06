"""Shell data structures and functionality module."""
import argparse
import dataclasses
import datetime
import io
import shlex
import typing

import colorama
import prompt_toolkit
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory

import reviser
from reviser import commands
from reviser import definitions
from reviser import templating
from reviser.interactivity import completions


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
    shell: "Shell"
    result: typing.Optional["ExecutionResult"] = None

    executed_at: datetime.datetime = dataclasses.field(
        init=False,
        default_factory=lambda: datetime.datetime.utcnow(),
    )

    @property
    def timestamp(self) -> str:
        """Get a string representation of the created at datetime."""
        return self.executed_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def finalize(
        self,
        status: str,
        message: str = None,
        info: dict = None,
        data: dict = None,
        echo: bool = False,
    ) -> "Execution":
        """Copy this execution and populate it with the result."""
        return dataclasses.replace(
            self,
            result=ExecutionResult(
                status=(status or "???").upper(),
                message=message or "???",
                info=info,
                data=data,
            ),
        ).echo_if(echo)

    def echo(self) -> "Execution":
        """Echo the result if set for display to the console."""
        if self.result:
            templating.printer(
                "interactivity/shells/execution_result.jinja2",
                result=self.result,
            )
        return self

    def echo_if(self, condition) -> "Execution":
        """Echo the result if set for display to the console."""
        if bool(condition):
            return self.echo()
        return self


class Shell:
    """
    Reviser Shell wrapper class.

    Interactive lambda deployer interactivity class responsible for managing
    the state and interactivity for the interface.
    """

    def __init__(
        self,
        context: "definitions.Context",
        selection: "definitions.Selection" = None,
    ):
        """Create a new shell for queued and/or interactive execution."""
        self.command_history: typing.List[str] = []
        self.execution_history: typing.List["Execution"] = []
        self._prompt_session: typing.Optional[prompt_toolkit.PromptSession] = None
        self.context = context
        self.selection = selection or definitions.Selection()
        self.shutdown = False
        #: Stores uncaught exceptions for reference when a command fails.
        self.error: typing.Optional[Exception] = None
        self._shell_completer = completions.ShellCompleter(self)
        self.command_queue: typing.List[str] = []
        #: Explicitly specifies if the shell should be running in
        #: interactive mode where it prompts users for input on the
        #: terminal.
        self._is_interactive: typing.Optional[bool] = None

    @property
    def is_interactive(self) -> typing.Optional[bool]:
        """Get whether the shell is running as an interactive command loop."""
        return self._is_interactive

    @is_interactive.setter
    def is_interactive(self, value: typing.Optional[bool]):
        """Set the is_interactive property."""
        if value and self._prompt_session is None:
            if not self._create_prompt_session():
                raise RuntimeError("Terminal connectivity not supported.")

        self._is_interactive = value

    @property
    def is_active(self) -> bool:
        """
        Get Whether the shell should continue running.

        This is determined by whether or not it is running interactively or there are
        queued commands to still process.
        """
        return not self.shutdown and bool(
            bool(self.command_queue) or self.is_interactive
        )

    def _create_prompt_session(self) -> bool:
        """
        Attempt creation of a session for interactive command execution.

        :return:
            Whether that session was successfully created. It will fail when executed
            in non-interactive environments that do no support user input and return
            False.
        """
        history = InMemoryHistory()
        for line in self.command_history:
            history.append_string(line)

        try:
            self._prompt_session = prompt_toolkit.PromptSession(history=history)
        except io.UnsupportedOperation:
            self._is_interactive = False
            return False

        return True

    def _setup(self):
        """Initialize before entering the command loop."""
        templating.printer(
            "interactivity/shells/splash.jinja2",
            version=reviser.__version__,
        )
        print("\n\n")
        colorama.init()

        # If no queued commands have been specified at the start of the
        # loop, consider the loop to be running in interactive mode.
        self.is_interactive = not bool(self.command_queue)

    def run(self) -> None:
        """Launch the command execution loop."""
        self._setup()

        try:
            while not self.shutdown and self.is_active:
                if line := self._get_next_command():
                    should_error_exit = execute(self, line)
                    self.shutdown = bool(self.shutdown or should_error_exit)

                if self.error and not self.is_interactive:
                    # Abort if an error was encountered in non-interactive mode.
                    return
        except KeyboardInterrupt:
            print("\n[INTERRUPTED]: Shutting down terminal.")
        except Exception as error:
            if self.error is None:
                # If the error was not already caught, catch it now.
                self.error = error
                templating.print_error(
                    error=error,
                    message="An unexpected command error occurred.",
                )
        finally:
            self._teardown()

    def _teardown(self):
        """Teardown after exiting the command loop."""
        print("\n\n")
        colorama.deinit()
        self.shutdown = True
        self.command_queue = []
        self.is_interactive = False
        self._prompt_session = None

    def _get_next_command(self) -> str:
        """
        Prompt user for input and returns that for command execution.

        However, if there is a queued command that is returned without a prompt instead.
        """
        context = self.context
        configuration = context.configuration
        templating.printer(
            "interactivity/shells/prompt.jinja2",
            profile=context.connection.session.profile_name or "default",
            region=configuration.aws_region,
            user_slug=context.connection.user_slug,
            selected=context.get_selected_targets(self.selection),
        )
        prompt = f"{colorama.Fore.GREEN}>{colorama.Style.RESET_ALL} "

        if self.command_queue:
            line = self.command_queue.pop(0)
            print(f"{prompt}{line}")
        elif self._prompt_session is not None:
            # noinspection PyTypeChecker
            line = self._prompt_session.prompt(
                message=ANSI(prompt),
                completer=self._shell_completer,
                complete_while_typing=True,
            )
        else:
            line = ""

        return line.strip()


def execute(shell: "Shell", line: str) -> bool:
    """
    Execute the specified input command within the given shell environment.

    :return:
        True if an error was encountered during execution and the shell should be
        shutdown as a consequence, which happens in non-interactive mode.
    """
    # Continue if interactive, but die if non-interactive.
    should_error_exit = not shell.is_interactive

    if len(line.strip()) < 1:
        return should_error_exit

    try:
        raw_args = shlex.split(line)
        action = raw_args[0]
        raw_args = raw_args[1:]
    except Exception as error:
        shell.error = error
        templating.print_error(
            error=error,
            message=f'An error occurred parsing "{line}".',
        )
        return should_error_exit

    action_module = commands.get_module(action)

    print("\n")
    if action_module is None:
        templating.print_error(f'Unknown command "{action}".')
        return should_error_exit

    try:
        try:
            parser = argparse.ArgumentParser(prog=action)
            action_module.populate_subparser(parser)
            args = vars(parser.parse_args(raw_args))
        except SystemExit:
            return should_error_exit

        execution = action_module.run(Execution(action, args, shell))
        shell.execution_history.append(execution)
        shell.command_history.append(line)
        return False
    except Exception as error:
        shell.error = error
        templating.print_error(
            error=error,
            message="An unexpected command error occurred.",
        )
        return should_error_exit
    finally:
        print("\n")
