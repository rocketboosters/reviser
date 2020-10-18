try:
    from reviser.interactivity import run_shell  # noqa
except ImportError as error:
    def run_shell(*args, **kwargs):
        """Replacement shell when import fails due to missing dependencies."""
        raise error

__version_info__ = (0, 1, 0)
__version__ = '.'.join([f'{v}' for v in __version_info__])

DEFAULT_RUNTIME = '3.8'
