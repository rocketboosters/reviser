import typing


def to_human_readable_size(
        number_of_bytes: typing.Optional[int],
) -> typing.Optional[str]:
    """Converts bytes value to human readable size."""
    if number_of_bytes is None:
        return None

    step_to_greater_unit = 1024
    unit = 'bytes'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'KB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'MB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'GB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'TB'

    number_of_bytes = round(number_of_bytes, 1)
    return f'{number_of_bytes} {unit}'
