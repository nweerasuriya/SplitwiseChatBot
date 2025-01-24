"""
Utilities Module
"""

__date__ = "2024-12-11"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"


import pandas as pd

from splitwise_api import SplitwiseAPI


def get_splitwise_data(group_id):
    """
    Use SplitwiseAPI to get expenses for a group
    """
    splitwise = SplitwiseAPI()
    group_expense = splitwise.get_expenses(group_id)
    df = pd.DataFrame(group_expense["expenses"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def process_data(group_id):
    """
    Process data to get summary of monthly expenses
    """
    df = get_splitwise_data(group_id)
    data, content_list, metadata = clean_data(df)
    summary_contents, summary_metadata = summarise_monthly_expenses(data)
    # append summary contents and metadata to content_list and metadata
    content_list.extend(summary_contents)
    metadata.extend(summary_metadata)
    return content_list, metadata


def groupby_date(content_list):
    """
    Group content list by date and return a list of grouped content separated by "||"
    """
    content_dict = {}
    # group content list by date
    for item in content_list:
        date = item.split("Date: ")[1].split("T")[0]
        if date in content_dict:
            content_dict[date] = content_dict[date] + " || \n " + item
        else:
            content_dict[date] = item
    return list(content_dict.values())


def parse_user_expenses(input_data: pd.Series):
    """
    Parse user expenses data which is a series of nested dictionaries with the following structure:
    num index : {user: {owed_share: float, paid_share: float}
    Return a summation of each user's expenses in the form of a dictionary with the same structure
    """
    user_expenses = {}
    for item in input_data:
        for user in item:
            # convert numbers in string format to float
            item[user]["owed_share"] = round(float(item[user]["owed_share"]), 2)
            item[user]["paid_share"] = round(float(item[user]["paid_share"]), 2)
            if user in user_expenses:
                user_expenses[user]["owed_share"] += item[user]["owed_share"]
                user_expenses[user]["paid_share"] += item[user]["paid_share"]
            else:
                # round to 2 decimal places
                user_expenses[user] = {
                    "owed_share": round(float(item[user]["owed_share"]), 2),
                    "paid_share": round(float(item[user]["paid_share"]), 2),
                }
    return user_expenses


def get_user_info(user_list: list) -> list:
    """
    Get user data from a list of dictionaries
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
    df = df[df["description"] != "Settle all balances"]
    # Split date into day, month, year
    df["day"] = df["date"].dt.day
    df["month"] = df["date"].dt.month_name()
    df["year"] = df["date"].dt.year
    # Combine description, cost and users into content
    df["content"] = df.apply(
        lambda row: f"Description: {row['description']} || Total cost of item: {row['cost']} {row['currency_code']} || Users: {row['users']}",
        axis=1,
    )
    content_list = df["content"].tolist()

    metadata = [
        {
            "type": "individual",
            "day": row["day"],
            "month": row["month"],
            "year": row["year"],
            "category": row["category"].lower(),
        }
        for _, row in df.iterrows()
    ]

    return df, content_list, metadata


def summarise_monthly_expenses(data):
    """
    Summarise monthly expenses by category
    """
    summary_contents = []
    summmary_metadata = []
    for year in data["year"].unique():
        for month in data["month"].unique():
            df = data[data["month"] == month]
            # summarise by category
            for category in df["category"].unique():
                df_category = df[df["category"] == category]
                # get total cost for the month converting from string to float to 2 decimal places
                total_cost = round(
                    df_category["cost"].apply(lambda x: float(x)).sum(), 2
                )
                user_expenses = parse_user_expenses(df_category["users"])
                # create content for summary
                content = f"Summary total for month is {total_cost} {df_category['currency_code'].mode()[0]} || User expenses: {user_expenses}"
                metadata = {
                    "type": "summary",
                    "month": month,
                    "year": str(df_category["year"].mode()[0]),
                    "category": category,
                }
                summary_contents.append(content)
                summmary_metadata.append(metadata)
    return summary_contents, summmary_metadata
