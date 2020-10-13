#!/usr/bin/env python3
"""
Module to act as a Prometheus Exporter for Docker containers with a
    healthcheck configured
"""

import argparse
import http.client
import json
import logging
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

LISTEN_PORT = 8080

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


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
            self._healthcheck()

    # Override built-in method
    # pylint: disable=invalid-name
    def do_POST(self):
        """
        Method to handle POST requests from AlertManager
        """
        if self.path == '/alert':
            self._alerts()

    def _healthcheck(self, message=True):
        """
        Method to return 200 or 500 response and an optional message
        """
        if not healthy():
            self.send_response(500)
            self.end_headers()
            if message:
                self.wfile.write(b'ERR')
            return False

        self.send_response(200)
        self.end_headers()
        if message:
            self.wfile.write(b'OK')
        return True

    def _alerts(self):
        """
        Method to handle the request for alerts
        """
        if not self._healthcheck(message=False):
            return

        content_length = int(self.headers['Content-Length'])
        rawdata = self.rfile.read(content_length)

        alert = json.loads(rawdata.decode())

        if alert['status'] == 'resolved':
            prefix = 'Resolved'
        else:
            prefix = alert['commonLabels'].get('severity', 'default').capitalize()

        gotify_msg = {
            'message': '{}: {}'.format(
                prefix,
                alert['commonAnnotations'].get('description', '...')
            ),
            'priority': int(alert['commonLabels'].get('priority', 5))
        }

        (status, reason) = gotify_send(
            os.environ['GOTIFY_SERVER'],
            os.environ['GOTIFY_PORT'],
            os.environ['GOTIFY_KEY'],
            gotify_msg
        )

        self.wfile.write(f'Status: {status}, Reason: {reason}'.encode())


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

    return (response.status, response.reason)


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

        HTTPServer(('', LISTEN_PORT), HTTPHandler).serve_forever()

        return 0

    sys.exit(main())
