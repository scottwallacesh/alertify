"""Test"""
import unittest

from Alertify import config  # pylint: disable=import-error


class ConfigTest(unittest.TestCase):
    """
    Tests for methods in the Config class.
    """

    @classmethod
    def setUpClass(cls):
        cls.defaults = {
            'delete_onresolve': bool(False),
            'disable_resolved': bool(False),
            'gotify_key_app': str(),
            'gotify_key_client': str(),
            'gotify_port': int(80),
            'gotify_server': str('localhost'),
            'listen_port': int(8080),
            'verbose': int(0),
        }

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_items(self):
        """Test"""
        self.assertEqual(
            config.Config().items(),
            self.defaults.items(),
        )

    def test_keys(self):
        """Test"""
        self.assertListEqual(
            config.Config.keys(),
            list(self.defaults.keys()),
        )

    def test_defaults(self):
        """Test"""
        self.assertDictEqual(
            config.Config.defaults(),
            self.defaults,
        )
