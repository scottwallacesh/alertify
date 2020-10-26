"""
Module to handle Alertify's configuration
"""
import inspect
import logging
import os
from distutils.util import strtobool

import yaml


class Config:
    """
    Class to handle the config
    """

    delete_onresolve = bool(False)
    disable_resolved = bool(False)
    gotify_client = str()
    gotify_key = str()
    gotify_port = int(80)
    gotify_server = str('localhost')
    listen_port = int(8080)
    verbose = int(0)

    def __init__(self, configfile=None):
        """
        Method to parse a configuration file
        """
        logging.debug('Parsing config')
        parsed = {}

        try:
            with open(configfile, 'r') as file:
                parsed = yaml.safe_load(file.read())
        except FileNotFoundError as error:
            logging.warning('No config file found (%s)', error.filename)
        except TypeError:
            logging.warning('No config file provided.')

        # Iterate over the config defaults and check for environment variable
        #   overrides, then check for any items in the config, otherwise
        #   use the default values.
        for key, default_val in self.defaults().items():
            userval = os.environ.get(key.upper(), parsed.get(key, default_val))

            # Ensure the types are adhered to.
            if isinstance(default_val, bool):
                setattr(self, key, strtobool(str(userval)))
            else:
                setattr(self, key, type(default_val)(userval))

    def items(self):
        """
        Method to return an iterator for the configured items
        """
        return {key: getattr(self, key) for key in self.__dict__}.items()

    @classmethod
    def keys(cls):
        """
        Method to return the defaults as a list of keys
        """
        return [
            attr[0]
            for attr in inspect.getmembers(cls)
            if not attr[0].startswith('_')
            and not any(
                [
                    inspect.ismethod(attr[1]),
                    callable(attr[1]),
                ]
            )
        ]

    @classmethod
    def defaults(cls):
        """
        Classmethod to return the defaults as a dictionary
        """
        return {key: getattr(cls, key) for key in cls.keys()}
