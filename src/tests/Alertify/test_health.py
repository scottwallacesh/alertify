"""Test"""
import unittest
from unittest.mock import patch

from Alertify import gotify, health  # pylint: disable=import-error


class HealthcheckTest(unittest.TestCase):
    """
    Tests for methods in the Healthcheck class.
    """

    @classmethod
    def setUpClass(cls):
        cls.healthcheck = health.Healthcheck(gotify.Gotify('', 0, '', ''))

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('Alertify.health.Healthcheck.gotify_alive')
    def test_gotify_alive(self, mock_gotify_alive):
        """Test"""
        mock_gotify_alive.return_value = {
            'status': 200,
            'reason': 'OK',
            'json': None,
        }

        self.assertDictEqual(
            self.healthcheck.gotify_alive(),
            {
                'status': 200,
                'reason': 'OK',
                'json': None,
            },
        )
