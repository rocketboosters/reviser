"""Shared utility function module."""
import typing


def to_human_readable_size(
    number_of_bytes: typing.Optional[int],
) -> typing.Optional[str]:
    """Convert bytes value to human readable size."""
    if number_of_bytes is None:
        return None

    step_to_greater_unit = 1024
    unit = "bytes"
    value = float(number_of_bytes)

    if value < 1024:
        return f"{int(value)} {unit}"

    if (value / step_to_greater_unit) >= 1:
        value /= step_to_greater_unit
        unit = "KB"

    if (value / step_to_greater_unit) >= 1:
        value /= step_to_greater_unit
        unit = "MB"

    if (value / step_to_greater_unit) >= 1:
        value /= step_to_greater_unit
        unit = "GB"

    if (value / step_to_greater_unit) >= 1:
        value /= step_to_greater_unit
        unit = "TB"

    value = round(value, 1)
    return f"{value} {unit}"


def get_matching_bucket(
    buckets: typing.Union[None, str, dict],
    aws_account_id: str,
    aws_region: str,
    default_bucket: str = None,
):
    """Fetch a bucket name from the buckets argument."""
    if not buckets:
        return default_bucket

    if isinstance(buckets, str):
        return buckets

    # Allow for setting buckets by account ID.
    account_buckets = buckets.get(aws_account_id, buckets)

    if isinstance(account_buckets, str):
        return account_buckets

    # Allow for settings buckets by aws region name.
    return account_buckets.get(aws_region, default_bucket)
