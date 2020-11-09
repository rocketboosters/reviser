import re
import shlex
import typing

from prompt_toolkit import completion
from prompt_toolkit.document import Document

from reviser import commands
from reviser.interactivity import shells


class ShellCompleter(completion.Completer):
    """
    Implements a concrete Prompt Toolkit Completer class specific to the
    behaviors of the lambda deployer interactive shell.
    """

    def __init__(self, shell: "shells.Shell"):
        """Initializes the prompt toolkit custom auto-completer."""
        super(ShellCompleter, self).__init__()
        self.shell = shell
        self.document: typing.Optional[Document] = None
        self.event: typing.Optional[completion.CompleteEvent] = None
        self.args: typing.List[str] = []

    @property
    def action(self) -> str:
        """Currently specified root shell command action."""
        return self.args[0] if self.args else ""

    @property
    def last(self) -> str:
        """The last argument in the current line."""
        return self.args[-1] if self.args else ""

    def get_completions(
        self, document: Document, complete_event: completion.CompleteEvent
    ) -> typing.Generator[completion.Completion, None, None]:
        """
        Implements the completion process where the Prompt Toolkit document
        and complete event are used to determine the applicable completions
        for the current shell input state.
        """
        try:
            self.args = shlex.split(document.text.strip())
        except ValueError:
            return

        self.document = document
        self.event = complete_event

        for c in _get_completions(self):
            yield c


def _get_completions(
    completer: ShellCompleter,
) -> typing.List[completion.Completion]:
    """
    Creates a list of completions that should be returned by the
    ShellCompleter.get_completions function.
    """
    if not completer.document:
        return []

    if completer.document.text.lstrip().find(" ") == -1:
        return _get_action_completions(completer)

    return _get_command_completions(completer) + _get_state_completions(completer)


def _get_action_completions(completer: ShellCompleter):
    """Returns matching command actions for the current shell prompt state."""
    actions = list(commands.ALIASES.keys()) + list(commands.COMMANDS.keys())
    index = len(completer.action)
    matches = [a for a in actions if a.startswith(completer.action)]
    return [completion.Completion(m, start_position=-index) for m in matches]


def _get_command_completions(completer: ShellCompleter):
    """
    Returns completions specific to the currently specified command
    and/or sub-command in the shell. These completions are defined in the
    completer.configs module in the configs.COMMAND_COMPLETES dictionary.
    """
    command_module = commands.get_module(completer.action)
    get_completions = getattr(command_module, "get_completions", lambda x: [])
    options = get_completions(completer)
    index = len(completer.last)
    return [
        completion.Completion(item, start_position=-index)
        for item in options
        if item.startswith(completer.last)
    ]


def _get_state_completions(completer: ShellCompleter):
    """
    Returns completions based on the current state of the shell. At this
    point, this only includes lambda function/layer name completion.
    """
    index = len(completer.last)
    targets = [
        *completer.shell.context.configuration.function_targets,
        *completer.shell.context.configuration.layer_targets,
    ]
    names = [n for t in targets for n in t.names]

    pattern = re.compile(r"[\s_]+")
    names += list(
        {
            word
            for name in names
            for word in pattern.sub("-", name).split("-")
            if len(word) > 2
        }
    )

    return [
        completion.Completion(n, start_position=-index)
        for n in names
        if n.startswith(completer.last)
    ]
