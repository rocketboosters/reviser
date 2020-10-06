import textwrap
import typing
from collections import defaultdict

from botocore.client import BaseClient

from lambda_deployer import definitions
from lambda_deployer.servicer import functioning


def _to_name(layer_name_or_arn: typing.Optional[str]) -> typing.Optional[str]:
    """Converts the layer name/arn to a name."""
    return layer_name_or_arn

    # if not layer_name_or_arn:
    #     return None
    #
    # return (
    #     layer_name_or_arn.rsplit(':', 2)[-2]
    #     if layer_name_or_arn.startswith('arn:')
    #     else layer_name_or_arn
    # )


def get_layer_versions(
        lambda_client: BaseClient,
        layer_name: str,
) -> typing.List['definitions.LambdaLayer']:
    """
    Returns a list of layer versions for the specified layer name (or ARN)
    in order of increasing version.

    :param lambda_client:
        Boto3 client used to query for layer version info.
    :param layer_name:
        Name or ARN of the layer for which to list versions.
    """
    try:
        paginator = lambda_client.get_paginator('list_layer_versions')
        request = {'LayerName': _to_name(layer_name)}
        layers = [
            definitions.LambdaLayer(layer)
            for page in paginator.paginate(**request)
            for layer in page.get('LayerVersions') or []
        ]
        return list(sorted(layers, key=lambda x: x.version))
    except lambda_client.exceptions.ResourceNotFoundException:
        return []


def remove_layer_version(lambda_client: BaseClient, layer_arn: str):
    """Removes the specified lambda layer."""
    try:
        lambda_client.delete_layer_version(
            LayerName=_to_name(layer_arn),
            VersionNumber=int(layer_arn.rsplit(':', 1)[-1])
        )
        print(f'[PRUNED]: {layer_arn}')
    except Exception as error:
        print(f'[FAILED]: Version {layer_arn} could not be deleted "{error}"')


def get_layer_version(
        lambda_client: BaseClient,
        layer_name: str,
        version: int,
) -> 'definitions.LambdaLayer':
    """Retrieves the configuration for the specified lambda layer."""
    return definitions.LambdaLayer(lambda_client.get_layer_version(
        LayerName=_to_name(layer_name),
        VersionNumber=version,
    ))


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

        functions = defaultdict(list)
        for func in function_versions:
            match = func.get_layer(name)
            if match is not None:
                functions[str(match.version)] += [
                    f'{func.name}:{func.version}',
                    *[f'{func.name}:{a.name}' for a in func.aliases]
                ]

        print('\n{}'.format(64 * '='))
        print(f'(L) {name}')
        for v in versions:
            print(textwrap.indent(
                '\n'.join(textwrap.wrap(
                    f'{v.version}: {v.description or v.created}',
                    width=60,
                    subsequent_indent='  ',
                )),
                prefix='  ',
            ))
            for func in functions[str(v.version)]:
                print(f'      - {func}')
