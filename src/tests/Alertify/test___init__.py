"""Test"""
import unittest
from unittest.mock import patch

import flask

import Alertify  # pylint: disable=import-error


class AlertifyTest(unittest.TestCase):
    """
    Tests for methods in the Alertify class.
    """

    @classmethod
    def setUpClass(cls):
        cls.alertify = Alertify.Alertify()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_configure(self):
        """Test"""
        self.alertify.configure(None)
        self.assertDictEqual(
            self.alertify.config.defaults(),
            Alertify.Config.defaults(),
        )

    @patch('Alertify.messaging.MessageHandler.process')
    def test_alert(self, mock_process):
        """Test"""
        mock_process.return_value = {
            'status': 200,
            'reason': 'OK',
            'json': None,
        }

        with flask.Flask(__name__).test_request_context(
            '/alert',
            data='{"alerts": []}',
            headers={'Content-type': 'application/json'},
        ):
            self.assertTupleEqual(
                self.alertify.alert(),
                ('', 204),
            )

    @patch('Alertify.health.Healthcheck.gotify_alive')
    def test_healthcheck(self, mock_gotify_alive):
        """Test"""
        mock_gotify_alive.return_value = {
            'status': 200,
            'reason': 'OK',
            'json': None,
        }

        self.assertTupleEqual(
            self.alertify.healthcheck(),
            ('OK', 200),
        )
