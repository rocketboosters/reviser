"""Invoke the target function."""
import json
import typing
from argparse import ArgumentParser

import yaml

from reviser import definitions
from reviser import interactivity
from reviser import templating


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Get shell auto-completes for this command."""
    return ["--function", "--response-format", "--tail"]


def populate_subparser(parser: ArgumentParser):
    """Add alias subcommand to supplied parser."""
    parser.add_argument(
        "--function",
        help="""
        The invoke command only acts on one function. This can be
        achieved either by selecting the function target via the
        select command, or specifying the function name to apply this
        change to with this flag.
        """,
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="""
        When specified, the invocation logging will be included as well for both the
        request and response data.
        """,
    )
    parser.add_argument(
        "--tail",
        action="store_true",
        help="""
        When specified, the tail of the log output from the function will be displayed
        as part of the execution. This will automatically be set if verbose is
        specified.
        """,
    )
    parser.add_argument(
        "--response-format",
        choices=["text", "json", "yaml"],
        default="text",
    )
    parser.add_argument(
        "--payload",
        default="{}",
        help="Specify the payload as a JSON-serialized string.",
    )
    parser.add_argument(
        "--payload-file",
        help="Specify the payload from a JSON/YAML file.",
    )


def _get_target_function(
    ex: "interactivity.Execution",
) -> typing.Tuple[typing.Optional["definitions.Target"], typing.Optional[str]]:
    """Get the target function that will be invoked."""
    selected = ex.shell.context.get_selected_targets(ex.shell.selection)
    function_name: typing.Optional[str] = ex.args.get("function")
    matches = [
        (target, name)
        for target in selected.function_targets
        for name in target.names
        if not function_name or name == function_name
    ]

    if not matches:
        ex.finalize(
            status="ERROR",
            message="No matching function targets found.",
            echo=True,
        )
        return None, None

    if len(matches) != 1:
        ex.finalize(
            status="ERROR",
            message="Invoke can only function on a single function.",
            echo=True,
        )
        return None, None

    return matches[0]


def _read_payload_file(ex: "interactivity.Execution") -> typing.Dict[str, typing.Any]:
    """Read invocation payload data from the file argument."""
    relative_file_path: typing.Optional[str] = ex.args.get("payload_file")
    if not relative_file_path:
        return {}

    path = ex.shell.context.configuration.directory.joinpath(relative_file_path)

    if path.name.endswith((".yaml", ".yml")):
        return yaml.safe_load(path.read_text())

    return json.loads(path.read_text())


def _get_payload(ex: "interactivity.Execution") -> typing.Dict[str, typing.Any]:
    """Assemble and return the payload for the function invocation."""
    value: typing.Dict[str, typing.Any] = json.loads(ex.args.get("payload", "{}"))
    value.update(_read_payload_file(ex))
    return value


def run(ex: "interactivity.Execution") -> "interactivity.Execution":
    """Execute the invoke command."""
    target, function_name = _get_target_function(ex)
    if not target:
        return ex

    payload = _get_payload(ex)
    is_verbose: bool = ex.args.get("verbose", False)
    tail_logs: bool = ex.args.get("tail", False) or is_verbose

    if is_verbose:
        print(
            "\n=== INVOCATION ===\n{}\n".format(
                yaml.safe_dump(
                    {
                        "function_name": function_name,
                        "payload": payload,
                    }
                )
            )
        )

    response = target.client("lambda").invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        LogType="Tail" if tail_logs else "None",
        Payload=json.dumps(payload).encode(),
    )

    if tail_logs and (logs := response.get("LogResult", "")):
        print(f"\n=== TAILED INVOCATION LOGS ===\n{logs}\n")

    invoked_version: str = response.get("ExecutedVersion", "$LATEST")

    if "FunctionError" in response:
        templating.print_error(response["FunctionError"])
        return ex.finalize(
            status="EXECUTION_ERROR",
            message="Function execution failed.",
            data={
                "version": invoked_version,
                "function_error": response.get("FunctionError"),
                "status_code": response.get("StatusCode"),
                "payload": payload,
            },
        )

    return ex.finalize(
        status="SUCCESS",
        message="Function invoked successfully.",
        data={
            "version": invoked_version,
            "payload": payload,
        },
    )
