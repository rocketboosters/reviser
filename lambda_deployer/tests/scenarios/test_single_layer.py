from ..scenarios import supports


def test_single_layer_scenario_push():
    """Should execute the push scenario as expected."""
    with supports.ScenarioRunner('single_layer/scenario_push.yaml') as sr:
        sr.check_success()

        layer = sr.configuration.get_layer('foo-layer')
        assert layer.bundle_zip_path.exists(), """
            Expect the foo-layer target to have been bundled.
            """

        assert sr.shell.execution_history[0].result.status == 'DEPLOYED'
        assert sr.shell.execution_history[1].result.status == 'DEPLOYED'

        observed = {
            cargs.args[0]
            for cargs in sr.patches.install_pip_package.call_args_list
        }
        assert {'spam', 'ham'} == observed, """
            Expect the two packages specified in the requirements.txt
            file to be installed during the layer build process.
            """

        observed = {
            cargs.args[0]
            for cargs in sr.patches.install_pipper_package.call_args_list
        }
        assert {'bar', 'baz'} == observed, """
            Expect the two packages specified in the pipper.json file
            to be installed during the layer build process.
            """
