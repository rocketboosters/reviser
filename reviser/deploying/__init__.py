import time
import typing

from reviser import definitions
from ..deploying import publisher
from ..deploying import uploader


def deploy_target(
    target: "definitions.Target",
    description: str = None,
    published_layers: typing.List["definitions.PublishedLayer"] = None,
    dry_run: bool = False,
) -> typing.List["definitions.PublishedLayer"]:
    """
    Deploy the bundled ZIP file to S3 for access by Lambda functions. The
    file is uploaded to the specified storage bucket with a timestamped key
    and then published to the lambda function.

    :param target:
        Configuration target to deploy.
    """
    s3_keys = uploader.upload(target, dry_run=dry_run)

    # Sleep for a few seconds to make sure the S3 upload has finished
    # processing to prevent race conditions during deployment
    if not dry_run:
        print("[SYNC]: Synchronization block between S3 and lambda")
        time.sleep(2)

    if target.kind == definitions.TargetType.LAYER:
        return publisher.publish_layer(
            target=target,
            s3_keys=s3_keys,
            description=description,
            dry_run=dry_run,
        )

    publisher.publish_function(
        target=target,
        s3_keys=s3_keys,
        published_layers=published_layers or [],
        description=description,
        dry_run=dry_run,
    )
    return []


def deploy(
    context: "definitions.Context",
    selection: "definitions.Selection",
    description: str = None,
    dry_run: bool = False,
) -> typing.List["definitions.Target"]:
    """
    Executes the deploy operation on the context's configuration filtered
    by the specified selection.
    """
    selected = context.get_selected_targets(selection)

    # Publish layers first so that the function publishes can update to
    # use any newly published layers.
    published_layers = []
    for target in selected.layer_targets:
        published_layers += deploy_target(
            target=target,
            description=description,
            published_layers=None,
            dry_run=dry_run,
        )

    for target in selected.function_targets:
        deploy_target(
            target=target,
            description=description,
            published_layers=published_layers,
            dry_run=dry_run,
        )

    return selected.targets
