from unittest import mock
from unittest.mock import MagicMock
from unittest.mock import patch

from reviser import definitions
from ..scenarios import supports


def test_simple_scenario_alias():
    """Should execute alias commands as expected."""
    with supports.ScenarioRunner("simple/scenario_alias.yaml") as sr:
        sr.check_success()
        assert sr.shell.execution_history[0].result.status == "SUCCESS"
        assert sr.shell.execution_history[1].result.status == "SUCCESS"
        assert sr.shell.execution_history[2].result.status == "ABORTED"


def test_simple_scenario_configs():
    """Should execute configs commands as expected."""
    with supports.ScenarioRunner("simple/scenario_configs.yaml") as sr:
        sr.check_success()
        assert sr.shell.execution_history[0].result.status == "SUCCESS"


def test_simple_scenario_list():
    """Should list function versions as expected."""
    with supports.ScenarioRunner("simple/scenario_list.yaml") as sr:
        sr.check_success()
        sr.check_commands()


def test_simple_scenario_prune():
    """Should prune function version 2 successfully."""
    with supports.ScenarioRunner("simple/scenario_prune.yaml") as sr:
        sr.check_success()
        result = sr.shell.execution_history[0].result
        assert result.status == "PRUNED"

        expected = ["arn:aws:lambda:us-east-1:123:function:foo-function:2"]
        assert (
            result.info.get("foo-function") == expected
        ), """
            Expect version 2 to be deleted, but not version 1 because
            it has an alias attached to it.
            """


def test_simple_scenario_prune_relative():
    """Should prune function versions 2 and 4 successfully."""
    with supports.ScenarioRunner("simple/scenario_prune_relative.yaml") as sr:
        sr.check_success()
        result = sr.shell.execution_history[0].result
        assert result.status == "PRUNED"

        expected = [
            "arn:aws:lambda:us-east-1:123:function:foo-function:2",
            "arn:aws:lambda:us-east-1:123:function:foo-function:4",
        ]
        assert (
            result.info.get("foo-function") == expected
        ), """
            Expect version 2 and 4 to be deleted, but not version 3 because
            it has an alias attached to it.
            """


@patch("reviser.deploying.publisher._wait_for_function_to_be_ready")
def test_simple_scenario_push(wait_for_function_to_be_ready: MagicMock):
    """Should execute the scenario as expected."""
    with supports.ScenarioRunner("simple/scenario_push.yaml") as sr:
        sr.check_success()

        foo_function = sr.configuration.get_function("foo-function")
        assert foo_function.bundle_zip_path.exists(), """
            Expect the foo-function target to have been bundled.
            """

        assert sr.shell.execution_history[0].result.status == "DEPLOYED"

        # No dependencies should have been installed when none are specified.
        sr.patches.install_pip_package.assert_not_called()
        sr.patches.install_pipper_package.assert_not_called()


def test_simple_scenario_reload():
    """Should reload configuration successfully."""
    with supports.ScenarioRunner("simple/scenario_reload.yaml") as sr:
        sr.check_success()

        result = sr.shell.execution_history[0].result
        assert result.status == "SUCCESS"

        before: definitions.Context = result.data["before"]
        before_target = before.configuration.targets[0]
        after: definitions.Context = result.data["after"]
        after_target = after.configuration.targets[0]
        assert (
            before_target.uuid == after_target.uuid
        ), """
            Expect target uuids to be preserved during reload because
            no significant changes between target reloads were found.
            """


def test_simple_scenario_region():
    """Should carry out region switching operations as expected without error."""
    with supports.ScenarioRunner("simple/scenario_region.yaml") as sr:
        sr.check_success()
        sr.check_commands()


def test_simple_scenario_select():
    """Should carry out select operations as expected without error."""
    with supports.ScenarioRunner("simple/scenario_select.yaml") as sr:
        sr.check_success()
        sr.check_commands()


def test_simple_scenario_status():
    """Should report function configuration status successfully."""
    with supports.ScenarioRunner("simple/scenario_status.yaml") as sr:
        sr.check_success()
        sr.check_commands()


@mock.patch("time.time", new=lambda: 1627345070)
@mock.patch("reviser.commands.tailer._escape_hook")
def test_simple_scenario_tail(escape_hook: mock.MagicMock):
    """Should carry out tail operations as expected without error."""
    escape_hook.side_effect = KeyboardInterrupt

    with supports.ScenarioRunner("simple/scenario_tail.yaml") as sr:
        sr.check_success()
        sr.check_commands()

    lobotomized = sr.patches.boto3_session
    gets = lobotomized.get_service_calls("logs", "get_log_events")
    assert len(gets) == 1
    expected_stream = "/aws/lambda/foobar/[$latest]active"
    assert gets[0].request["logStreamName"] == expected_stream
