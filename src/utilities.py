"""
Utilities Module
"""

__date__ = "2024-12-11"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"


import pandas as pd

from src.splitwise_api import SplitwiseAPI, clean_data


def get_splitwise_data(group_id=50024800):
    splitwise = SplitwiseAPI()
    group_expense = splitwise.get_expenses(group_id)
    df = pd.DataFrame(group_expense["expenses"])
    df1 = clean_data(df)
    return df1


def groupby_date(content_list):
    content_dict = {}
    # group content list by date
    for item in content_list:
        date = item.split("Date: ")[1].split("T")[0]
        if date in content_dict:
            content_dict[date] = content_dict[date] + " || \n " + item
        else:
            content_dict[date] = item
    return list(content_dict.values())
