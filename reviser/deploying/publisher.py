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
    Publish function new version, waiting for existing updates to complete.

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
    s3_keys: typing.Optional[typing.List[str]] = None,
    published_layers: typing.Optional[typing.List["definitions.PublishedLayer"]] = None,
    description: typing.Optional[str] = None,
    dry_run: bool = False,
):
    """
    Publish an updated version of the lambda function.

    :param target:
        The lambda function to publish.
    :param s3_keys:
        If the lambda function is not image based, the S3 keys of the code
        artifacts to deploy. If the lambda function is image based this will
        be ignored. This is expected to be an ordered list aligning with the
        target's names.
    :param published_layers:
        The published lambda layers to connect to the lambda function.
    :param description:
        A description of the lambda function version.
    :param dry_run:
        Whether to actually perform the action.
    """
    s3_keys = s3_keys or []
    published_layers = published_layers or []
    client = target.client("lambda")
    for i, name in enumerate(target.names):
        print(f"[PUBLISHING]: Deploying update to {name} $LATEST")
        response = None
        s3_key = s3_keys[i] if len(s3_keys) > i else None
        image = target.image.get_region_uri(target.aws_region)

        if not dry_run:
            code_args = (
                typing.cast(typing.Dict[str, str], {"ImageUri": image})
                if image
                else typing.cast(
                    typing.Dict[str, str], {"S3Bucket": target.bucket, "S3Key": s3_key}
                )
            )
            response = client.update_function_code(
                FunctionName=name, Publish=False, **code_args
            )

        _update_function_configuration(
            client=client,
            function_name=name,
            target=target,
            published_layers=published_layers,
            dry_run=dry_run,
        )

        print("[PUBLISHING]: Publishing new version")
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

    print("[DEPLOYED]: Lambda function code has been deployed\n")


def publish_layer(
    target: "definitions.Target",
    s3_keys: typing.List[str],
    description: typing.Optional[str] = None,
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
