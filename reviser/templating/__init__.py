import pathlib
import re
import textwrap
import traceback
import typing

import colorama
import yaml
from jinja2 import Environment

import reviser

_COLOR_MAP = {
    "green": colorama.Fore.GREEN,
    "red": colorama.Fore.RED,
    "error": colorama.Fore.RED,
    "cyan": colorama.Fore.CYAN,
    "magenta": colorama.Fore.MAGENTA,
    "yellow": colorama.Fore.YELLOW,
    "warning": colorama.Fore.YELLOW,
}


def _yaml_filter(value: dict, indent: int = 0) -> str:
    """Renders the value as yaml"""
    if not value:
        return ""

    return textwrap.indent(yaml.safe_dump(value), prefix=indent * " ")


def _single_line_filter(value: str) -> str:
    """Reduces a string to a single line with no insignificant padding."""
    regex = re.compile(r"\s{2,}")
    return regex.sub(" ", (value or "").replace("\n", " ")).strip()


def _colorize_filter(value: str, color: str = None) -> str:
    """Applies ansi console coloring to the string."""
    if color_value := _COLOR_MAP.get((color or "").lower()):
        return f'{color_value}{value or ""}{colorama.Style.RESET_ALL}'
    return value


_environment = Environment()
_environment.filters["yaml"] = _yaml_filter
_environment.filters["single_line"] = _single_line_filter
_environment.filters["colorize"] = _colorize_filter


def render(location: str, **kwargs) -> str:
    """Loads a template from the path and returns the rendered contents."""
    contents = (
        pathlib.Path(reviser.__file__)
        .parent.joinpath(*location.strip("/").split("/"))
        .read_text()
    )
    return _environment.from_string(contents).render(**kwargs)


def printer(location: str, **kwargs):
    """Renders the template and prints it to stdout."""
    print(render(location, **kwargs))


def print_error(message: str, error: Exception = None):
    """
    Renders an exception template to stdout. If error is specified,
    that will be rendered as a stacktrace as well.
    """
    stack_trace: typing.Optional[str]
    if error:
        stack_trace = "\n".join(
            traceback.format_exception(
                type(error),
                error,
                error.__traceback__,
            )
        )
    else:
        stack_trace = None
    printer(
        "templating/error.jinja2",
        message=message,
        stack_trace=stack_trace,
    )
