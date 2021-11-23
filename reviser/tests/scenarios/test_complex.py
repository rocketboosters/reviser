from ..scenarios import supports
from unittest.mock import patch
from unittest.mock import MagicMock


@patch("reviser.deploying.publisher._wait_for_function_to_be_ready")
def test_complex_scenario_push(wait_for_function_to_be_ready: MagicMock):
    """Should execute the push command as expected."""
    with supports.ScenarioRunner("complex/scenario_push.yaml") as sr:
        sr.check_success()

        foo_function = sr.configuration.get_function("foo-function")
        assert foo_function.bundle_zip_path.exists(), """
            Expect the foo-function target to have been bundled.
            """


def test_complex_scenario_status():
    """Should carry out status operation as expected without error."""
    with supports.ScenarioRunner("complex/scenario_status.yaml") as sr:
        sr.check_success()
        sr.check_commands()


def test_complex_scenario_select():
    """Should carry out select operations as expected without error."""
    with supports.ScenarioRunner("complex/scenario_select.yaml") as sr:
        sr.check_success()
        sr.check_commands()
