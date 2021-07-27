"""Lambda entrypoint for the complex scenario test."""


def run(event: dict, context):
    """Execute the lambda function."""
    print(event, context)
