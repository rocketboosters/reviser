import datetime
import functools
import os
import typing

from reviser import definitions
from reviser import utils


def upload_callback(bytes_uploaded: int, status: dict):
    """Update the display with current update status"""
    status["uploaded_bytes"] += bytes_uploaded
    progress = int(100 * status["uploaded_bytes"] / status["total_bytes"])
    size = utils.to_human_readable_size(status["uploaded_bytes"])

    if progress - status["display_progress"] >= 5:
        print(f"{progress}% ({size})")
        status["display_progress"] = progress


def upload(
    target: "definitions.Target",
    dry_run: bool = False,
) -> typing.List[str]:
    """
    Upload deployment bundle using Boto3 with progress callback
    display

    :param target:
        The lambda function(s)/layer(s) target that will be uploaded
        for all selected names in the target.
    :param dry_run:
        If true, the upload process will be exercised without actually
        uploading the data.
    """
    try:
        size_bytes = os.path.getsize(target.bundle_zip_path)
    except FileNotFoundError:
        if not dry_run:
            raise RuntimeError("Bundling is required before deploy.")
        size_bytes = 0

    upload_status = {
        "uploaded_bytes": 0,
        "total_bytes": size_bytes,
        "display_progress": -5,
    }

    now = datetime.datetime.utcnow()
    timestamp = now.isoformat().replace(":", "-").replace(".", "-")
    s3_keys = [
        f"lambda-deployer/{target.kind.value}/{name}/{timestamp}.zip"
        for name in target.names
    ]

    size = utils.to_human_readable_size(upload_status["total_bytes"])
    print(f"[UPLOADING]: {s3_keys[0]} (size: {size})")

    client = target.client("s3")

    if not dry_run:
        client.upload_file(
            Filename=str(target.bundle_zip_path),
            Bucket=target.bucket,
            Key=s3_keys[0],
            Callback=functools.partial(upload_callback, status=upload_status),
        )

    for key in s3_keys[1:]:
        print(f"[COPYING]: {s3_keys[0]} -> {key}")
        if not dry_run:
            client.copy_object(
                Bucket=target.bucket,
                Key=key,
                CopySource={
                    "Bucket": target.bucket,
                    "Key": s3_keys[0],
                },
            )

    return s3_keys
