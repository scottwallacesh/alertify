"""
Alertify module to act as a bridge between Prometheus Alertmanager and Gotify
"""
# pylint: disable=invalid-name

__author__ = 'Scott Wallace'
__email__ = 'scott@wallace.sh'
__maintainer__ = 'Scott Wallace'

__version__ = '2.0'

import json
import logging

import werkzeug.exceptions
from flask import Flask, request, request_started
from flask_classful import FlaskView, route

from .config import Config
from .gotify import Gotify
from .health import Healthcheck
from .messaging import MessageHandler

webapp = Flask(__name__)

# FIXME: * Find a better way to deny FlaskView methods without using a `_`
#          prefix or raising a NotFound exception


class Alertify(FlaskView):
    """
    Main Alertify class
    """

    route_base = '/'
    trailing_slash = False

    def __init__(self):
        # Instantiate with defaults
        self.configure()

    def configure(self, configfile=None):
        """
        Configure from a configfile
        """
        # Deny via HTTP
        if request:
            raise werkzeug.exceptions.NotFound

        self.config = Config(configfile)
        self.gotify = Gotify(
            self.config.gotify_server,
            self.config.gotify_port,
            self.config.gotify_key_app,
            self.config.gotify_key_client,
        )
        self.msg_hndlr = MessageHandler(
            self.gotify,
            self.config.disable_resolved,
            self.config.delete_onresolve,
        )

    def run(self):
        """
        Listen on port and run webserver
        """
        # Deny via HTTP
        if request:
            raise werkzeug.exceptions.NotFound

        webapp.run(host='0.0.0.0', port=self.config.listen_port)

    @route('/alert', methods=['POST'])
    def alert(self):
        """
        Handle the alerts from Alertmanager
        """
        message = request.get_json()

        logging.debug(
            'Received from Alertmanager:\n%s',
            json.dumps(message, indent=2),
        )

        for alertmsg in message['alerts']:
            response = self.msg_hndlr.process(alertmsg)
        try:
            return response['reason'], response['status']
        except UnboundLocalError:
            return '', 204

    def healthcheck(self):
        """
        Perform a healthcheck and return the results
        """
        response = Healthcheck(self.gotify).gotify_alive()
        return response['reason'], response['status']


Alertify.register(webapp)
