import typing

from reviser import definitions
from ..deploying import updater


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

        updater.update_function_configuration(
            function_name=name,
            target=target,
            published_layers=published_layers,
            dry_run=dry_run,
        )

        print("[PUBLISHING]: Publishing new version from bundle")
        if response and not dry_run:
            response = client.publish_version(
                FunctionName=response["FunctionName"],
                CodeSha256=response["CodeSha256"],
                Description=description or "",
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
    """
    Publish an updated version of the layer after bundle has been uploaded
    to S3 and is available to source as the new lambda layer code.
    """
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
