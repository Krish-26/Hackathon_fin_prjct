import json 
import os
from datetime import date, datetime
import calendar
import random
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st




st.set_page_config(page_title="Student Monthly Allowance Tracker",page_icon="💰",layout="wide",)

DATA_FILE = "finance_data.json"  #Main data file 


def get_current_month_key() -> str:
    """Return the current month in 'YYYY-MM' format, used as a key in JSON."""
    today = date.today()
    return f"{today.year:04d}-{today.month:02d}"

def load_data():
        if not os.path.exists(DATA_FILE):
        # Initial default states
            return {
                "current_month": get_current_month_key(),
                "monthly_allowance": 0.0,
                "categories": [
                    "Food",
                    "Transport",
                    "Rent / Hostel",
                    "Groceries",
                    "Entertainment",
                    "Academic",
                    "Health",
                    "Savings",
                    "Miscellaneous",
                ],
                "transactions": [],  # List of dicts
                "archives": {},  # "YYYY-MM": {monthly_allowance, transactions}
                "savings_goals": [],  # List of savings goal dicts: {id, name, target_amount, target_date, created_date}
                "to_take": [],  # Money friends owe you: {id, person, amount, description, date}
                "to_give": [],  # Money you owe friends: {id, person, amount, description, date}
            }

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            # If file is corrupted, fall back to default structure
            return {
                "current_month": get_current_month_key(),
                "monthly_allowance": 0.0,
                "categories": [],
                "transactions": [],
                "archives": {},
                "savings_goals": [],
                "to_take": [],
                "to_give": [],
            }

        # Ensure required keys exist even if file is old
        data.setdefault("current_month", get_current_month_key())
        data.setdefault("monthly_allowance", 0.0)
        data.setdefault("categories", [])
        data.setdefault("transactions", [])
        data.setdefault("archives", {})
        data.setdefault("savings_goals", [])
        data.setdefault("to_take", [])
        data.setdefault("to_give", [])
        return data


def save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def rollover_month_if_needed(data: dict) -> dict:

    today_month = get_current_month_key()
    stored_month = data.get("current_month", today_month)

    if stored_month != today_month:
        # Archive previous month data under its month key
        previous_month_key = stored_month
        # Only archive if there is anything meaningful
        if data.get("transactions") or data.get("monthly_allowance", 0) != 0:
            data["archives"][previous_month_key] = {
                "monthly_allowance": data.get("monthly_allowance", 0.0),
                "transactions": data.get("transactions", []),
            }

        # Start a new month, keeping the same categories and allowance
        data["current_month"] = today_month
        data["transactions"] = []

        # Persist change immediately so that refreshes see the new month
        save_data(data)

    return data


def compute_basic_metrics(df: pd.DataFrame, monthly_allowance: float) -> dict:
#totals and derived metrics for dashboard
    if df.empty:
        transaction_income = 0.0
        total_expense = 0.0
    else:
        transaction_income = df.loc[df["income_or_expenditure"] == "Income", "amount"].sum()
        total_expense = df.loc[df["income_or_expenditure"] == "Expenditure", "amount"].sum()

    # Monthly allowance is considered as income
    total_income = monthly_allowance + transaction_income
    
    # Remaining budget = total income (allowance + transactions) - expenses
    net_available = total_income - total_expense

    return {
        "total_income": float(total_income),  # Includes monthly allowance
        "total_expense": float(total_expense),
        "net_available": float(net_available),
        "remaining_budget": float(max(net_available, 0.0)),  # Do not show negative as remaining
    }


def transactions_to_dataframe(transactions: list) -> pd.DataFrame:
#Convert list to dataframe
    if not transactions:
        return pd.DataFrame(columns=["date", "category", "income_or_expenditure", "payment_mode", "amount"])

    df = pd.DataFrame(transactions)
    # Parse date to datetime for grouping and sorting
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    return df











def render_dashboard(data: dict) -> None:
    pass







def main():
    
    
    data = load_data()
    data = rollover_month_if_needed(data)

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        options=[
            "Dashboard",
            "Insights",
            "Savings",
            "CSV Analysis",
            "Previous Months Data",
            "To Take & To Give",
            "About",
        ],
        index=0,  #landing page
    )
    # Display current month info in sidebar
    current_month_key = data.get("current_month", get_current_month_key())
    year, month = current_month_key.split("-")
    month_name = calendar.month_name[int(month)]
    st.sidebar.markdown(f"**Current Month:** {month_name} {year}")

    # Route to appropriate page
    if page == "Dashboard":
        render_dashboard(data)
    elif page == "Insights":
        pass
    elif page == "Savings":
        pass
    elif page == "CSV Analysis":
        pass
    elif page == "Previous Months Data":
        pass
    elif page == "To Take & To Give":
        pass
    elif page == "About":
        pass

main()
