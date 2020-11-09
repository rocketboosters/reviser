import typing
import yaml

from botocore.client import BaseClient

from reviser import definitions
from reviser import servicer


def _get_layer_updates(
    client: BaseClient,
    function_name: str,
    target: "definitions.Target",
    current_configuration: dict,
    published_layers: typing.List["definitions.PublishedLayer"],
) -> typing.Optional[typing.List[str]]:
    """
    Creates an updated list of layer ARNs to update the function layer
    configuration to during function configuration update.
    """
    if target.ignores_any("layer", "layers"):
        return None

    existing = [item["Arn"] for item in (current_configuration.get("Layers") or [])]
    updates = {p.arn: p.versionedArn for p in published_layers}
    layers = [
        updates.get(a.arn, a.arn)
        for a in target.layer_attachments
        if a.is_attachable(function_name)
    ]

    latest = []
    for arn in layers:
        if arn and arn.count(":") == 7:
            latest.append(arn)
        elif arn and (found_versions := servicer.get_layer_versions(client, arn)):
            version = found_versions[-1].version
            latest.append(f"{arn}:{version}")
        else:
            print(f"\n[WARNING]: No versions found for layer:\n   {arn}\n")

    if latest == existing:
        return None
    return latest


def _get_runtime_update(
    target: "definitions.Target",
    current_configuration: dict,
) -> typing.Optional[str]:
    """Specifies an updated runtime if a change is found."""
    latest = f"python{definitions.RUNTIME_VERSION}"
    existing = current_configuration.get("Runtime")
    if target.ignores_any("runtime") or latest == existing:
        return None
    return latest


def _get_memory_update(
    target: "definitions.Target",
    current_configuration: dict,
) -> typing.Optional[int]:
    existing = current_configuration.get("MemorySize")
    latest = target.memory
    if target.ignores_any("memory") or latest == existing:
        return None
    return latest


def _get_timeout_update(
    target: "definitions.Target",
    current_configuration: dict,
) -> typing.Optional[int]:
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
    """
    Determines the environment variable updates for the function.
    """
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
    """Updates the function configuration as part of a deployment process."""
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
