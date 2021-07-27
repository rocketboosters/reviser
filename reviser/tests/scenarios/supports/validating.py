"""Test validation supports library."""
from reviser import interactivity
from reviser import definitions


def assert_command_result(
    command: "definitions.DataWrapper",
    result: "interactivity.ExecutionResult",
):
    """Validate that the execution result meets expectations."""
    value = command.get("command")
    expected = command.get("expected")

    if status := expected.get("status"):
        assert (
            result.status == status
        ), f"""
            Expected command "{value}" to return a status "{status}",
            but instead the status was "{result.status}".
            """

    if info := expected.get("info"):
        assert result.info is not None and (
            info.items() <= result.info.items()
        ), f"""
            Expected command "{value}" to return a subset of info matching:

            {info}

            but instead it was:

            {result.info}
            """
