#!/usr/bin/env python3
"""
Module to act as a Prometheus Exporter for Docker containers with a
    healthcheck configured
"""

import argparse
import http.client
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

LISTEN_PORT = 8080
VERBOSE = int(os.environ.get('ALERTIFY_VERBOSE', 0))


class HTTPHandler(SimpleHTTPRequestHandler):
    """
    Class to encompass the requirements of a Prometheus Exporter
        for Docker containers with a healthcheck configured
    """

    # Override built-in method
    # pylint: disable=invalid-name
    def do_GET(self):
        """
        Method to handle GET requests
        """
        if self.path == '/healthcheck':
            if not healthy():
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
        self.send_response(int(status) or 500)
        self.end_headers()
        self.wfile.write(bytes(str(message).encode()))

    def _alerts(self):
        """
        Method to handle the request for alerts
        """
        if not healthy():
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

        if VERBOSE:
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

        if VERBOSE:
            print('Sending to Gotify:')
            print(json.dumps(gotify_msg, indent=2))
        response = 'Status: {status}, Reason: {reason}'.format(
            **gotify_send(
                os.environ['GOTIFY_SERVER'],
                os.environ['GOTIFY_PORT'],
                os.environ['GOTIFY_KEY'],
                gotify_msg
            )
        )

        if VERBOSE:
            print(response)
        self._respond(200, response)


def gotify_send(server, port, authkey, payload):
    """
    Function to POST data to a Gotify server
    """

    gotify = http.client.HTTPConnection(server, port)
    headers = {
        'X-Gotify-Key': authkey,
        'Content-type': 'application/json',
    }

    gotify.request('POST', '/message', json.dumps(payload), headers)
    response = gotify.getresponse()

    return {
        'status': response.status,
        'reason': response.reason
    }


def healthy():
    """
    Simple funtion to return if all the requirements are met
    """
    return all([
        'GOTIFY_SERVER' in os.environ,
        'GOTIFY_PORT' in os.environ,
        'GOTIFY_KEY' in os.environ,
    ])


if __name__ == '__main__':
    def cli_parse():
        """
        Function to parse the CLI
        """
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Bridge between Prometheus Alertmanager and Gotify\n',
            epilog='Three environment variables are required to be set:\n'
                   '  * GOTIFY_SERVER: hostname of the Gotify server\n'
                   '  * GOTIFY_PORT: port of the Gotify server\n'
                   '  * GOTIFY_KEY: app token for alertify'
        )

        parser.add_argument(
            '-H', '--healthcheck',
            action='store_true',
            help='Simply exit with 0 for healthy or 1 when unhealthy',
        )

        return parser.parse_args()

    def main():
        """
        main()
        """
        args = cli_parse()

        if args.healthcheck:
            # Invert the sense of 'healthy' for Unix CLI usage
            return not healthy()

        print(f'Starting web server on port {LISTEN_PORT}')
        try:
            HTTPServer(('', LISTEN_PORT), HTTPHandler).serve_forever()
        except KeyboardInterrupt:
            print('Exiting')

        return 0

    sys.exit(main())
