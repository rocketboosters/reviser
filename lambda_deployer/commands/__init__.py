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

COMMANDS = {
    '?': helper,
    'alias': aliaser,
    'bundle': bundler,
    'configs': configer,
    'deploy': deployer,
    'exit': exiter,
    'help': helper,
    'list': lister,
    'prune': pruner,
    'push': pusher,
    'reload': reloader,
    'select': selector,
    'shell': sheller,
    'status': reporter,
}
