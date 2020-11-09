import pathlib as _pathlib
from importlib import metadata as _metadata

try:
    from reviser.interactivity import run_shell  # noqa
except ImportError as error:
    _stored_error = error

    def run_shell(*args, **kwargs):  # type:ignore
        """Replacement shell when import fails due to missing dependencies."""
        global _stored_error
        raise _stored_error


try:
    __version__ = _metadata.version(__package__)
except _metadata.PackageNotFoundError:  # pragma: no-cover
    # If the package is not installed such that it has distribution metadata
    # fallback to loading the version from the pyproject.toml file.
    import toml as _toml

    __version__ = _toml.loads(
        _pathlib.Path(__file__).parent.parent.joinpath("pyproject.toml").read_text()
    )["tool"]["poetry"]["version"]
