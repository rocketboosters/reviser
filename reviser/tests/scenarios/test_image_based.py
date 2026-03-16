"""Scenario tests for lambda targets configured with ECR image-based deployments."""

from unittest.mock import MagicMock
from unittest.mock import patch

from ..scenarios import supports


@patch("reviser.deploying.publisher._wait_for_existing_updates_to_complete")
def test_image_based_scenario_push(_wait_for_existing_updates_to_complete: MagicMock):
    """Should skip bundling and deploy directly for image-based targets."""
    with supports.ScenarioRunner("image_based/scenario_push.yaml") as sr:
        sr.check_success()

        foo_function = sr.configuration.get_function("foo-function")
        assert not foo_function.bundle_zip_path.exists(), """
            Expect the foo-function target to NOT have been bundled because
            it uses an image-based configuration.
            """

        assert sr.shell.execution_history[0].result.status == "DEPLOYED", """
            Expect the push command to have deployed successfully without bundling.
            """

        # No dependencies should have been installed for an image-based target.
        sr.patches.install_pip_package.assert_not_called()
        sr.patches.install_pipper_package.assert_not_called()


def test_image_based_scenario_bundle():
    """Should skip bundling and report skipped targets for image-based targets."""
    with supports.ScenarioRunner("image_based/scenario_bundle.yaml") as sr:
        sr.check_success()

        foo_function = sr.configuration.get_function("foo-function")
        assert not foo_function.bundle_zip_path.exists(), """
            Expect the foo-function target to NOT have been bundled because
            it uses an image-based configuration.
            """

        result = sr.shell.execution_history[0].result
        assert result.status == "BUNDLED", """
            Expect the bundle command to succeed even when all targets are skipped.
            """

        assert result.info.get("items") == [], """
            Expect no items to appear in the bundled items list because the only
            target uses an image-based configuration.
            """

        assert result.info.get("skipped") == ["foo-function"], """
            Expect foo-function to appear in the skipped list because it uses
            an image-based configuration.
            """

        # No dependencies should have been installed for an image-based target.
        sr.patches.install_pip_package.assert_not_called()
        sr.patches.install_pipper_package.assert_not_called()
