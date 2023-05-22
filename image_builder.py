"""Build and optionally push the reviser container images to dockerhub."""
import argparse
import os
import pathlib
import textwrap
import typing

import toml

HUB_PREFIXES = ["docker.io/swernst/reviser", "docker.io/rocketboosters/reviser"]
MY_DIRECTORY = pathlib.Path(__file__).parent.absolute()
PROJECT_DATA = toml.loads(MY_DIRECTORY.joinpath("pyproject.toml").read_text())
VERSION = PROJECT_DATA["tool"]["poetry"]["version"]
BUILDS = {
    "3.8": {"build_args": {"PYTHON_VERSION": "3.8"}},
    "3.9": {"build_args": {"PYTHON_VERSION": "3.9"}},
}


def _append_to_script(script_path: pathlib.Path, *args: str):
    """Append the lines of args to the script path file."""
    print("[SCRIPT]: Writing command to script.")
    with open(script_path, mode="a") as f:
        f.write("\n".join(args).replace(" --", " \\\n   --"))
        f.write("\n")


def _get_tags(args: argparse.Namespace, python_version: str) -> typing.List[str]:
    """Create a list of tags to apply to the built image."""
    version = "{}{}".format(
        "pre-" if args.pre else "",
        VERSION,
    )
    generic = "pre" if args.pre else "latest"

    tags: typing.List[str] = []
    for prefix in HUB_PREFIXES:
        tags += [
            "{}:{}-{}".format(prefix, version, python_version),
            "{}:{}-{}".format(prefix, generic, python_version),
        ]
        if not args.pre:
            tags.append("{}:current-{}".format(prefix, python_version))

    return tags


def build(
    python_version: str,
    spec: typing.Dict[str, typing.Any],
    args: argparse.Namespace,
    script_path: typing.Optional[pathlib.Path] = None,
) -> typing.Dict[str, typing.Any]:
    """Build the container from the specified docker file path."""
    path = "./Dockerfile"
    tags = _get_tags(args, python_version)
    parts = ["docker", "build", "--pull", f'--file="{path}"']
    if not args.cache:
        parts.append("--no-cache")

    for key, value in spec["build_args"].items():
        parts.append(f"--build-arg {key}={value}")

    for tag in tags:
        parts.append(f"--tag={tag}")

    command = " ".join(parts + ["."])

    print("[BUILDING]:", python_version)
    print(textwrap.indent(command.replace(" -", "\n   -"), "   "))

    if args.dry_run:
        print("[DRY-RUN]: Skipped building command")
    elif script_path:
        _append_to_script(script_path, command)
    else:
        os.environ["DOCKER_BUILDKIT"] = "1"
        os.system(command)

    return dict(spec=spec, id=python_version, path=path, command=command, tags=tags)


def publish(
    build_entry: dict,
    args: argparse.Namespace,
    script_path: typing.Optional[pathlib.Path] = None,
):
    """Publish the specified build entry to docker hub."""
    for tag in build_entry["tags"]:
        command = "docker push {}".format(tag)
        print(f"[PUSH]: Pushing tag {tag}")
        print(textwrap.indent(command.replace(" -", "\n   -"), "   "))

        if args.dry_run:
            print("[DRY-RUN]: Skipped pushing {}".format(tag))
        elif script_path:
            _append_to_script(script_path, command)
        else:
            os.system(command)


def parse() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--publish",
        "--push",
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
    parser.add_argument(
        "--script-path",
        help=textwrap.dedent(
            """
            When specified, the commands will be written to a script instead of
            executed. This is used for multi-stage CI where Python execution and
            docker commands cannot be easily colocated.
            """
        ),
    )
    return parser.parse_args()


def _initialize_script_path(args: argparse.Namespace) -> typing.Optional[pathlib.Path]:
    """Initialize the output script if it exists."""
    if not args.script_path:
        return None

    p = pathlib.Path(args.script_path).resolve()
    p.write_text('#!/bin/sh\nexport DOCKER_BUILDKIT="1"\n')
    p.chmod(0o775)
    return p


def run():
    """Execute the build process."""
    args = parse()
    script_path = _initialize_script_path(args)

    build_results = [
        build(python_version, spec, args, script_path)
        for python_version, spec in BUILDS.items()
        if not args.ids or python_version in args.ids
    ]

    if not args.publish:
        return

    for entry in build_results:
        publish(entry, args, script_path)


if __name__ == "__main__":
    run()
