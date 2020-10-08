from pytest import mark

from lambda_deployer import utils

SCENARIOS = {
    None: None,
    '900 bytes': 900,
    '2.0 KB': 2048,
    '117.7 MB': 123456789,
    '92.0 GB': 98765432111,
    '112.0 TB': 123123123123123,
}


@mark.parametrize('expected, value', SCENARIOS.items())
def test_to_human_readable_size(expected: str, value: int):
    """Should return the expected display value."""
    assert expected == utils.to_human_readable_size(value)
