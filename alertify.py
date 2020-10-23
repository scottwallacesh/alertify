#!/usr/bin/env python3
"""
Module to act as a bridge between Prometheus Alertmanager and Gotify
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
    'delete_onresolve': bool(False),
    'disable_resolved': bool(False),
    'gotify_client': str(),
    'gotify_key': str(),
    'gotify_port': int(80),
    'gotify_server': str('localhost'),
    'listen_port': int(8080),
    'verbose': bool(False),
}


class Gotify:
    """
    Class to handle Gotify communications
    """
    verbose = False

    def __init__(self, server, port, app_key, client_key=None):
        self.api = http.client.HTTPConnection(server, port)
        self.app_key = app_key
        self.client_key = client_key
        self.base_headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }

    def _call(self, method, url, body=None):
        """
        Method to call Gotify with an app or client key as appropriate
        """
        headers = self.base_headers.copy()
        if method in ['GET', 'DELETE']:
            headers['X-Gotify-Key'] = self.client_key
        else:
            headers['X-Gotify-Key'] = self.app_key

        if self.verbose:
            print('Sending to Gotify:')
            print(body)

        try:
            self.api.request(method, url, body=body, headers=headers)
            response = self.api.getresponse()
        except ConnectionRefusedError as error:
            print(f'ERROR: {error}')
            return {
                'status': error.errno,
                'reason': error.strerror
            }

        resp_obj = {
            'status': response.status,
            'reason': response.reason,
            'json': None
        }
        rawbody = response.read()
        if len(rawbody) > 0:
            try:
                resp_obj['json'] = json.loads(rawbody.decode())
            except json.decoder.JSONDecodeError as error:
                print(f'ERROR: {error}')

        if self.verbose:
            print('Returned from Gotify:')
            print(json.dumps(resp_obj, indent=2))
            print('Status: {status}, Reason: {reason}'.format(**resp_obj))

        return resp_obj

    def delete(self, msg_id):
        """
        Method to delete a message from the Gotify server
        """
        if self.verbose:
            print(f'Deleting message ID {msg_id}')
        return self._call('DELETE', f'/message/{msg_id}')

    def find_byfingerprint(self, message):
        """
        Method to return the ID of a matching message
        """
        try:
            new_fingerprint = message['fingerprint']
        except KeyError:
            if self.verbose:
                print('No fingerprint found in new message')
            return None

        for old_message in self.messages():
            try:
                old_fingerprint = old_message['extras']['alertify']['fingerprint']
                if old_fingerprint == new_fingerprint:
                    return old_message['id']
            except KeyError:
                if self.verbose:
                    print(
                        f'No fingerprint found in message {old_message["id"]}')
                continue

        return None

    def messages(self):
        """
        Method to return a list of messages from the Gotify server
        """
        if self.verbose:
            print('Fetching existing messages from Gotify')
        return self._call('GET', '/message')['json'].get('messages', None)

    def send_alert(self, payload):
        """
        Method to send a message payload to a Gotify server
        """
        if self.verbose:
            print('Sending message to Gotify')
        return self._call('POST', '/message', body=json.dumps(payload, indent=2))


class HTTPHandler(SimpleHTTPRequestHandler):
    """
    Class to handle the HTTP requests from a client
    """
    config = None

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
            am_msg = json.loads(rawdata.decode())
        except json.decoder.JSONDecodeError as error:
            print(f'ERROR: Bad JSON: {error}')
            self._respond(400, f'Bad JSON: {error}')
            return

        if self.config.get('verbose'):
            print('Received from Alertmanager:')
            print(json.dumps(am_msg, indent=2))

        gotify = Gotify(
            self.config.get('gotify_server'),
            self.config.get('gotify_port'),
            self.config.get('gotify_key'),
            self.config.get('gotify_client')
        )

        if self.config.get('verbose'):
            gotify.verbose = True

        for alert in am_msg['alerts']:
            try:
                if alert['status'] == 'resolved':
                    if self.config.get('disable_resolved'):
                        print('Ignoring resolved messages')
                        self._respond(
                            200, 'Ignored. "resolved" messages are disabled')
                        continue
                    if self.config.get('delete_onresolve'):
                        alert_id = gotify.find_byfingerprint(alert)
                        if alert_id:
                            response = gotify.delete(alert_id)
                        continue
                    prefix = 'Resolved'
                else:
                    prefix = alert['labels'].get(
                        'severity', 'warning').capitalize()

                gotify_msg = {
                    'title': '{}: {}'.format(
                        prefix,
                        alert['annotations'].get('summary'),
                    ),
                    'message': '{}: {}'.format(
                        alert['labels'].get('instance', '[unknown]'),
                        alert['annotations'].get('description', '[nodata]'),
                    ),
                    'priority': int(alert['labels'].get('priority', 5)),
                    'extras': {
                        'alertify': {
                            'fingerprint': alert.get('fingerprint', None)
                        }
                    }
                }
            except KeyError as error:
                print(f'ERROR: KeyError: {error}')
                self._respond(400, f'Missing field: {error}')
                return

            response = gotify.send_alert(gotify_msg)

        try:
            self._respond(response['status'], response['reason'])
        except UnboundLocalError:
            self._respond('204', '')

    def _respond(self, status, message):
        """
        Method to output a simple HTTP status and string to the client
        """
        self.send_response(int(status) or 500)
        self.end_headers()
        self.wfile.write(bytes(str(message).encode()))

    # Override built-in method
    def do_GET(self):   # pylint: disable=invalid-name
        """
        Method to handle GET requests
        """
        if self.path == '/healthcheck':
            if not healthy(self.config):
                print('ERROR: Check requirements')
                self._respond(500, 'ERR')

            self._respond(200, 'OK')

    # Override built-in method
    def do_POST(self):  # pylint: disable=invalid-name
        """
        Method to handle POST requests from AlertManager
        """
        if self.path == '/alert':
            self._alerts()

    # FIXME: This isn't right.  A normal method doesn't work, however.
    @classmethod
    def set_config(cls, config):
        """
        Classmethod to add config to the class
        """
        cls.config = config


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
        print(
            f'Config:\n'
            f'{yaml.dump(config, explicit_start=True, default_flow_style=False)}'
        )
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
