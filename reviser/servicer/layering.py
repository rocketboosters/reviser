import textwrap
import typing
from collections import defaultdict

from botocore.client import BaseClient

from reviser import definitions
from reviser import templating
from reviser.servicer import functioning


def get_layer_versions(
    lambda_client: BaseClient,
    layer_name: str,
) -> typing.List["definitions.LambdaLayer"]:
    """
    Returns a list of layer versions for the specified layer name (or ARN)
    in order of increasing version.

    :param lambda_client:
        Boto3 client used to query for layer version info.
    :param layer_name:
        Name or ARN of the layer for which to list versions.
    """
    try:
        paginator = lambda_client.get_paginator("list_layer_versions")
        request = {"LayerName": layer_name}
        layers = [
            definitions.LambdaLayer(layer)
            for page in paginator.paginate(**request)
            for layer in page.get("LayerVersions") or []
        ]
        return list(sorted(layers, key=lambda x: x.version or 0))
    except lambda_client.exceptions.ResourceNotFoundException:
        return []


def remove_layer_version(lambda_client: BaseClient, layer_arn: str) -> bool:
    """Removes the specified lambda layer."""
    parts = layer_arn.rsplit(":", 1)
    request = dict(
        LayerName=parts[0],
        VersionNumber=int(parts[1]),
    )
    try:
        lambda_client.delete_layer_version(**request)
        return True
    except Exception as error:
        print("REQUEST:", request)
        templating.print_error(
            f'[FAILED]: Version {layer_arn} could not be deleted "{error}"', error
        )
        return False


def get_layer_version(
    lambda_client: BaseClient,
    layer_name: str,
    version: int,
) -> "definitions.LambdaLayer":
    """Retrieves the configuration for the specified lambda layer."""
    return definitions.LambdaLayer(
        lambda_client.get_layer_version(
            LayerName=layer_name,
            VersionNumber=version,
        )
    )


def echo_layer_versions(
    client: BaseClient,
    layer_names: typing.List[str],
    function_names: typing.List[str],
):
    """Print a table of lambda layer versions to the terminal"""
    function_versions = [
        version
        for name in function_names
        for version in functioning.get_function_versions(client, name)
    ]

    for name in layer_names:
        versions = get_layer_versions(client, name)
        if not versions:
            print(f'\n[IGNORED]: No layer "{name}" was found.')
            continue

        functions: typing.DefaultDict[str, list] = defaultdict(list)
        for func in function_versions:
            match = func.get_layer(name)
            if match is not None:
                functions[str(match.version)] += [
                    f"{func.name}:{func.version}",
                    *[f"{func.name}:{a.name}" for a in func.aliases],
                ]

        print("\n{}".format(64 * "="))
        print(f"(L) {name}")
        for v in versions:
            print(
                textwrap.indent(
                    "\n".join(
                        textwrap.wrap(
                            f"{v.version}: {v.description or v.created}",
                            width=60,
                            subsequent_indent="  ",
                        )
                    ),
                    prefix="  ",
                )
            )
            for func in functions[str(v.version)]:
                print(f"      - {func}")
