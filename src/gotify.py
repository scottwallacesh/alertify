"""
Module to handle communication with the Gotify server
"""
import http.client
import json


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
            print(f'DEBUG: Sending to Gotify: {body}')

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
            print(f'DEBUG: Returned from Gotify: {json.dumps(resp_obj, indent=2)}')
            print('DEBUG: Status: {status}, Reason: {reason}'.format(**resp_obj))

        return resp_obj

    def delete(self, msg_id):
        """
        Method to delete a message from the Gotify server
        """
        if self.verbose:
            print(f'DEBUG: Deleting message ID {msg_id}')
        return self._call('DELETE', f'/message/{msg_id}')

    def find_byfingerprint(self, message):
        """
        Method to return the ID of a matching message
        """
        try:
            new_fingerprint = message['fingerprint']
        except KeyError:
            if self.verbose:
                print('DEBUG: No fingerprint found in new message')
            return None

        for old_message in self.messages():
            try:
                old_fingerprint = old_message['extras']['alertify']['fingerprint']
                if old_fingerprint == new_fingerprint:
                    return old_message['id']
            except KeyError:
                if self.verbose:
                    print(
                        f'DEBUG: No fingerprint found in message {old_message["id"]}'
                    )
                continue

        if self.verbose:
            print('DEBUG: No fingerprint matched.')
        return None

    def messages(self):
        """
        Method to return a list of messages from the Gotify server
        """
        if not self.client_key and self.verbose:
            print('DEBUG: No client key is configured.  No messages could be retrieved.')
            return []
        if self.verbose:
            print('DEBUG: Fetching existing messages from Gotify')
        return self._call('GET', '/message')['json'].get('messages', [])

    def send_alert(self, payload):
        """
        Method to send a message payload to a Gotify server
        """
        if self.verbose:
            print('DEBUG: Sending message to Gotify')
        return self._call('POST', '/message', body=json.dumps(payload, indent=2))
