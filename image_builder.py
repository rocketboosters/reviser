import argparse
import os
import pathlib
import textwrap

import toml

HUB_PREFIX = "swernst/reviser"
MY_DIRECTORY = pathlib.Path(__file__).parent.absolute()
PROJECT_DATA = toml.loads(MY_DIRECTORY.joinpath('pyproject.toml').read_text())
VERSION = PROJECT_DATA['tool']['poetry']['version']
BUILDS = {
    "3.8": {"build_args": {"PYTHON_VERSION": "3.8"}},
}


def build(python_version: str, spec: dict, args: argparse.Namespace) -> dict:
    """Builds the container from the specified docker file path"""
    path = MY_DIRECTORY.joinpath("Dockerfile")

    version = "{}{}".format(
        "pre-" if args.pre else "",
        VERSION,
    )
    generic = "pre" if args.pre else "latest"

    tags = [
        "{}:{}-{}".format(HUB_PREFIX, version, python_version),
        "{}:{}-{}".format(HUB_PREFIX, generic, python_version),
    ]
    if not args.pre:
        tags.append("{}:current-{}".format(HUB_PREFIX, python_version))

    parts = ["docker", "build", "--pull", f'--file="{path}"']
    if not args.cache:
        parts.append("--no-cache")

    for key, value in spec["build_args"].items():
        parts.append(f"--build-arg {key}={value}")

    for tag in tags:
        parts.append(f"--tag={tag}")

    command = " ".join(parts + ["."])

    print("[BUILDING]:", python_version)
    if args.dry_run:
        print("[DRY-RUN]: Skipped building command")
        print(textwrap.indent(command.replace(" -", "\n   -"), "   "))
    else:
        os.environ["DOCKER_BUILDKIT"] = "1"
        os.system(command)

    return dict(spec=spec, id=python_version, path=path, command=command, tags=tags)


def publish(build_entry: dict, args: argparse.Namespace):
    """Publishes the specified build entry to docker hub"""
    for tag in build_entry["tags"]:
        if args.dry_run:
            print("[DRY-RUN]: Skipped pushing {}".format(tag))
        else:
            print("[PUSHING]:", tag)
            os.system("docker push {}".format(tag))


def parse() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--publish",
        action="store_true",
        help="Whether or not to publish images after building them.",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Allows the docker build to use existing cache.",
    )
    parser.add_argument(
        "-i",
        "--id",
        dest="ids",
        action="append",
        help=textwrap.dedent(
            """
            One or more build identifiers to build. If not specified
            all images will be built. This flag can be specified multiple
            times in a single command.
            """,
        ),
    )
    parser.add_argument(
        "--pre",
        action="store_true",
        help=textwrap.dedent(
            """
            If true images will be built with a "pre" in the version
            identifier and "current" images will be skipped. This is
            used to publish images for pre-releases to the hub prior
            to the official release.
            """,
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=textwrap.dedent(
            """
            When set, the actual build process is skipped and instead
            the build command is printed showing what would have been
            executed.
            """,
        ),
    )
    return parser.parse_args()


def run():
    """Execute the build process"""
    args = parse()

    build_results = [
        build(python_version, spec, args)
        for python_version, spec in BUILDS.items()
        if not args.ids or python_version in args.ids
    ]

    if not args.publish:
        return

    for entry in build_results:
        publish(entry, args)


if __name__ == "__main__":
    run()
