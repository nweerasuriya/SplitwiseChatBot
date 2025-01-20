"""
Testing the data processing functions
"""

__date__ = "2025-01-08"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"


import pytest
import pandas as pd
from src.utilities import (
    clean_data,
    summarise_monthly_expenses,
    process_data,
)

@pytest.fixture
def synth_data():
    """
    Create sythetic dataset
    """
    synthetic_data = [
        {
            "description": "Dining Out",
            "category": {"name": "Dining out"},
            "cost": 25.50,
            "currency_code": "GBP",
            "date": "2024-10-05T18:30:00Z",
            "users": [
                {
                    "user": {"first_name": "Alice", "last_name": "Z"},
                    "user_id": 1,
                    "paid_share": "25.50",
                    "owed_share": "25.50",
                }
            ],
        },
        {
            "description": "Groceries",
            "category": {"name": "Groceries"},
            "cost": 45.75,
            "currency_code": "GBP",
            "date": "2024-10-10T14:20:00Z",
            "users": [
                {
                    "user": {"first_name": "Bob", "last_name": "X"},
                    "user_id": 2,
                    "paid_share": "45.75",
                    "owed_share": "0",
                },
                {
                    "user": {"first_name": "Alice", "last_name": "Z"},
                    "user_id": 1,
                    "paid_share": 0,
                    "owed_share": "45.75",
                },
            ],
        },
        {
            "description": "Dining Out 2",
            "category": {"name": "Dining out"},
            "cost": 30.00,
            "currency_code": "GBP",
            "date": "2024-10-15T19:00:00Z",
            "users": [
                {
                    "user": {"first_name": "Alice", "last_name": "Z"},
                    "user_id": 1,
                    "paid_share": "30.00",
                    "owed_share": "30.00",
                }
            ],
        },
        {
            "description": "Groceries 2",
            "category": {"name": "Groceries"},
            "cost": 10.20,
            "currency_code": "GBP",
            "date": "2024-11-01T12:45:00Z",
            "users": [
                {
                    "user": {"first_name": "Bob", "last_name": "X"},
                    "user_id": 2,
                    "paid_share": "10.20",
                    "owed_share": "5.10",
                },
                {
                    "user": {"first_name": "Alice", "last_name": "Z"},
                    "user_id": 1,
                    "paid_share": "0",
                    "owed_share": "5.10",
                },
            ],
        },
        {
            "description": "Dining Out",
            "category": {"name": "Dining out"},
            "cost": 20.00,
            "currency_code": "GBP",
            "date": "2024-11-05T18:15:00Z",
            "users": [
                {
                    "user": {"first_name": "Bob", "last_name": "X"},
                    "user_id": 2,
                    "paid_share": "20.00",
                    "owed_share": "20.00",
                }
            ],
        },
    ]
    # Convert to DataFrame
    synthetic_df = pd.DataFrame(synthetic_data)
    synthetic_df["date"] = pd.to_datetime(synthetic_df["date"])
    return synthetic_df


def test_clean_data(synth_data):
    keep_columns = [
        "description",
        "cost",
        "currency_code",
        "date",
        "category",
        "users",
    ]

    data, content_list, metadata = clean_data(synth_data, keep_columns)

    # Check if the data is a DataFrame
    assert isinstance(data, pd.DataFrame)
    # Check if the content_list is a list of size 5
    assert len(content_list) == 5
    # Check if the metadata only has months October and November and category Dining out and Groceries
    assert len(metadata) == 5
    # irrespective of the order
    assert list(set([item["month"] for item in metadata])).sort() == ["October", "November"].sort()	
    assert list(set([item["category"] for item in metadata])).sort() == [
        "dining out",
        "groceries",
    ].sort()


def test_summarise_monthly_expenses(synth_data):
    keep_columns = [
        "description",
        "cost",
        "currency_code",
        "date",
        "category",
        "users",
    ]
    data, _, _ = clean_data(synth_data, keep_columns)
    summary_contents, summary_metadata = summarise_monthly_expenses(data)
    # Check if the summary_contents is a list of size 4
    assert len(summary_contents) == 4
    assert summary_contents[0].split("||")[0] == "Summary total for month is 55.5 GBP "
    assert summary_contents[-1].split("||")[0] == "Summary total for month is 20.0 GBP "
    assert (
        summary_contents[2].split("User expenses:")[1]
        == " {'Bob X': {'owed_share': 5.1, 'paid_share': 10.2}, 'Alice Z': {'owed_share': 5.1, 'paid_share': 0.0}}"
    )
    # Check if the summary_metadata is a list of size 4
    assert len(summary_metadata) == 4
    # assert type is summary for all items
    assert all([item["type"] == "summary" for item in summary_metadata])
    assert summary_metadata[0]["month"] == "October"
    assert summary_metadata[-1]["month"] == "November"
