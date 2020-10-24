"""
Alertify module to act as a bridge between Prometheus Alertmanager and Gotify
"""

__author__ = 'Scott Wallace'
__email__ = 'scott@wallace.sh'
__maintainer__ = 'Scott Wallace'

__version__ = '1.5'

from .config import Config
from .gotify import Gotify
from .server import Server
from .healthcheck import Healthcheck
from .messaging import MessageHandler


class Alertify:
    """
    Class for Alertify
    """

    def __init__(self, configfile=None):
        self.config = Config(configfile)
        self.gotify = Gotify(
            self.config.gotify_server,
            self.config.gotify_port,
            self.config.gotify_key,
            self.config.gotify_client,
        )
        self.message_handler = MessageHandler(
            self.gotify,
            self.config.disable_resolved,
            self.config.delete_onresolve,
        )
        self.healthcheck = Healthcheck(self.gotify)
        self.server = Server(
            self.config.listen_port,
            self.message_handler,
            self.healthcheck,
        )
