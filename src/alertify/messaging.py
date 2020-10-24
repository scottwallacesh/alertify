"""
Module for handling the messaging
"""
import logging


class MessageHandler:
    """
    Class to handle alert messaging
    """

    def __init__(self, gotify_client, disable_resolved=False, delete_onresolve=False):
        self.gotify = gotify_client
        self.disable_resolved = disable_resolved
        self.delete_onresolve = delete_onresolve

    def process(self, alert):
        """
        Method to process the alert message
        """
        try:
            if alert['status'] == 'resolved':
                if self.disable_resolved:
                    logging.info('Ignoring resolved messages')
                    return {
                        'status': 200,
                        'reason': 'Ignored. "resolved" messages are disabled',
                    }

                if self.delete_onresolve:
                    alert_id = self.gotify.find_byfingerprint(alert)
                    if alert_id:
                        return self.gotify.delete(alert_id)
                    logging.warning('Could not find a matching message to delete.')

                prefix = 'resolved'
            else:
                prefix = alert['labels'].get('severity', 'warning')

            gotify_msg = {
                'title': '[{}] {}'.format(
                    prefix.upper(),
                    alert['annotations'].get('summary'),
                ),
                'message': '{}: {}'.format(
                    alert['labels'].get('instance', '[unknown]'),
                    alert['annotations'].get('description', '[nodata]'),
                ),
                'priority': int(alert['labels'].get('priority', 5)),
                'extras': {
                    'alertify': {
                        'fingerprint': alert.get('fingerprint', None),
                    }
                },
            }
        except KeyError as error:
            logging.error('KeyError: %s', error)
            return {
                'status': 400,
                'reason': f'Missing field: {error}',
            }

        return self.gotify.send_alert(gotify_msg)
