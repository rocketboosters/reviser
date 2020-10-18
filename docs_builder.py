import argparse
import io
import os
import pathlib
import typing
import re

import reviser
from reviser import commands
from reviser import templating


def _explode_docs(docs: str) -> typing.Tuple[str, str]:
    """Returns the first paragraph of the command documentation."""
    lines = [line.rstrip() for line in (docs or '').split('\n')]
    start_index = next((i for i, line in enumerate(lines) if line), 0)

    try:
        end_index = lines.index('', start_index) + 1
        return (
            ' '.join(lines[start_index:end_index]),
            '\n'.join(lines[end_index:])
        )
    except ValueError:
        return ' '.join(lines[start_index:]), ''


def _assemble_command(name: str, command_module) -> typing.Tuple[str, str]:
    """Creates the documentation entry for the given command."""
    summary, details = _explode_docs(command_module.__doc__)

    # Force the output of the ArgumentParser to a width of 80 columns.
    os.environ['COLUMNS'] = '80'
    parser = argparse.ArgumentParser(prog=name, add_help=False)

    usage = None
    if populator := getattr(command_module, 'populate_subparser', None):
        populator(parser)
        buffer = io.StringIO()
        parser.print_help(file=buffer)
        buffer.seek(0)
        usage = buffer.read()

    header = name
    if aliases := commands.REVERSED_ALIASES.get(name, []):
        header = '{} ({})'.format(header, ', '.join(aliases))

    result = templating.render(
        '../docs/command.jinja2',
        header=header,
        summary=summary,
        usage=usage,
        details=details or None,
    )
    return header, result.strip()


def _to_anchor(value: str) -> str:
    """Converts a header string into its anchor equivalent."""
    cleaner = re.compile(r'[^A-Za-z0-9\-_]+')
    return cleaner.sub('', value.replace(' ', '-').lower())


def _create_commands_docs() -> typing.Tuple[str, str]:
    """
    Iterates through all available shell commands in alphabetical order
    and creates a combined docstring for them all in markdown format.
    """
    sources = list(sorted(commands.COMMANDS.items(), key=lambda item: item[0]))
    items = [
        _assemble_command(name, command_module)
        for name, command_module in sources
    ]
    docs = '\n\n'.join([item[1] for item in items])
    tocs = '\n'.join([
        f'   - [{item[0]}](#{_to_anchor(item[0])})'
        for item in items
    ])
    return docs, tocs


def _create_configuration_docs() -> typing.Tuple[str, str]:
    """
    Loads and processes configuration documentation into a single doc
    string block and a toc string for the header.
    """

    root = pathlib.Path(__file__).parent.joinpath('docs').absolute()
    docs = root.joinpath('configuration.md').read_text()
    matcher = re.compile(r'(?P<prefix>#+)\s+(?P<name>.+)')
    tocs = '\n'.join([
        '{}- [{}](#{})'.format(
            ' ' * 3 * (len(match.group('prefix')) - 1),
            match.group('name'),
            _to_anchor(match.group('name')),
        )
        for line in docs.split('\n')
        if (match := matcher.match(line.rstrip()))
    ])
    return docs, tocs


def main():
    """Creates the README.md file from template and code documentation."""
    shell_commands, shell_commands_toc = _create_commands_docs()
    configuration, configuration_toc = _create_configuration_docs()

    output = templating.render(
        '../docs/README.template.md',
        configuration=configuration,
        configuration_toc=configuration_toc,
        shell_commands=shell_commands,
        shell_commands_toc=shell_commands_toc,
        version=reviser.__version__,
    ).replace('\r', '')
    pathlib.Path(__file__).parent.joinpath('README.md').write_text(output)


if __name__ == '__main__':
    main()
