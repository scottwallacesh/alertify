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
                    for alert_id in self.gotify.find_byfingerprint(alert):
                        if not self.gotify.delete(alert_id):
                            logging.error('There was a problem removing message ID %d', alert_id)

                prefix = 'resolved'
            else:
                prefix = alert['labels'].get('severity', 'warning')

            instance = alert['labels'].get('instance', None)

            gotify_msg = {
                'title': '[{}] {}'.format(
                    prefix.upper(),
                    alert['annotations'].get('summary'),
                ),
                'message': '{}{}'.format(
                    f'{instance}: ' if instance else '',
                    alert['annotations'].get('description', ''),
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
