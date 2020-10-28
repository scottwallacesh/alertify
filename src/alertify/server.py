"""
Module to act as a bridge between Prometheus Alertmanager and Gotify
"""

import json
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler


class Server:
    """
    Class to handle the webserver for Alertify
    """

    def __init__(self, port, message_handler, healthcheck):
        self.port = port
        self.message_handler = message_handler
        self.healthcheck = healthcheck

    def listen_and_run(self):
        """
        Method to bind to the port and run indefinitely
        """
        logging.info('Starting web server on port %d', self.port)

        # FIXME: Find a better way to handle the injection of these values
        http_handler = self.HTTPHandler
        http_handler.message_handler = self.message_handler
        http_handler.healthcheck = self.healthcheck

        try:
            with HTTPServer(('', self.port), http_handler) as webserver:
                webserver.serve_forever()
                return True
        except KeyboardInterrupt:
            logging.info('Exiting')

    class HTTPHandler(SimpleHTTPRequestHandler):
        """
        Class to handle the HTTP requests from a client
        """

        def _respond(self, status, message):
            """
            Method to output a simple HTTP status and string to the client
            """
            self.send_response(int(status) or 500)
            self.end_headers()
            self.wfile.write(bytes(str(message).encode()))

        def do_GET(self):  # pylint: disable=invalid-name
            """
            Method to handle GET requests
            """
            if self.path == '/healthcheck':
                response = self.healthcheck.gotify_alive()
                self._respond(response['status'], response['reason'])

        def do_POST(self):  # pylint: disable=invalid-name
            """
            Method to handle POST requests from AlertManager
            """
            if self.path == '/alert':
                try:
                    content_length = int(self.headers['Content-Length'])
                    message = json.loads(self.rfile.read(content_length).decode())
                except json.decoder.JSONDecodeError as error:
                    logging.error('Bad JSON: %s', error)
                    self._respond(400, f'Bad JSON: {error}')

                logging.debug(
                    'Received from Alertmanager:\n%s',
                    json.dumps(message, indent=2),
                )

                for alert in message['alerts']:
                    response = self.message_handler.process(alert)
                try:
                    self._respond(response['status'], response['reason'])
                except UnboundLocalError:
                    self._respond('204', '')
