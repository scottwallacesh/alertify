"""
Module to handle communication with the Gotify server
"""
import http.client
import json
import logging


class Gotify:
    """
    Class to handle Gotify communications
    """

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

        logging.debug('Sending to Gotify:\n%s', body)

        try:
            self.api.request(method, url, body=body, headers=headers)
            response = self.api.getresponse()
        except ConnectionRefusedError as error:
            logging.error(error)
            return {
                'status': error.errno,
                'reason': error.strerror,
            }

        resp_obj = {
            'status': response.status,
            'reason': response.reason,
            'json': None,
        }
        rawbody = response.read()
        if len(rawbody) > 0:
            try:
                resp_obj['json'] = json.loads(rawbody.decode())
            except json.decoder.JSONDecodeError as error:
                logging.error(error)

        logging.debug('Returned from Gotify:\n%s', json.dumps(resp_obj, indent=2))
        logging.debug('Status: %s, Reason: %s', resp_obj['status'], resp_obj['reason'])

        return resp_obj

    def delete(self, msg_id):
        """
        Method to delete a message from the Gotify server
        """
        logging.debug('Deleting message ID: %s', msg_id)
        return self._call('DELETE', f'/message/{msg_id}')

    def find_byfingerprint(self, message):
        """
        Method to return the ID of a matching message
        """
        try:
            new_fingerprint = message['fingerprint']
        except KeyError:
            logging.debug('No fingerprint found in new message')
            return None

        for old_message in self.messages():
            try:
                old_fingerprint = old_message['extras']['alertify']['fingerprint']
                if old_fingerprint == new_fingerprint:
                    return old_message['id']
            except KeyError:
                logging.debug(
                    'No fingerprint found in message ID: %s',
                    old_message['id'],
                )
                continue

        logging.debug('No fingerprint matched.')
        return None

    def messages(self):
        """
        Method to return a list of messages from the Gotify server
        """
        if not self.client_key:
            logging.debug(
                'No client key is configured.  No messages could be retrieved.'
            )
            return []
        logging.debug('Fetching existing messages from Gotify')
        return self._call('GET', '/message')['json'].get('messages', [])

    def send_alert(self, payload):
        """
        Method to send a message payload to a Gotify server
        """
        logging.debug('Sending message to Gotify')
        return self._call('POST', '/message', body=json.dumps(payload, indent=2))
