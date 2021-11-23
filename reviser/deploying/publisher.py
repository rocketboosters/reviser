"""Publisher functionality module."""
import typing

from botocore.client import BaseClient

from reviser import definitions
from ..deploying import updater


def _wait_for_existing_updates_to_complete(client: BaseClient, function_name: str):
    """
    Wait for any existing updates to complete on the lambda function.

    This is used to make sure the function is ready to be updated.

    :param client:
        Lambda boto3 client
    :param function_name:
        Lambda function name
    :param waiter_type:
        The client.get_waiter type.
    """
    waiter = client.get_waiter("function_updated")
    waiter.wait(FunctionName=function_name)


def _update_function_configuration(
    client: BaseClient,
    function_name: str,
    target: "definitions.Target",
    published_layers: typing.List["definitions.PublishedLayer"],
    dry_run: bool,
):
    """
    Update the function configuration.

    Functions can only be updated if they are ready to be updated, so we will
    have to wait for the function State to be Active, and LastUpdateStatus to be
    Successful. It will exponentially increment the sleep time for every
    status check.

    :param client:
        Lambda boto3 client
    :param function_name:
        Lambda function name
    :param target:
        The definitions.Target.
    :param published_layers:
        The definitions.PublishedLayer
    """
    _wait_for_existing_updates_to_complete(client, function_name)
    updater.update_function_configuration(
        function_name=function_name,
        target=target,
        published_layers=published_layers,
        dry_run=dry_run,
    )


def _publish_function_version(
    client: BaseClient, function_name: str, code_sha_256: str, description: str
):
    """
    Publish function new version.

    Functions can only be updated if they are ready to be updated, so we will
    have to wait for the function State to be Active, and LastUpdateStatus to be
    Successful. It will exponentially increment the sleep time for every status
    check.

    :param client:
        Lambda boto3 client
    :param function_name:
        Lambda function name
    :param code_sha_256:
        The CodeSha256 from the client.update_function_cod response.
    :param description:
        The publish description
    :return:
        The client.publish_version response
    """
    _wait_for_existing_updates_to_complete(client, function_name)
    return client.publish_version(
        FunctionName=function_name,
        CodeSha256=code_sha_256,
        Description=description or "",
    )


def publish_function(
    target: "definitions.Target",
    s3_keys: typing.List[str],
    published_layers: typing.List["definitions.PublishedLayer"],
    description: str = None,
    dry_run: bool = False,
):
    """Publish updated versions of the functions after upload."""
    client = target.client("lambda")
    for name, key in zip(target.names, s3_keys):
        print(f"[PUBLISHING]: Deploying code bundle to {name} $LATEST")
        response = None

        if not dry_run:
            response = client.update_function_code(
                FunctionName=name,
                S3Bucket=target.bucket,
                S3Key=key,
                Publish=False,
            )

        _update_function_configuration(
            client=client,
            function_name=name,
            target=target,
            published_layers=published_layers,
            dry_run=dry_run,
        )

        print("[PUBLISHING]: Publishing new version from bundle")
        if response and not dry_run:
            response = _publish_function_version(
                client=client,
                function_name=response["FunctionName"],
                code_sha_256=response["CodeSha256"],
                description=description or "",
            )
            print(
                "[PUBLISHED]: Function {} ({})".format(
                    name,
                    response["Version"],
                )
            )
            print("  - Version:", response["FunctionArn"])
            print("  - Runtime:", response["Runtime"])

    print("[DEPLOYED]: Lambda function code has been deployed\n")


def publish_layer(
    target: "definitions.Target",
    s3_keys: typing.List[str],
    description: str = None,
    dry_run: bool = False,
) -> typing.List["definitions.PublishedLayer"]:
    """Publish an updated version of the layer after bundle has been uploaded to S3."""
    published_layers = []
    client = target.client("lambda")

    for name, key in zip(target.names, s3_keys):
        print(f"[PUBLISHING]: Publishing code bundle to {name} layer")
        if dry_run:
            continue

        response = client.publish_layer_version(
            LayerName=name,
            Description=description or "",
            Content={
                "S3Bucket": target.bucket,
                "S3Key": key,
            },
            CompatibleRuntimes=[f"python{definitions.RUNTIME_VERSION}"],
        )
        print("[PUBLISHED]: Layer {} ({})".format(name, response["Version"]))
        print("  - Layer:", response["LayerArn"])
        print("  - Version:", response["LayerVersionArn"])
        published_layers.append(definitions.PublishedLayer(response=response))

    print("[DEPLOYED]: Lambda layer code has been deployed\n")
    return published_layers
