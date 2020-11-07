"""
Module for handling any healthcheck related activity
"""


class Healthcheck:
    """
    Class to handle the healthchecks
    """

    def __init__(self, gotify_client):
        self.gotify = gotify_client

    def gotify_alive(self):
        """
        Simple method to return the Gotify healthcheck response
        """
        return self.gotify.healthcheck()
