from ..scenarios import supports


def test_simple_scenario_one():
    """Should execute the scenario as expected."""
    with supports.ScenarioRunner('simple/scenario_one.yaml') as sr:
        sr.check_success()

        foo_function = sr.configuration.get_function('foo-function')
        assert foo_function.bundle_zip_path.exists(), """
            Expect the foo-function target to have been bundled.
            """

        # No dependencies should have been installed when none are specified.
        sr.patches.install_pip_package.assert_not_called()
        sr.patches.install_pipper_package.assert_not_called()
