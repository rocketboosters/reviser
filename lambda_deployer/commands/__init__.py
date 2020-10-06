from ..commands import aliaser
from ..commands import bundler
from ..commands import configer
from ..commands import deployer
from ..commands import lister
from ..commands import pruner
from ..commands import pusher
from ..commands import reloader
from ..commands import reporter
from ..commands import selector

COMMANDS = {
    'alias': aliaser,
    'bundle': bundler,
    'configs': configer,
    'deploy': deployer,
    'list': lister,
    'prune': pruner,
    'push': pusher,
    'reload': reloader,
    'select': selector,
    'status': reporter,
}
