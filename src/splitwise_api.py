"""
Splitwise data retrieval

This script is used to retrieve group data from the Splitwise API

"""

__date__ = "2024-10-28"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"

import os

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


class SplitwiseAPI:
    """
    Class to retrieve data from the Splitwise API
    """

    # OAuth endpoints
    AUTH_URL = "https://secure.splitwise.com/oauth/authorize"
    TOKEN_URL = "https://secure.splitwise.com/oauth/token"

    def __init__(self):
        # Load API credentials from environment variables
        self.consumer_key = os.environ.get("SPLITWISE_CLIENT_ID")
        self.consumer_secret = os.environ.get("SPLITWISE_CLIENT_SECRET")

        # Create OAuth2 session
        self.client = BackendApplicationClient(client_id=self.consumer_key)
        self.session = OAuth2Session(client=self.client)

        _ = self.session.fetch_token(
            self.TOKEN_URL,
            client_id=self.consumer_key,
            client_secret=self.consumer_secret,
            include_client_id=True,
        )

    def get_expenses(self, group_id=None, limit=100):
        """
        Get expenses for a group if group_id is provided, otherwise get all expenses
        """
        if group_id:
            url = f"https://secure.splitwise.com/api/v3.0/get_expenses?group_id={group_id}&limit={limit}"
        else:
            url = f"https://secure.splitwise.com/api/v3.0/get_expenses&limit={limit}"
        response = self.session.get(url)
        return response.json()

    def get_groups(self, group_id=None, limit=20):
        """
        Get groups for a user
        """
        if group_id:
            url = f"https://secure.splitwise.com/api/v3.0/get_group/{group_id}"
        else:
            url = "https://secure.splitwise.com/api/v3.0/get_groups"
        response = self.session.get(url)
        return response.json()
