from collections import defaultdict as _defaultdict

from ..commands import aliaser
from ..commands import bundler
from ..commands import configer
from ..commands import deployer
from ..commands import exiter
from ..commands import helper
from ..commands import lister
from ..commands import pruner
from ..commands import pusher
from ..commands import reloader
from ..commands import reporter
from ..commands import selector
from ..commands import sheller

#: Commands available to the shell.
COMMANDS = {
    "alias": aliaser,
    "bundle": bundler,
    "configs": configer,
    "deploy": deployer,
    "exit": exiter,
    "help": helper,
    "list": lister,
    "prune": pruner,
    "push": pusher,
    "reload": reloader,
    "select": selector,
    "shell": sheller,
    "status": reporter,
}

#: Aliases of commands to make available to the shell.
ALIASES = {
    "?": "help",
}


def _invert_aliases():
    """Reverses the alias dictionary to be a lookup from command to aliases."""
    out = _defaultdict(list)
    for alias, name in ALIASES.items():
        out[name].append(alias)
    return out


#: List of aliases assigned to shell commands for documentation purposes.
REVERSED_ALIASES = _invert_aliases()


def get_module(command: str):
    """Retrieves the command module for the associated command."""
    return COMMANDS.get(ALIASES.get(command, command), None)
