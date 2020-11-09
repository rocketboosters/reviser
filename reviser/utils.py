import typing


def to_human_readable_size(
    number_of_bytes: typing.Optional[int],
) -> typing.Optional[str]:
    """Converts bytes value to human readable size."""
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
