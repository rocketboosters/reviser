"""Update functionality module."""
import typing
import yaml

from botocore.client import BaseClient

from reviser import definitions
from reviser import servicer


def _filter_layer_updates(
    function_name: str,
    target: "definitions.Target",
    published_layers: typing.List["definitions.PublishedLayer"],
) -> typing.List[str]:
    """Filter layer updates to ones attachable to the specified function."""
    updates = {p.arn: p.versioned_arn for p in published_layers}
    return [
        updates.get(a.arn) or a.arn
        for a in target.layer_attachments
        if a.is_attachable(function_name)
    ]


def _to_versioned_arn(client: BaseClient, arn: str) -> str:
    """
    Convert the ARN into a versioned ARN if not already.

    Return an empty string if no versioned ARN exists.
    """
    if arn and arn.count(":") == 7:
        # Having seven ":" in a layer arn means that the version is included.
        # An unversioned arn would only have six ":".
        return arn

    if arn and (found_versions := servicer.get_layer_versions(client, arn)):
        version = found_versions[-1].version
        return f"{arn}:{version}"

    print(f"\n[WARNING]: No versions found for layer:\n   {arn}\n")
    return ""


def _get_layer_updates(
    client: BaseClient,
    function_name: str,
    target: "definitions.Target",
    current_configuration: dict,
    published_layers: typing.List["definitions.PublishedLayer"],
) -> typing.Optional[typing.List[str]]:
    """
    Create an updated list of layer ARNs to update on the function.

    These will be layer configurations to apply during the function configuration
    update now that new layers may have been made available.
    """
    if target.ignores_any("layer", "layers"):
        return None

    existing = [item["Arn"] for item in (current_configuration.get("Layers") or [])]
    layers = _filter_layer_updates(function_name, target, published_layers)

    latest = [
        versioned_arn
        for arn in layers
        if (versioned_arn := _to_versioned_arn(client, arn))
    ]

    if latest == existing:
        return None

    return latest


def _get_handler_update(
    target: "definitions.Target",
    current_configuration: dict,
) -> typing.Optional[str]:
    """Specify an updated handler if a change is found."""
    latest = target.bundle.handler
    existing = current_configuration.get("Handler")
    if target.ignores_any("handler") or latest == existing:
        return None
    return latest


def _get_runtime_update(
    target: "definitions.Target",
    current_configuration: dict,
) -> typing.Optional[str]:
    """Specify an updated runtime if a change is found."""
    latest = f"python{definitions.RUNTIME_VERSION}"
    existing = current_configuration.get("Runtime")
    if target.ignores_any("runtime") or latest == existing:
        return None
    return latest


def _get_memory_update(
    target: "definitions.Target",
    current_configuration: dict,
) -> typing.Optional[int]:
    """Specify an updated memory value if a change is found."""
    existing = current_configuration.get("MemorySize")
    latest = target.memory
    if target.ignores_any("memory") or latest == existing:
        return None
    return latest


def _get_timeout_update(
    target: "definitions.Target",
    current_configuration: dict,
) -> typing.Optional[int]:
    """Specify an updated timeout value if a change is found."""
    existing = current_configuration.get("Timeout")
    latest = target.timeout
    if target.ignores_any("timeout") or latest == existing:
        return None
    return latest


def _get_variable_updates(
    function_name: str,
    target: "definitions.Target",
    current_configuration: dict,
) -> typing.Optional[dict]:
    """Determine the environment variable updates for the function."""
    if target.ignores_any("variable", "variables"):
        return None

    existing = current_configuration.get("Environment", {}).get("Variables", {})

    def _get_value(variable: "definitions.EnvironmentVariable"):
        """Fetch the environment variable value based on its settings."""
        if variable.preserve:
            return existing.get(variable.name)
        return variable.get_value(function_name)

    latest = {e.name: v for e in target.variables if (v := _get_value(e))}
    if latest == existing:
        return None
    return {"Variables": latest}


def update_function_configuration(
    function_name: str,
    target: "definitions.Target",
    published_layers: typing.List["definitions.PublishedLayer"],
    dry_run: bool = False,
):
    """Update the function configuration as part of a deployment process."""
    client = target.client("lambda")
    current = client.get_function_configuration(FunctionName=function_name)

    changes = dict(
        Layers=_get_layer_updates(
            client,
            function_name,
            target,
            current_configuration=current,
            published_layers=published_layers,
        ),
        Runtime=_get_runtime_update(target, current),
        MemorySize=_get_memory_update(target, current),
        Timeout=_get_timeout_update(target, current),
        Environment=_get_variable_updates(function_name, target, current),
        Handler=_get_handler_update(target, current),
    )

    modifications = {k: v for k, v in changes.items() if v is not None}
    if not modifications:
        print(f"[UNCHANGED]: {function_name} configuration unchanged.")
        return

    print(f"[MODIFYING]: Updating {function_name} configuration values:")
    print(yaml.safe_dump(modifications))

    if dry_run:
        print("[DRY_RUN]: No configuration updates applied.")
        return

    client.update_function_configuration(FunctionName=function_name, **modifications)
