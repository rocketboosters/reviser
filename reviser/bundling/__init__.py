import os
import zipfile

from reviser import definitions
from reviser.bundling import _installer


def _create_zip(target: "definitions.Target"):
    """
    Bundle together all of the source files into a single zip file that can
    be uploaded as an AWS Lambda function

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


def create(
    context: "definitions.Context",
    selection: "definitions.Selection",
    reinstall: bool = False,
):
    """
    Copies the entire contents of the project folder to a temporary location
    and then installs and bundles the copied project for deployment.

    :param context:
        The context in which this bundle action is taking place.
    :param selection:
        A selection object that defines the subset of targets to execute
        the bundling process upon.
    :param reinstall:
        Whether or not to force re-installation of dependencies for previously
        bundled targets.
    """
    selected = context.get_selected_targets(selection)

    for target in selected.targets:
        target.bundle_directory.mkdir(exist_ok=True, parents=True)

        skip_installs = (
            not reinstall
            and target.site_packages_directory.exists()
            and os.listdir(str(target.site_packages_directory))
        )
        if not skip_installs:
            _installer.install_dependencies(target)
        else:
            print("[DEPENDENCIES]: Using existing installation cache.")

        for copy_path in target.bundle.get_copy_paths():
            copy_path.copy()
            print(f"[COPIED]: {copy_path.source.relative_to(target.directory)}")

        _create_zip(target)

    return selected
