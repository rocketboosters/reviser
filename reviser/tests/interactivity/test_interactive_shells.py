from unittest.mock import MagicMock
from unittest.mock import patch

from reviser import interactivity
import pytest

ROOT = "reviser.interactivity.shells"


@patch(f"{ROOT}.prompt_toolkit.PromptSession")
def test_interactive_command_execution(prompt_session_init: MagicMock):
    """Should execute the help and exit commands successfully."""
    ps = MagicMock()
    ps.prompt.side_effect = [" ", "?", "shell", "exit"]
    prompt_session_init.return_value = ps

    context = MagicMock()
    shell = interactivity.Shell(context)
    shell.run()

    assert shell.execution_history[0].result.status == "HELPED"
    assert shell.execution_history[1].result.status == "SHELL"
    assert shell.execution_history[2].result.status == "EXIT"


@patch(f"{ROOT}.prompt_toolkit.PromptSession")
def test_unknown_command(prompt_session_init: MagicMock):
    """Should handle unknown commands without uncaught errors."""
    ps = MagicMock()
    ps.prompt.side_effect = ["foo", "exit"]
    prompt_session_init.return_value = ps

    context = MagicMock()
    shell = interactivity.Shell(context)
    shell.run()

    assert shell.execution_history[0].result.status == "EXIT"


@patch(f"{ROOT}.prompt_toolkit.PromptSession")
def test_keyboard_interrupt(prompt_session_init: MagicMock):
    """Should handle keyboard interrupt gracefully."""
    ps = MagicMock()
    ps.prompt.side_effect = KeyboardInterrupt
    prompt_session_init.return_value = ps

    context = MagicMock()
    shell = interactivity.Shell(context)
    shell.run()

    assert len(shell.execution_history) == 0


def test_non_interactive_error():
    """Should raise errors when running in non-interactive mode."""
    context = MagicMock()
    shell = interactivity.Shell(context)
    shell.command_queue = ["foo"]
    shell._get_next_command = MagicMock(side_effect=ValueError("whoops"))

    with pytest.raises(ValueError):
        shell.run()

    assert len(shell.execution_history) == 0


@patch(f"{ROOT}.prompt_toolkit.PromptSession")
def test_unknown_error(prompt_session_init: MagicMock):
    """Should handle unknown command errors gracefully."""
    ps = MagicMock()
    ps.prompt.side_effect = ValueError("foo")
    prompt_session_init.return_value = ps

    context = MagicMock()
    shell = interactivity.Shell(context)
    shell.run()

    assert shell.error
    assert len(shell.execution_history) == 0


@patch(f"{ROOT}.prompt_toolkit.PromptSession")
def test_execution_parsing_error(prompt_session_init: MagicMock):
    """Should handle command parsing errors gracefully."""
    ps = MagicMock()
    ps.prompt.side_effect = ['select "', "exit"]
    prompt_session_init.return_value = ps

    context = MagicMock()
    shell = interactivity.Shell(context)
    shell.run()

    assert shell.error
    assert len(shell.execution_history) == 1
