import pathlib as _pathlib
from importlib import metadata as _metadata

import toml as _toml

try:
    from reviser.interactivity import run_shell  # noqa
except ImportError as error:

    def run_shell(*args, **kwargs):
        """Replacement shell when import fails due to missing dependencies."""
        raise error


try:
    __version__ = _metadata.version(__package__)
except _metadata.PackageNotFoundError:  # pragma: no-cover
    # If the package is not installed such that it has distribution metadata
    # fallback to loading the version from the pyproject.toml file.
    __version__ = _toml.loads(
        _pathlib.Path(__file__).parent.parent.joinpath("pyproject.toml").read_text()
    )["tool"]["poetry"]["version"]
