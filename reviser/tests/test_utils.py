import typing

from pytest import mark

from reviser import utils

SCENARIOS = {
    None: None,
    "900 bytes": 900,
    "2.0 KB": 2048,
    "117.7 MB": 123456789,
    "92.0 GB": 98765432111,
    "112.0 TB": 123123123123123,
}


@mark.parametrize("expected, value", SCENARIOS.items())
def test_to_human_readable_size(expected: str, value: int):
    """Should return the expected display value."""
    assert expected == utils.to_human_readable_size(value)


EXTRACT_PACKAGE_NAME_SCENARIOS = (
    ("boto3", "boto3"),
    ("", ""),
    (None, ""),
    ("boto3>=1.11.23,<2.0.0", "boto3"),
    ("Dumb_package-name==1.11.23", "Dumb_package-name"),
)


@mark.parametrize("value, expected", EXTRACT_PACKAGE_NAME_SCENARIOS)
def test_extract_package_name(value: typing.Optional[str], expected: str):
    """Should extract the expected name from the package identifier."""
    assert expected == utils.extract_package_name(value)
