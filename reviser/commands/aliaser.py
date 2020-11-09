"""
Assigns an alias to the specified version of the selected or
specified lambda function. Or it will create a new alias and assign
it to the specified version if the --create flag is included.

To assign an existing `test` alias to version 42 of the selected
function, the command would be:

```
> alias test 42
```

If multiple functions are currently selected, use `--function=<NAME>`
to identify the function to which the alias change will be applied.
"""
import typing
from argparse import ArgumentParser

from reviser import definitions
from reviser import interactivity
from reviser import servicer


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Shell auto-completes for this command."""
    return ["--function", "--yes", "--create"]


def populate_subparser(parser: ArgumentParser):
    """Add alias subcommand to supplied parser"""
    parser.add_argument(
        "alias",
        help="""
        Name of an existing alias to move to the specified version,
        or the name of an alias to create and assign to the specified
        function version if the --create flag is included to allow for
        creating a new alias.
        """,
    )
    parser.add_argument(
        "version",
        default="$LATEST",
        help="""
        Version of the function that the alias should be assigned
        to. This will either be an integer value or $LATEST. To see
        what versions are available for a given function use the list
        command.
        """,
    )
    parser.add_argument(
        "--function",
        help="""
        The alias command only acts on one function. This can be
        achieved either by selecting the function target via the
        select command, or specifying the function name to apply this
        change to with this flag.
        """,
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="""
        By default this command will require input confirmation
        before carrying out the change. Specify this flag to
        skip input confirmation and proceed without a breaking prompt.
        """,
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="""
        When specified the alias will be created instead of reassigned.
        Use this to create and assign new aliases to a function. When
        this flag is not specified, the command will fail if the alias
        doesn't exist, which helps prevent accidental alias creation.
        """,
    )


def _get_version(target: "definitions.Target", version: str) -> str:
    """
    Converts the version value into an absolute function version.
    """
    try:
        number = int(version)
    except ValueError:
        return version

    if number > 0:
        return version

    client = target.client("lambda")
    versions = servicer.get_function_versions(client, target.names[0])
    return versions[number - 1].version or "unknown"


def run(ex: "interactivity.Execution") -> "interactivity.Execution":
    """Execute the command invocation."""
    selected = ex.shell.context.get_selected_targets(ex.shell.selection)
    is_ambiguous = not ex.args.get("function") and (
        0 < len(selected.function_targets) > 1
        or len(selected.function_targets[0].names) > 1
    )
    if is_ambiguous:
        return ex.finalize(
            status="ERROR",
            message="""
                Ambiguous alias assignment. Only one function can be assigned
                at a time. Either modify the selection or use the --function
                flag to specify the target function for the alias change.
                """,
            echo=True,
        )

    target = selected.function_targets[0]
    name = ex.args.get("function") or target.names[0]
    client = target.client("lambda")
    alias = ex.args.get("alias")
    version = _get_version(target, ex.args.get("version", "unknown"))
    create = ex.args.get("create")
    yes = ex.args.get("yes")

    request = dict(
        FunctionName=name,
        Name=alias,
        FunctionVersion=version,
    )

    prefix = f"Create {alias} at" if create else f"Move {alias} to"
    message = f"\n{prefix} {name}:{version} [y/N]? "
    if not yes and not (input(message) or "").strip().lower().startswith("y"):
        return ex.finalize(
            status="ABORTED",
            message="No alias changes made.",
            echo=True,
        )

    if create:
        client.create_alias(**request)
    else:
        client.update_alias(**request)

    return ex.finalize(
        status="SUCCESS",
        message="Alias change has been applied.",
        info={"function": name, "alias": alias, "version": version},
        echo=True,
    )
