#!/usr/bin/env python3
"""
Module to act as a Prometheus Exporter for Docker containers with a
    healthcheck configured
"""

import argparse
import functools
import http.client
import json
import os
import sys
from distutils.util import strtobool
from http.server import HTTPServer, SimpleHTTPRequestHandler

import yaml

DEFAULTS = {
    'listen_port': int(8080),
    'gotify_server': str('localhost'),
    'gotify_port': int(80),
    'gotify_key': str(),
    'verbose': bool(False),
}


class HTTPHandler(SimpleHTTPRequestHandler):
    """
    Class to encompass the requirements of a Prometheus Exporter
        for Docker containers with a healthcheck configured
    """

    config = None

    @staticmethod
    def set_config(config):
        """
        Method
        """
        HTTPHandler.config = config

    # Override built-in method
    # pylint: disable=invalid-name
    def do_GET(self):
        """
        Method to handle GET requests
        """
        if self.path == '/healthcheck':
            if not healthy(self.config):
                print('ERROR: Check requirements')
                self._respond(500, 'ERR')

            self._respond(200, 'OK')

    # Override built-in method
    # pylint: disable=invalid-name
    def do_POST(self):
        """
        Method to handle POST requests from AlertManager
        """
        if self.path == '/alert':
            self._alerts()

    def _respond(self, status, message):
        """
        Method to output a simple HTTP status and string to the client
        """
        self.send_response(int(status) or 500)
        self.end_headers()
        self.wfile.write(bytes(str(message).encode()))

    def _alerts(self):
        """
        Method to handle the request for alerts
        """
        if not healthy(self.config):
            print('ERROR: Check requirements')
            self._respond(500, 'Server not configured correctly')
            return

        content_length = int(self.headers['Content-Length'])
        rawdata = self.rfile.read(content_length)

        try:
            alert = json.loads(rawdata.decode())
        except json.decoder.JSONDecodeError as error:
            print(f'ERROR: Bad JSON: {error}')
            self._respond(400, f'Bad JSON: {error}')
            return

        if self.config.get('verbose'):
            print('Received from Alertmanager:')
            print(json.dumps(alert, indent=2))

        try:
            if alert['status'] == 'resolved':
                prefix = 'Resolved'
            else:
                prefix = alert['commonLabels'].get(
                    'severity', 'default').capitalize()

            gotify_msg = {
                'title': '{}: {}'.format(
                    alert['receiver'],
                    alert['commonLabels'].get('instance', 'Unknown')
                ),
                'message': '{}: {}'.format(
                    prefix,
                    alert['commonAnnotations'].get('description', '...')
                ),
                'priority': int(alert['commonLabels'].get('priority', 5))
            }
        except KeyError as error:
            print(f'ERROR: KeyError: {error}')
            self._respond(400, f'Missing field: {error}')
            return

        if self.config.get('verbose'):
            print('Sending to Gotify:')
            print(json.dumps(gotify_msg, indent=2))

        response = gotify_send(
            self.config.get('gotify_server'),
            self.config.get('gotify_port'),
            self.config.get('gotify_key'),
            gotify_msg
        )

        if self.config.get('verbose'):
            print('Status: {status}, Reason: {reason}'.format(**response))
        self._respond(response['status'], response['reason'])


def gotify_send(server, port, authkey, payload):
    """
    Function to POST data to a Gotify server
    """

    gotify = http.client.HTTPConnection(server, port)
    headers = {
        'X-Gotify-Key': authkey,
        'Content-type': 'application/json',
    }

    try:
        gotify.request('POST', '/message', json.dumps(payload), headers)
        response = gotify.getresponse()
    except ConnectionRefusedError as error:
        print(f'ERROR: {error}')
        return {
            'status': error.errno,
            'reason': error.strerror
        }

    return {
        'status': response.status,
        'reason': response.reason
    }


def healthy(config):
    """
    Simple function to return if all the requirements are met
    """
    return all([
        len(config.get('gotify_key', ''))
    ])


@functools.lru_cache
def parse_config(configfile):
    """
    Function to parse a configuration file
    """
    config = {}

    try:
        with open(configfile, 'r') as file:
            parsed = yaml.safe_load(file.read())
    except FileNotFoundError as error:
        print(f'WARN: {error}')
        parsed = {}

    # Iterate over the DEFAULTS dictionary and check for environment variables
    #   of the same name, then check for any items in the YAML config, otherwise
    #   use the default values.
    # Ensure the types are adhered to.
    for key, val in DEFAULTS.items():
        config[key] = os.environ.get(key.upper(), parsed.get(key, val))
        if isinstance(val, bool):
            config[key] = strtobool(str(config[key]))
        else:
            config[key] = type(val)(config[key])

    if config['verbose']:
        print(f'Config:\n{yaml.dump(config, explicit_start=True, default_flow_style=False)}')
    return config


if __name__ == '__main__':
    def parse_cli():
        """
        Function to parse the CLI
        """
        maxlen = max([len(key) for key in DEFAULTS])
        defaults = [
            f'  * {key.upper().ljust(maxlen)} (default: {val if val != "" else "None"})'
            for key, val in DEFAULTS.items()
        ]

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Bridge between Prometheus Alertmanager and Gotify\n',
            epilog='The following environment variables will override any config or default:\n' +
                   '\n'.join(defaults)
        )

        parser.add_argument(
            '-c', '--config',
            default=f'{os.path.splitext(__file__)[0]}.yaml',
            help=f'path to config YAML.  (default: {os.path.splitext(__file__)[0]}.yaml)',
        )

        parser.add_argument(
            '-H', '--healthcheck',
            action='store_true',
            help='simply exit with 0 for healthy or 1 when unhealthy',
        )

        return parser.parse_args()

    def main():
        """
        main()
        """
        args = parse_cli()
        config = parse_config(args.config)

        if args.healthcheck:
            # Invert the sense of 'healthy' for Unix CLI usage
            return not healthy(config)

        listen_port = config.get('listen_port')

        print(f'Starting web server on port {listen_port}')
        try:
            with HTTPServer(('', listen_port), HTTPHandler) as webserver:
                HTTPHandler.set_config(config)
                webserver.serve_forever()
        except KeyboardInterrupt:
            print('Exiting')

        return 0

    sys.exit(main())
