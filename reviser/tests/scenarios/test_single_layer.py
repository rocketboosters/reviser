from ..scenarios import supports


def test_simple_scenario_list():
    """Should list function versions as expected."""
    with supports.ScenarioRunner("single_layer/scenario_list.yaml") as sr:
        sr.check_success()
        sr.check_commands()


def test_single_layer_scenario_prune():
    """Should execute the push scenario as expected."""
    with supports.ScenarioRunner("single_layer/scenario_prune.yaml") as sr:
        sr.check_success()

        result = sr.shell.execution_history[0].result
        assert result.status == "PRUNED"

        expected = [
            "arn:aws:lambda:us-east-1:123:layer:foo-layer:1",
            "arn:aws:lambda:us-east-1:123:layer:foo-layer:2",
        ]
        assert result.info.get("foo-layer") == expected, """
            Expect versions 1 and 2 to be deleted.
            """


def test_single_layer_scenario_push():
    """Should execute the push scenario as expected."""
    with supports.ScenarioRunner("single_layer/scenario_push.yaml") as sr:
        sr.check_success()

        layer = sr.configuration.get_layer("foo-layer")
        assert layer.bundle_zip_path.exists(), """
            Expect the foo-layer target to have been bundled.
            """

        assert sr.shell.execution_history[0].result.status == "DEPLOYED"
        assert sr.shell.execution_history[1].result.status == "DEPLOYED"

        observed = {
            cargs.args[0] for cargs in sr.patches.install_pip_package.call_args_list
        }
        assert {
            "spam",
            "ham",
        } == observed, """
            Expect the two packages specified in the requirements.txt
            file to be installed during the layer build process.
            """

        observed = sr.patches.install_pip_package.call_args_list[0].args[2]
        assert [
            "--pip-arg-1=pip-val-1",
            "--pip-arg-2=pip-val-2",
        ] == observed, """
            Expect pip install to be called with the two supplied arguments
            during the layer build process.
            """

        observed = {
            cargs.args[0] for cargs in sr.patches.install_pipper_package.call_args_list
        }
        assert {
            "bar",
            "baz",
        } == observed, """
            Expect the two packages specified in the pipper.json file
            to be installed during the layer build process.
            """

        observed = sr.patches.install_pipper_package.call_args_list[0].args[3]
        assert [
            "--pipper-arg-1=pipper-val-1",
            "--pipper-arg-2=pipper-val-2",
        ] == observed, """
            Expect pipper install to be called with the two supplied
            arguments during the layer build process.
            """


def test_simple_scenario_select():
    """Should carry out select operations as expected without error."""
    with supports.ScenarioRunner("single_layer/scenario_select.yaml") as sr:
        sr.check_success()
        sr.check_commands()


def test_simple_scenario_status():
    """Should report function configuration status successfully."""
    with supports.ScenarioRunner("single_layer/scenario_status.yaml") as sr:
        sr.check_success()
        sr.check_commands()
