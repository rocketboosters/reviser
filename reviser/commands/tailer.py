"""Tail the logs for the selected lambda functions."""
import argparse
import datetime
import json
import time
import typing

import botocore.client

from reviser import definitions
from reviser import interactivity


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Get shell auto-completes for this command."""
    return []


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    return


def run(ex: "interactivity.Execution") -> "interactivity.Execution":
    """Execute a bundle operation on the selected function/layer targets."""
    selected = ex.shell.context.get_selected_targets(ex.shell.selection)
    functions = [
        t for t in selected.targets if t.kind == definitions.TargetType.FUNCTION
    ]
    try:
        print("Tailing lambda logs. Press ctrl + C to stop")
        _log_forever(functions)
    except KeyboardInterrupt:
        # This is the expected way to exit.
        pass
    return ex.finalize(
        status="STOPPED",
        message="Stopped tailing logs.",
        info={},
        echo=True,
    )


def _log_forever(targets: typing.List[definitions.Target]):
    """Tail continuously the given targets without end."""
    tokens: typing.Dict[str, str] = {}
    started_at = time.time()
    has_multiple = len([n for t in targets for n in t.names]) > 1
    while True:
        for t in targets:
            for name in t.names:
                log_group = f"/aws/lambda/{name}"
                client = t.client("logs")
                active = _get_active_log_streams(client, log_group)
                for stream in active:
                    stream_key = f"{log_group}/{stream}"
                    token = tokens.get(stream_key)
                    extra = {"nextToken": token} if token else {}
                    response = client.get_log_events(
                        logGroupName=log_group,
                        logStreamName=stream,
                        startFromHead=True,
                        startTime=int(started_at * 1000),
                        **extra,
                    )
                    _print_log_events(response["events"], name, has_multiple)
                    tokens[stream_key] = response["nextForwardToken"]
        time.sleep(1)
        _escape_hook()


def _is_active(log_stream: dict, cut_off: int) -> bool:
    """
    Determine if the given stream is still active and worth tailing.

    :param log_stream:
        A dictionary returned by `describe_log_streams` describing the
        log_stream under consideration.
    :param cut_off:
        The number of seconds to wait before calling a log_stream inactive.
        If the stream does not have a `lastIngestionTime` more recent than
        `cut_off` seconds ago it will be considered not active.
    :return:
        Whether the given log stream is active.
    """
    last_ingest = log_stream["lastIngestionTime"] / 1000
    return time.time() - last_ingest < cut_off


def _print_log_events(
    events: typing.List[dict],
    function_name: str,
    show_name: bool,
):
    """
    Print out the given set of events from a `get_log_events` call.

    :param events:
        The raw events to print out.
    :param function_name:
        The name of the function from which the events came.
    :param show_name:
        Whether to include the function name when printing out the log
        message.
    """
    base_prefix = f"[{function_name}]" if show_name else ""
    for event in events:
        timestamp = datetime.datetime.fromtimestamp(event["timestamp"] / 1000)
        prefix = f"{base_prefix}{timestamp.isoformat()} : "
        try:
            record = json.loads(event["message"])
            message = json.dumps(record, indent=2)
        except json.decoder.JSONDecodeError:
            message = event["message"]
        message = message.strip()
        for line in message.split("\n"):
            print(f"{prefix}{line}")
            prefix = " " * len(prefix)


def _get_active_log_streams(
    client: botocore.client.BaseClient,
    log_group: str,
    cut_off: int = 900,
) -> typing.List[str]:
    """
    Get the active streams within the specified log group.

    :param client:
        The client with which to query cloudwatch.
    :param log_group:
        The log group to search.
    :param cut_off:
        The number of seconds to wait before calling a log_stream inactive.
        If the stream does not have a `lastIngestionTime` more recent than
        `cut_off` seconds ago it will be considered not active.
    """
    response = client.describe_log_streams(
        logGroupName=log_group,
        orderBy="LastEventTime",
        descending=True,
    )
    return [
        log_stream["logStreamName"]
        for log_stream in response["logStreams"]
        if _is_active(log_stream, cut_off)
    ]


def _escape_hook():
    """Escape function for giving unit tests a means to escape the infinite loop."""
    pass
