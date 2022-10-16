"""Subpackage for assembling a lambda code package bundle for upload and deployment."""
import os
import typing
import zipfile

from reviser import definitions
from reviser.bundling import _installer


def _create_zip(target: "definitions.Target"):
    """
    Bundle together all source files into a single zip file.

    This zip file is structured so that it can be uploaded as an AWS Lambda function.

    :param target:
        A target configuration to bundle into a zip file for deployment.
    """
    zip_bundle = zipfile.ZipFile(
        target.bundle_zip_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    )

    for site_package_path in target.bundle.get_site_package_paths():
        # Add installed site package files into the bundle. For functions
        # the site packages should be added to the top-level bundle directory
        # as is the convention recommended by AWS documentation. However,
        # for layers, the site packages folder should be preserved during
        # bundling, which is why the root folders below are different for
        # the two types.
        root = (
            target.site_packages_directory
            if target.kind == definitions.TargetType.FUNCTION
            else target.bundle_directory
        )
        name = str(site_package_path.relative_to(root))
        zip_bundle.write(str(site_package_path), arcname=name)

    for copy_path in target.bundle.get_copy_paths():
        # Add copied source files into the bundle.
        name = str(copy_path.destination.relative_to(target.bundle_directory))
        zip_bundle.write(str(copy_path.destination), arcname=name)

    zip_bundle.close()
    print(f"[ARCHIVED]: {target.bundle_zip_path}")


def _check_do_install(
    target: "definitions.Target",
    reinstall: bool,
    installed_shared_dependencies: typing.Set[str],
):
    """Check to see if target needs to reinstall dependencies."""
    # Force an installation if reinstall is set and either the dependency is not
    # shared or the dependency is shared but has not been added yet.
    force_install = reinstall and (
        not target.dependencies.is_shared
        or target.dependencies.name not in installed_shared_dependencies
    )

    # Install if forced or the dependencies do net yet exist.
    return (
        force_install
        or not target.dependencies.site_packages_directory.exists()
        or not os.listdir(str(target.dependencies.site_packages_directory))
    )


def _check_do_copy(
    target: "definitions.Target",
    installed_shared_dependencies: typing.Set[str],
):
    """Check to see if target needs to re-copy shared dependencies."""
    # Copy if shared and a previous installation updated the shared dependencies.
    return (
        target.dependencies.is_shared
        and target.dependencies.name in installed_shared_dependencies
    )


def create(
    context: "definitions.Context",
    selection: "definitions.Selection",
    reinstall: bool = False,
):
    """
    Assemble the contents of the bundle folder for zipping.

    This copies the entire contents of the project folder to a temporary location
    and then installs and bundles the copied project for deployment.

    :param context:
        The context in which this bundle action is taking place.
    :param selection:
        A selection object that defines the subset of targets to execute
        the bundling process upon.
    :param reinstall:
        Whether to force re-installation of dependencies for previously
        bundled targets.
    """
    selected = context.get_selected_targets(selection)

    installed_shared_dependencies: typing.Set[str] = set([])

    for target in selected.targets:
        target.bundle_directory.mkdir(exist_ok=True, parents=True)

        if _check_do_install(target, reinstall, installed_shared_dependencies):
            _installer.install_dependencies(target)
            if target.dependencies.is_shared and target.dependencies.name:
                # List the shared dependency as having been installed to prevent
                # multiple installations in the same operation.
                installed_shared_dependencies.add(target.dependencies.name)
        elif _check_do_copy(target, installed_shared_dependencies):
            # Handle copying shared site packages that have already been installed by
            # a previous target.
            _installer.copy_shared_dependencies(target)
        else:
            print("[DEPENDENCIES]: Using existing installation cache.")

        for copy_path in target.bundle.get_copy_paths():
            copy_path.copy()
            print(f"[COPIED]: {copy_path.source.relative_to(target.directory)}")

        _create_zip(target)

    return selected
