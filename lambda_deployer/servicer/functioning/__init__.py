import dataclasses
import datetime
import typing
from collections import defaultdict

from botocore.client import BaseClient

from lambda_deployer import definitions
from lambda_deployer import templating


def assign_alias(
        lambda_client: BaseClient,
        function_name: str,
        alias: str,
        version: str,
        create: bool = False,
):
    """
    Update an alias to point to the specified version. Creates the alias
    if it does not exist is specified.

    :param lambda_client:
        Client to use for the update.
    :param function_name:
        Name of the target lambda function.
    :param alias:
        Name of the alias to update.
    :param version:
        Version of the function to be used by the alias.
    :param create:
        Whether or not to create the alias if doesn't exist.
    """
    try:
        lambda_client.update_alias(
            FunctionName=function_name,
            Name=alias,
            FunctionVersion=version
        )
    except lambda_client.error.ResourceNotFoundException:
        if create:
            lambda_client.create_alias(
                FunctionName=function_name,
                Name=alias,
                FunctionVersion=version
            )
        else:
            raise


def get_function_versions(
        lambda_client: BaseClient,
        function_name: str,
) -> typing.List['definitions.LambdaFunction']:
    """Lists all of a function's versions and their associated aliases."""
    try:
        paginator = lambda_client.get_paginator('list_versions_by_function')
        versions = [
            definitions.LambdaFunction(item)
            for response in paginator.paginate(FunctionName=function_name)
            for item in response['Versions']
        ]
    except lambda_client.exceptions.ResourceNotFoundException:
        return []

    aliases = lambda_client.list_aliases(
        FunctionName=function_name,
        MaxItems=500
    )
    aliased = defaultdict(list)
    for a in aliases['Aliases']:
        aliased[a['FunctionVersion']].append(a)

    versions.sort(
        key=lambda x: int(1e8 if x.version == '$LATEST' else x.version),
    )
    return [
        dataclasses.replace(v, alias_responses=aliased[v.version])
        for v in versions
    ]


def remove_function_version(lambda_client, version_arn: str):
    """
    Removes the lambda function version with the specified version ARN. This
    will fail for any versions.

    :param lambda_client:
        Boto3 client for interacting with the lambda function.
    :param version_arn:
        The ARN for the version of the lambda function that should be removed.
    """

    try:
        lambda_client.delete_function(FunctionName=version_arn)
        print('[PRUNED]: {}'.format(version_arn))
    except Exception as error:
        print('[FAILED]: Version {} could not be deleted "{}"'.format(
            version_arn,
            error
        ))


def echo_function_versions(client: BaseClient, names: typing.List[str]):
    """
    Displays function versions with basic info for each specified
    lambda function.
    """
    for name in names:
        versions = get_function_versions(client, name)
        if not versions:
            print(f'\n[IGNORED]: No function "{name}" was found.')
            continue

        groups = defaultdict(list)
        for v in versions:
            dt = datetime.datetime.fromisoformat(v.modified.split('+')[0])
            groups[str(dt.date())].append({
                'time': dt.strftime('%H:%M'),
                'data': v
            })

        templating.printer(
            'servicer/functioning/echo_versions.jinja2',
            name=name,
            groups=list(sorted(
                groups.items(),
                key=lambda x: x[0]
            ))
        )


def get_function_version(
        lambda_client: BaseClient,
        function_name: str,
        qualifier: str = '$LATEST',
) -> 'definitions.LambdaFunction':
    """Retrieves the configuration for the specified lambda function."""
    response = lambda_client.get_function_configuration(
        FunctionName=function_name,
        Qualifier=qualifier or '$LATEST',
    )

    request = {
        'FunctionName': function_name,
        'MaxItems': 500,
    }
    if (version := response.get('version')) and version != '$LATEST':
        request['FunctionVersion'] = version
    alias_response = lambda_client.list_aliases(**request)

    return definitions.LambdaFunction(
        response,
        alias_response.get('Aliases') or [],
    )
