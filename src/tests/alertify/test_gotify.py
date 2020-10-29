"""
Module to handle unit tests for the alertify.gotify module
"""
import unittest
from unittest.mock import patch

from alertify import gotify  # pylint: disable=import-error


class GotifyTest(unittest.TestCase):
    """
    Tests for methods in the Gotify class.
    """

    @classmethod
    def setUpClass(cls):
        cls.gotify_client = gotify.Gotify('', 0, '', '')

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('http.client.HTTPConnection.request')
    @patch('http.client.HTTPConnection.getresponse')
    @patch('http.client.HTTPResponse.read')
    def test_delete(self, mock_request, mock_getresponse, mock_read):
        """Test"""
        mock_request.return_value.status = {}
        mock_getresponse.return_value.status = 200
        mock_getresponse.return_value.reason = 'OK'
        mock_read.return_value = {}

        self.assertDictEqual(
            self.gotify_client.delete('123'),
            {
                'status': 200,
                'reason': 'OK',
                'json': None,
            },
        )

    @patch('alertify.gotify.Gotify.messages')
    def test_find_byfingerprint(self, mock_messages):
        """Test"""
        mock_messages.return_value = [
            {
                'id': 42,
                'extras': {'alertify': {'fingerprint': 'deadbeefcafebabe'}},
            }
        ]

        self.assertListEqual(
            self.gotify_client.find_byfingerprint({'fingerprint': 'deadbeefcafebabe'}),
            [42],
        )

    def test_messages(self):
        """Test"""
        self.assertListEqual(
            self.gotify_client.messages(),
            [],
        )

    @patch('http.client.HTTPConnection.request')
    @patch('http.client.HTTPConnection.getresponse')
    @patch('http.client.HTTPResponse.read')
    def test_send_alert(self, mock_request, mock_getresponse, mock_read):
        """Test"""
        mock_request.return_value.status = {}
        mock_getresponse.return_value.status = 200
        mock_getresponse.return_value.reason = 'OK'
        mock_read.return_value = {}

        self.assertDictEqual(
            self.gotify_client.send_alert({}),
            {
                'status': 200,
                'reason': 'OK',
                'json': None,
            },
        )

    @patch('http.client.HTTPConnection.request')
    @patch('http.client.HTTPConnection.getresponse')
    @patch('http.client.HTTPResponse.read')
    def test_healthcheck(self, mock_request, mock_getresponse, mock_read):
        """Test"""
        mock_request.return_value.status = {}
        mock_getresponse.return_value.status = 200
        mock_getresponse.return_value.reason = 'OK'
        mock_read.return_value = {}

        self.assertDictEqual(
            self.gotify_client.healthcheck(),
            {
                'status': 200,
                'reason': 'OK',
                'json': None,
            },
        )
