"""Test"""
import unittest
from unittest.mock import patch

from alertify import server  # pylint: disable=import-error


class ServerTest(unittest.TestCase):
    """
    Tests for methods in the Server class.
    """

    @classmethod
    def setUpClass(cls):
        cls.server = server.Server(0, None, None)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('http.server.HTTPServer.serve_forever')
    def test_listen_and_run(self, mock_serve_forever):
        """Test"""
        mock_serve_forever.return_value = True

        self.assertTrue(self.server.listen_and_run())
