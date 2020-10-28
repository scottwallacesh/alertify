"""Test"""
import unittest
from unittest.mock import patch

from alertify import healthcheck, gotify  # pylint: disable=import-error


class HealthcheckTest(unittest.TestCase):
    """
    Tests for methods in the Healthcheck class.
    """

    @classmethod
    def setUpClass(cls):
        cls.healthcheck = healthcheck.Healthcheck(gotify.Gotify('', 0, '', ''))

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('alertify.healthcheck.Healthcheck.gotify_alive')
    def test_report(self, mock_healthcheck):
        """Test"""
        mock_healthcheck.return_value = {
            'status': 200,
            'reason': 'OK',
            'json': None,
        }

        self.assertTrue(self.healthcheck.report())

    @patch('alertify.healthcheck.Healthcheck.gotify_alive')
    def test_gotify_alive(self, mock_healthcheck):
        """Test"""
        mock_healthcheck.return_value = {
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
