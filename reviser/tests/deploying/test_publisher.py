from unittest import mock

from reviser.deploying import publisher


def test_publish_function_version():
    """Should publish a new function version."""
    client = mock.MagicMock()
    publisher._publish_function_version(
        client, function_name="fake", code_sha_256="fake", description="fake"
    )
    assert client.publish_version.call_count == 1


def test_update_function_configuration():
    """Should update function configuration without errors."""
    client = mock.MagicMock()
    publisher._update_function_configuration(
        client,
        function_name="fake",
        target=mock.MagicMock(),
        published_layers=[],
        dry_run=False,
    )


def test_wait_for_existing_updates_to_complete():
    """Should call client wait for function foo"""
    client = mock.MagicMock()
    wait_mock = mock.MagicMock()
    wait_mock.wait = mock.MagicMock()
    client.get_waiter.return_value = wait_mock
    lambda_name = "foo"
    publisher._wait_for_existing_updates_to_complete(client, lambda_name)
    assert wait_mock.wait.call_count == 1
