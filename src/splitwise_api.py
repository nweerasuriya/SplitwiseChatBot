"""
Splitwise data retrieval

This script is used to retrieve group data from the Splitwise API

"""

__date__ = "2024-10-28"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"

import os

import pandas as pd
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


def get_user_info(user_list: list) -> list:
    """
    Get user data from a list of dictionaries

    Args:
        user_list: list of dictionaries

    Returns:
        dict: dictionary with user name as key and user info as value
    """
    first_name = [user["user"]["first_name"] for user in user_list]
    last_name = [user["user"]["last_name"] for user in user_list]
    # Combine first name and last name unless last name is None
    name = [
        f"{first} {last}" if last else first
        for first, last in zip(first_name, last_name)
    ]
    info_list = ["paid_share", "owed_share"]
    all_info = {}
    for info in info_list:
        all_info[info] = [user[info] for user in user_list]
    final_info = {
        name[i]: {info: all_info[info][i] for info in info_list}
        for i in range(len(name))
    }
    return final_info


def clean_data(input_df: pd.DataFrame, keep_columns: list = None) -> tuple:
    """
    Clean Splitwise data and get list of contents

    Args:
        input_df: DataFrame with Splitwise data

    Returns:
        Cleaned DataFrame, list of content, list of metadata dict
    """
    if not keep_columns:
        keep_columns = [
            "id",
            "description",
            "details",
            "cost",
            "currency_code",
            "repayments",
            "date",
            "category",
            "users",
        ]

    df = input_df[keep_columns].copy()
    # Get name from category column
    df["category"] = df["category"].apply(lambda x: x["name"])
    df["users"] = df["users"].apply(get_user_info)
    # convert to date
    # df["date"] = pd.to_datetime(df["date"]).dt.date

    # remove columns with description "Settle all balances"
    df = df[df["description"] != "Settle all balances"]
    # add month name
    df["day"] = pd.to_datetime(df["date"]).dt.day
    df["month"] = pd.to_datetime(df["date"]).dt.month_name()
    df["year"] = pd.to_datetime(df["date"]).dt.year
    df["content"] = df.apply(
        lambda row: f"Description: {row['description']} || Total cost of item: {row['cost']} {row['currency_code']} || Users: {row['users']}",
        axis=1,
    )
    content_list = df["content"].tolist()

    metadata = [
        {
            "day": row["day"],
            "month": row["month"],
            "year": row["year"],
            "category": row["category"],
        }
        for _, row in df.iterrows()
    ]

    return df, content_list, metadata
