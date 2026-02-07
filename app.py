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


def get_days_in_current_month() -> int:
    today = date.today()
    return calendar.monthrange(today.year, today.month)[1]


def compute_insight_metrics(metrics: dict) -> dict:
    """
   metrics for Insights page:
    - average daily spending so far
    - remaining days
    - safe daily spending limit
    """
    today = date.today()
    days_in_month = get_days_in_current_month()
    days_passed = today.day  # Up to and including today
    remaining_days = max(days_in_month - days_passed, 0)

    total_expense = metrics["total_expense"]
    remaining_budget = metrics["remaining_budget"]

    avg_daily_spent = total_expense / days_passed if days_passed > 0 else 0.0
    safe_daily_spend = remaining_budget / remaining_days if remaining_days > 0 else 0.0

    return {
        "avg_daily_spent": float(avg_daily_spent),
        "remaining_days": int(remaining_days),
        "safe_daily_spend": float(safe_daily_spend),
    }





#Financial tips system
FINANCIAL_TIPS = [
    "Note your expenses once a day to stay calmly aware.",
    "Keep small, predictable snacks at home to avoid impulse buys outside.",
    "Plan your week’s meals so food spending feels intentional.",
    "Refill a water bottle instead of buying bottles on campus.",
    "Use a simple spending limit for outings and stick to it comfortably.",
    "Share subscriptions with trusted friends where allowed to reduce cost.",
    "Schedule a weekly ‘money check-in’ that takes just 5–10 minutes.",
    "Walk or cycle for short distances when it feels safe and practical.",
    "Use a shopping list so you only buy what you had in mind.",
    "Keep one low-cost comfort activity ready for stressful days.",
    "Borrow books from the library before buying new ones.",
    "Cook in bulk with friends and share ingredients to save gently.",
    "Track how often you order food; small changes can add up calmly.",
    "Keep a small emergency cushion, even if it grows slowly.",
    "If you overspend one day, you can gently rebalance over the week.",
    "Look for student discounts before paying full price.",
    "Bring homemade tea or coffee when possible to reduce café trips.",
    "Compare prices online before buying electronics or textbooks.",
    "Set a simple monthly savings goal, even if the amount is small.",
    "Write down your top three spending priorities for this month.",
    "Plan social outings that don’t always revolve around spending.",
    "Buy second-hand when it feels comfortable for you.",
    "Use cash for some categories if it helps you feel more in control.",
    "Pause for a few seconds before each unplanned purchase.",
    "Unsubscribe from marketing emails that tempt you to buy more.",
    "Set gentle limits for late-night online shopping.",
    "Review your recurring subscriptions once a month.",
    "Use a shared ride instead of solo cabs when it feels safe.",
    "Try a ‘no-spend’ day occasionally to reset your habits.",
    "Keep snacks in your bag to avoid expensive last-minute buys.",
    "Plan ahead for exam periods when delivery spending might rise.",
    "Split big purchases into planned, smaller monthly amounts.",
    "Try making coffee at home most days and buying it occasionally.",
    "Notice which days you tend to spend more, and plan ahead.",
    "Set a calm limit for how often you use food delivery apps.",
    "Use your allowance tracking as information, not as judgment.",
    "Compare prices between nearby stores for everyday items.",
    "Keep one payment method as your primary one to simplify tracking.",
    "Add notes to your transactions so they make sense later.",
    "Create a small ‘fun fund’ so enjoyment is part of your budget.",
    "When you get extra income, decide its purpose before spending.",
    "Try generic brands for a few items and see how you feel.",
    "Keep a list of things you want and revisit it after a few days.",
    "Celebrate small wins like sticking to your plan for a week.",
    "If a plan doesn’t work, adjust it rather than abandoning it.",
    "Use reminders to pay any dues on time and avoid late fees.",
    "Talk openly with friends about low-cost hangout ideas.",
    "Bundle small online orders to reduce delivery fees.",
    "Prepare simple meals in advance for busy days.",
    "Notice which purchases actually make you feel better long term.",
    "Use campus resources (labs, gyms, libraries) wherever possible.",
    "Take advantage of student offers on transport passes if available.",
    "Write down upcoming events so you can plan their costs calmly.",
    "Keep your most common categories visible to stay mindful.",
    "Review last month’s spending for 5 minutes to spot easy tweaks.",
    "Use your allowance tracker as a supportive tool, not a critic.",
    "Choose one category to gently reduce this month, not all at once.",
    "Make a simple meal plan before grocery shopping.",
    "Avoid shopping when you’re very tired or stressed if possible.",
    "Track cash withdrawals so you know where they are going.",
    "Use campus printers or shared printers to save on printing costs.",
    "Sell or donate items you don’t use and free up space and money.",
    "When you get a gift or bonus, consider saving a small part of it.",
    "Choose one day a week to quickly log all pending transactions.",
    "Staying curious about your habits is more helpful than being harsh.",
    "Ask seniors how they managed their allowance for practical ideas.",
    "Keep big financial goals visible but flexible.",
    "Reflect on one purchase each week that felt really worth it.",
    "Reflect on one purchase each week that you might skip next time.",
    "Use a simple color scheme and calm visuals for your money tools.",
    "Give yourself permission to enjoy your allowance mindfully.",
    "Remember that small, steady changes often beat strict rules.",
    "Revisit your budget if your routine or semester changes.",
    "Use this tracker to reduce surprise, not to create pressure.",
    "Notice which subscriptions you actually use regularly.",
    "Group similar expenses together to see clear patterns.",
    "Set a friendly reminder near your study space to check your budget.",
    "Track how often you take cabs versus public transport.",
    "Plan ahead for festivals and celebrations in your budget.",
    "Aim for progress in your financial habits, not perfection.",
    "If you miss tracking for a few days, you can always restart calmly.",
    "Use digital wallets mindfully; small taps can add up quietly.",
    "Recheck your allowance amount each semester to see if it still fits.",
    "Keep your financial notes simple enough that you enjoy using them.",
]


def get_random_tips(n: int = 3) -> list:
    n = min(n, len(FINANCIAL_TIPS))
    return random.sample(FINANCIAL_TIPS, n)










def render_dashboard(data: dict) -> None:
    #main dashboard
    st.subheader("Dashboard - Current Month Overview")

    # Allowance settings
    with st.expander("Monthly Allowance Settings", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(
                "Set your planned monthly allowance. "
                "This is the amount you aim to manage calmly over the month."
            )
        with col2:
            new_allowance = st.number_input(
                "Monthly Allowance",
                min_value=0.0,
                value=float(data.get("monthly_allowance", 0.0)),
                step=100.0,
            )
        if st.button("Save Allowance"):
            data["monthly_allowance"] = float(new_allowance)
            save_data(data)
            st.success("Monthly allowance saved. You can adjust this anytime.")

    # Convert current transactions to DataFrame
    df = transactions_to_dataframe(data.get("transactions", []))
    basic_metrics = compute_basic_metrics(df, data.get("monthly_allowance", 0.0))

    #Key metrics
    st.markdown("### Key Monthly Numbers")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Monthly Allowance", f"{data.get('monthly_allowance', 0.0):,.2f}")
    with m2:
        st.metric("Total Spent (Expenses)", f"{basic_metrics['total_expense']:,.2f}")
    with m3:
        st.metric("Remaining Budget (Approx.)", f"{basic_metrics['remaining_budget']:,.2f}")

    #Transaction input form
    st.markdown("### Add a Transaction")
    with st.form("add_transaction_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            tx_date = st.date_input("Date", value=date.today())
            income_or_exp = st.selectbox(
                "Type",
                options=["Expenditure", "Income"],
                help="Choose whether this is money going out (Expenditure) or coming in (Income).",
            )
            payment_mode = st.selectbox(
                "Payment Mode",
                options=["Cash", "Card", "UPI / Wallet", "Bank Transfer", "Other"],
            )
        with c2:
            # Category selection from persisted categories
            if not data.get("categories"):
                st.info("No categories yet. Please add a category below first.")
                category = None
            else:
                category = st.selectbox("Category", options=data["categories"])

            amount = st.number_input(
                "Amount",
                min_value=0.0,
                step=10.0,
                format="%.2f",
            )

        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            if category is None:
                st.warning("Please add at least one category before logging a transaction.")
            elif amount <= 0:
                st.warning("Please enter an amount greater than zero.")
            else:
                new_tx = {
                    "date": tx_date.isoformat(),
                    "category": category,
                    "income_or_expenditure": income_or_exp,
                    "payment_mode": payment_mode,
                    "amount": float(amount),
                }
                data.setdefault("transactions", []).append(new_tx)
                save_data(data)
                st.success("Transaction added. You're keeping a clear, calm record.")

    #Category management
    st.markdown("### Manage Categories")
    c1, c2 = st.columns(2)
    with c1:
        st.write("Add a category that matches your real student life.")
        new_cat = st.text_input("New Category Name")
        if st.button("Add Category"):
            cleaned = new_cat.strip()
            if not cleaned:
                st.warning("Please enter a non-empty category name.")
            elif cleaned in data["categories"]:
                st.info("This category already exists.")
            else:
                data["categories"].append(cleaned)
                save_data(data)
                st.success("Category added and saved for future use.")

    with c2:
        st.write("Remove categories you no longer use (optional).")
        if data.get("categories"):
            cats_to_delete = st.multiselect(
                "Select Categories to Remove",
                options=data["categories"],
            )
            if st.button("Delete Selected Categories"):
                data["categories"] = [c for c in data["categories"] if c not in cats_to_delete]
                save_data(data)
                st.success("Selected categories removed. Past transactions remain unchanged.")
        else:
            st.info("No categories defined yet.")

    #Transactions table with filters and sorting
    st.markdown("### Transactions This Month")
    if df.empty:
        st.info("No transactions for this month yet. Adding even a few entries gives you helpful insight.")
        return

    # Filters
    f1, f2 = st.columns(2)
    with f1:
        type_filter = st.selectbox(
            "Show",
            options=["All", "Income only", "Expenditure only"],
        )
    with f2:
        sort_option = st.selectbox(
            "Sort by Amount",
            options=["None", "Amount Ascending", "Amount Descending"],
        )

    # Apply type filter
    if type_filter == "Income only":
        df_filtered = df[df["income_or_expenditure"] == "Income"].copy()
    elif type_filter == "Expenditure only":
        df_filtered = df[df["income_or_expenditure"] == "Expenditure"].copy()
    else:
        df_filtered = df.copy()

    # Apply sorting
    if sort_option == "Amount Ascending":
        df_filtered = df_filtered.sort_values("amount", ascending=True)
    elif sort_option == "Amount Descending":
        df_filtered = df_filtered.sort_values("amount", ascending=False)
    else:
        df_filtered = df_filtered.sort_values("date", ascending=True)

    # Format date for display
    df_filtered["date"] = df_filtered["date"].dt.date

    st.dataframe(df_filtered, use_container_width=True)

    # Delete transactions section
    st.markdown("### Delete Transactions")
    st.write("Select transactions to remove from your records.")
    
    # Create a list of transaction labels for selection
    # We'll use the original df (before filtering) to show all transactions
    df_original = transactions_to_dataframe(data.get("transactions", []))
    if not df_original.empty:
        # Create readable labels for each transaction
        transaction_labels = []
        transaction_indices = []
        
        for idx, row in df_original.iterrows():
            date_str = pd.to_datetime(row["date"]).strftime("%Y-%m-%d")
            label = f"{date_str} | {row['category']} | {row['income_or_expenditure']} | {row['amount']:.2f}"
            transaction_labels.append(label)
            transaction_indices.append(idx)
        
        # Multiselect for choosing transactions to delete
        transactions_to_delete = st.multiselect(
            "Select transactions to delete",
            options=transaction_labels,
            help="Choose one or more transactions to remove. This action cannot be undone.",
        )
        
        if transactions_to_delete:
            if st.button("🗑️ Delete Selected Transactions", type="primary"):
                # Find indices of selected transactions
                selected_indices = [transaction_indices[i] for i, label in enumerate(transaction_labels) if label in transactions_to_delete]
                
                # Remove transactions from the original list
                # We need to match by the transaction dict, not by DataFrame index
                transactions_list = data.get("transactions", [])
                
                # Convert selected DataFrame rows back to dicts for matching
                selected_transactions = []
                for idx in selected_indices:
                    row = df_original.iloc[idx]
                    # Reconstruct transaction dict matching the stored format
                    tx_dict = {
                        "date": pd.to_datetime(row["date"]).strftime("%Y-%m-%d"),
                        "category": row["category"],
                        "income_or_expenditure": row["income_or_expenditure"],
                        "payment_mode": row["payment_mode"],
                        "amount": float(row["amount"]),
                    }
                    selected_transactions.append(tx_dict)
                
                # Remove matching transactions from the list
                # Use a matching function that compares all fields
                def transactions_match(tx1, tx2):
                    """Check if two transaction dicts match."""
                    return (
                        tx1.get("date") == tx2.get("date")
                        and tx1.get("category") == tx2.get("category")
                        and tx1.get("income_or_expenditure") == tx2.get("income_or_expenditure")
                        and tx1.get("payment_mode") == tx2.get("payment_mode")
                        and abs(tx1.get("amount", 0) - tx2.get("amount", 0)) < 0.01  # Float comparison
                    )
                
                # Filter out matching transactions
                original_count = len(transactions_list)
                transactions_list = [
                    tx for tx in transactions_list
                    if not any(transactions_match(tx, selected_tx) for selected_tx in selected_transactions)
                ]
                deleted_count = original_count - len(transactions_list)
                
                # Update data and save
                data["transactions"] = transactions_list
                save_data(data)
                st.success(f"Successfully deleted {deleted_count} transaction(s). Your records have been updated.")
                st.rerun()  # Refresh to show updated table














def render_insights(data: dict) -> None:
    """Render the Insights tab with analytics, charts, and financial tips."""
    st.subheader("Insights – Gentle View of Your Habits")

    df = transactions_to_dataframe(data.get("transactions", []))
    basic_metrics = compute_basic_metrics(df, data.get("monthly_allowance", 0.0))
    insight_metrics = compute_insight_metrics(basic_metrics)

    # --- Spending intelligence section ---
    st.markdown("### Spending Intelligence")
    i1, i2, i3 = st.columns(3)
    with i1:
        st.metric(
            "Average Daily Spending So Far",
            f"{insight_metrics['avg_daily_spent']:,.2f}",
        )
    with i2:
        st.metric(
            "Remaining Days in Month",
            f"{insight_metrics['remaining_days']}",
        )
    with i3:
        st.metric(
            "Safe Daily Spending Limit (Approx.)",
            f"{insight_metrics['safe_daily_spend']:,.2f}",
        )

    st.write(
        "These numbers are estimates to gently guide you. "
        "You can adjust plans at any time to keep things comfortable."
    )

    # --- Visuals section ---
    st.markdown("### Visual Overview")
    if df.empty:
        st.info("Once you log some transactions, charts will appear here to support your decisions.")
    else:
        col1, col2 = st.columns(2)

        # Category-wise pie chart (expenses only)
        with col1:
            st.write("Category-wise Spending (Expenses)")
            df_exp = df[df["income_or_expenditure"] == "Expenditure"]
            if df_exp.empty:
                st.info("No expenditure entries yet for this month.")
            else:
                category_sums = df_exp.groupby("category")["amount"].sum().sort_values(ascending=False)
                fig, ax = plt.subplots()
                # Use calm, non-red colors
                colors = plt.cm.Pastel2.colors
                ax.pie(
                    category_sums.values,
                    labels=category_sums.index,
                    autopct="%1.1f%%",
                    startangle=90,
                    colors=colors,
                )
                ax.axis("equal")
                st.pyplot(fig)

        # Daily spending trend (expenses only)
        with col2:
            st.write("Daily Spending Trend (Expenses)")
            df_exp = df[df["income_or_expenditure"] == "Expenditure"]
            if df_exp.empty:
                st.info("No expenditure entries yet for this month.")
            else:
                daily = df_exp.groupby("date")["amount"].sum().reset_index()
                daily = daily.sort_values("date")
                fig, ax = plt.subplots()
                ax.plot(daily["date"], daily["amount"], marker="o", color="#4c72b0")
                ax.set_xlabel("Date")
                ax.set_ylabel("Amount")
                ax.set_title("Daily Expenditure")
                plt.xticks(rotation=45)
                st.pyplot(fig)

        # Income vs Expenditure comparison
        st.write("Income vs Expenditure This Month")
        total_income = basic_metrics["total_income"]
        total_expense = basic_metrics["total_expense"]
        fig, ax = plt.subplots()
        labels = ["Income", "Expenditure"]
        values = [total_income, total_expense]
        colors = ["#55a868", "#4c72b0"]  # Calm green and blue
        ax.bar(labels, values, color=colors)
        ax.set_ylabel("Amount")
        st.pyplot(fig)

    # --- Financial tips section ---
    st.markdown("### Gentle Financial Tips for Students")
    st.write(
        "Here are a few calm, practical thoughts for this session. "
        "They change with each refresh so you always see something new."
    )
    for tip in get_random_tips(3):
        st.markdown(f"- {tip}")

    st.info(
        "You’re currently using your allowance tracker in a healthy way. "
        "Simply noticing your patterns regularly keeps you in a safe spending range."
    )











def render_savings(data: dict) -> None:
   #Render the Savings tab with goal tracking and progress visualization
    st.subheader("Monthly Savings Goals – Your Path to Financial Growth")
    
    st.write(
        "Set savings goals and track your progress calmly. "
        "Every small step toward your goals is meaningful."
    )
    
    # Calculate current savings from transactions
    # Monthly allowance is treated as income
    df = transactions_to_dataframe(data.get("transactions", []))
    monthly_allowance = data.get("monthly_allowance", 0.0)
    
    if df.empty:
        transaction_income = 0.0
        total_expense = 0.0
    else:
        transaction_income = df.loc[df["income_or_expenditure"] == "Income", "amount"].sum()
        total_expense = df.loc[df["income_or_expenditure"] == "Expenditure", "amount"].sum()
    
    # Total income includes monthly allowance + transaction income
    total_income = monthly_allowance + transaction_income
    # Savings = total income (allowance + transactions) - expenses
    current_savings = float(total_income - total_expense)
    
    # Show current savings status
    st.markdown("### Current Savings Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Month Savings", f"{current_savings:,.2f}")
    with col2:
        monthly_allowance = data.get("monthly_allowance", 0.0)
        if monthly_allowance > 0:
            savings_rate = (current_savings / monthly_allowance * 100) if monthly_allowance > 0 else 0.0
            st.metric("Savings Rate (of Allowance)", f"{savings_rate:.1f}%")
        else:
            st.info("Set your monthly allowance in Dashboard to see savings rate.")
    
    # --- Manage Savings Goals ---
    st.markdown("### Manage Your Savings Goals")
    
    savings_goals = data.get("savings_goals", [])
    
    # Create new goal form
    with st.expander("➕ Create New Savings Goal", expanded=False):
        with st.form("new_goal_form", clear_on_submit=True):
            goal_name = st.text_input("Goal Name", placeholder="e.g., Emergency Fund, New Laptop, Trip")
            target_amount = st.number_input("Target Amount", min_value=0.0, step=100.0, format="%.2f")
            # Get today's date
            today = date.today()

            # Calculate the last day of the current month
            last_day = calendar.monthrange(today.year, today.month)[1]
            max_date = date(today.year, today.month, last_day)

            # The updated input line
            target_date = st.date_input(
                "Target Date", 
                value=today, 
                min_value=today, 
                max_value=max_date,
                help="Goals must be completed within the current month."
            )
            
            submitted = st.form_submit_button("Create Goal")
            if submitted:
                if not goal_name.strip():
                    st.warning("Please enter a goal name.")
                elif target_amount <= 0:
                    st.warning("Please enter a target amount greater than zero.")
                elif target_date is None:
                    st.warning("Please select a target date.")
                else:
                    # Generate unique ID for the goal
                    new_id = str(len(savings_goals) + 1) + "-" + str(int(datetime.now().timestamp()))
                    new_goal = {
                        "id": new_id,
                        "name": goal_name.strip(),
                        "target_amount": float(target_amount),
                        "target_date": target_date.isoformat(),
                        "created_date": date.today().isoformat(),
                    }
                    savings_goals.append(new_goal)
                    data["savings_goals"] = savings_goals
                    save_data(data)
                    st.success(f"Goal '{goal_name}' created. You're taking a positive step forward!")
                    st.rerun()
    
    # Display existing goals
    st.markdown("### Your Savings Goals")
    
    if not savings_goals:
        st.info(
            "No savings goals set yet. Create your first goal above to start tracking your progress. "
            "Even small goals help build healthy financial habits."
        )
    else:
        # Calculate progress for each goal, but only for the current month. In a real app, you might want to track cumulative savings across months.
        today = date.today()
        
        for idx, goal in enumerate(savings_goals):
            goal_id = goal.get("id", str(idx))
            goal_name = goal.get("name", "Unnamed Goal")
            target_amount = goal.get("target_amount", 0.0)
            target_date_str = goal.get("target_date", "")
            created_date_str = goal.get("created_date", date.today().isoformat())
            
            try:
                target_date_obj = datetime.fromisoformat(target_date_str).date()
            except (ValueError, TypeError):
                target_date_obj = None
            
            # Calculate progress (simplified: use current month savings as progress)
            # In a real app, you might want cumulative savings across months
            progress_amount = max(current_savings, 0.0)  # Don't show negative progress
            progress_percentage = min((progress_amount / target_amount * 100) if target_amount > 0 else 0.0, 100.0)
            remaining = max(target_amount - progress_amount, 0.0)
            
            # Calculate days remaining if target date exists
            days_remaining = None
            if target_date_obj:
                days_remaining = (target_date_obj - today).days
            
            # Create a card-like display for each goal
            with st.container():
                st.markdown(f"#### {goal_name}")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    # Progress bar
                    st.progress(progress_percentage / 100.0)
                    st.caption(f"Progress: {progress_percentage:.1f}% ({progress_amount:,.2f} / {target_amount:,.2f})")
                
                with col2:
                    st.metric("Target", f"{target_amount:,.2f}")
                    if days_remaining is not None:
                        if days_remaining >= 0:
                            st.caption(f"{days_remaining} days remaining")
                        else:
                            st.caption("Target date passed")
                
                with col3:
                    st.metric("Remaining", f"{remaining:,.2f}")
                    if days_remaining is not None and days_remaining > 0:
                        # Calculate suggested daily savings
                        suggested_daily = remaining / days_remaining if days_remaining > 0 else 0.0
                        st.caption(f"~{suggested_daily:,.2f}/day to reach goal")
                
                # Goal actions
                col_del, col_edit = st.columns([1, 1])
                with col_del:
                    if st.button(f"Delete Goal", key=f"delete_{goal_id}"):
                        data["savings_goals"] = [g for g in savings_goals if g.get("id") != goal_id]
                        save_data(data)
                        st.success(f"Goal '{goal_name}' deleted.")
                        st.rerun()
                
                st.divider()
        
        # Overall progress visualization
        st.markdown("### Overall Progress Visualization")
        if len(savings_goals) > 0:
            goal_names = [g.get("name", "Unnamed") for g in savings_goals]
            target_amounts = [g.get("target_amount", 0.0) for g in savings_goals]
            progress_amounts = [min(current_savings, target) for target in target_amounts]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            x_pos = range(len(goal_names))
            width = 0.35
            
            bars1 = ax.bar([x - width/2 for x in x_pos], target_amounts, width, label="Target", color="#4c72b0", alpha=0.7)
            bars2 = ax.bar([x + width/2 for x in x_pos], progress_amounts, width, label="Progress", color="#55a868", alpha=0.7)
            
            ax.set_xlabel("Goals")
            ax.set_ylabel("Amount")
            ax.set_title("Savings Goals Progress")
            ax.set_xticks(x_pos)
            ax.set_xticklabels(goal_names, rotation=45, ha="right")
            ax.legend()
            
            plt.tight_layout()
            st.pyplot(fig)
    
    st.info(
        "💡 **Tip**: Track your savings regularly and adjust goals as needed. "
        "Remember, building savings is a journey, not a race. Every step counts."
        
    )









def render_csv_analysis() -> None:
  
    #This does NOT persist data; it only analyzes the uploaded file.

    st.subheader("CSV Analysis – Learn from Past Data")
    st.write(
        "Upload a CSV file with your past transactions to explore patterns.\n\n"
        "**Expected columns (case-sensitive):** `date`, `category`, `income_or_expenditure`, `payment_mode`, `amount`.\n"
        "Dates should be in a format that pandas can understand (e.g., YYYY-MM-DD)."
    )

    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
    if uploaded_file is None:
        st.info("No file uploaded yet. Choose a file to see insights.")
        return

    try:
        df = pd.read_csv(uploaded_file)
    except Exception:
        st.warning("Unable to read this file as CSV. Please check the format.")
        return

    # Ensure required columns
    required_cols = {"date", "category", "income_or_expenditure", "payment_mode", "amount"}
    if not required_cols.issubset(df.columns):
        st.warning(
            "The CSV is missing one or more required columns. "
            "Please ensure it includes: date, category, income_or_expenditure, payment_mode, amount."
        )
        st.write("Detected columns:", list(df.columns))
        return

    # Normalize dtypes
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

    st.markdown("### Raw Data Preview")
    st.dataframe(df.head(50), use_container_width=True)

    # Basic analytics
    total_spending = df.loc[df["income_or_expenditure"] == "Expenditure", "amount"].sum()
    total_income = df.loc[df["income_or_expenditure"] == "Income", "amount"].sum()

    if df["date"].notna().any():
        min_date = df["date"].min().date()
        max_date = df["date"].max().date()
        days_range = max((max_date - min_date).days + 1, 1)
        avg_daily_spent = total_spending / days_range
    else:
        min_date = max_date = None
        days_range = 0
        avg_daily_spent = 0.0

    st.markdown("### Summary from CSV")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Spending (Expenses)", f"{total_spending:,.2f}")
    with c2:
        st.metric("Total Income", f"{total_income:,.2f}")
    with c3:
        st.metric("Average Daily Spending (Over File Range)", f"{avg_daily_spent:,.2f}")

    if min_date and max_date:
        st.write(f"Date range in file: **{min_date}** to **{max_date}**.")

    # Visuals similar to Insights
    st.markdown("### Visuals from CSV")
    col1, col2 = st.columns(2)

    # Category-wise pie (expenses)
    with col1:
        st.write("Category-wise Spending (Expenses)")
        df_exp = df[df["income_or_expenditure"] == "Expenditure"]
        if df_exp.empty:
            st.info("No expenditure entries detected in this file.")
        else:
            category_sums = df_exp.groupby("category")["amount"].sum().sort_values(ascending=False)
            fig, ax = plt.subplots()
            colors = plt.cm.Pastel1.colors
            ax.pie(
                category_sums.values,
                labels=category_sums.index,
                autopct="%1.1f%%",
                startangle=90,
                colors=colors,
            )
            ax.axis("equal")
            st.pyplot(fig)

    # Daily spending trend
    with col2:
        st.write("Daily Spending Trend (Expenses)")
        df_exp = df[df["income_or_expenditure"] == "Expenditure"]
        if df_exp.empty:
            st.info("No expenditure entries detected in this file.")
        else:
            daily = df_exp.groupby("date")["amount"].sum().reset_index()
            daily = daily.sort_values("date")
            fig, ax = plt.subplots()
            ax.plot(daily["date"], daily["amount"], marker="o", color="#4c72b0")
            ax.set_xlabel("Date")
            ax.set_ylabel("Amount")
            ax.set_title("Daily Expenditure (CSV)")
            plt.xticks(rotation=45)
            st.pyplot(fig)

    # Income vs Expenditure comparison
    st.write("Income vs Expenditure (CSV)")
    fig, ax = plt.subplots()
    labels = ["Income", "Expenditure"]
    values = [total_income, total_spending]
    colors = ["#55a868", "#4c72b0"]
    ax.bar(labels, values, color=colors)
    ax.set_ylabel("Amount")
    st.pyplot(fig)










def render_previous_months(data: dict) -> None:
    #Render the Previous Months Data tab with archives and summaries
    st.subheader("Previous Months Data – Calm Retrospective")

    archives = data.get("archives", {})
    if not archives:
        st.info("No previous month data archived yet. As months pass, summaries will appear here.")
        return

    # Sort month keys descending so latest appears first
    months = sorted(archives.keys(), reverse=True)
    # Show readable labels like "2025-12 (December 2025)"
    def pretty_label(month_key: str) -> str:
        year, month = month_key.split("-")
        month_name = calendar.month_name[int(month)]
        return f"{month_key} ({month_name} {year})"

    label_map = {pretty_label(m): m for m in months}
    selected_label = st.selectbox("Choose a month to explore", options=list(label_map.keys()))
    selected_key = label_map[selected_label]

    month_data = archives[selected_key]
    df = transactions_to_dataframe(month_data.get("transactions", []))
    basic_metrics = compute_basic_metrics(df, month_data.get("monthly_allowance", 0.0))

    # Summary metrics
    st.markdown(f"### Summary for {selected_label}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Monthly Allowance (for that month)", f"{month_data.get('monthly_allowance', 0.0):,.2f}")
    with c2:
        st.metric("Total Spent (Expenses)", f"{basic_metrics['total_expense']:,.2f}")
    with c3:
        st.metric("Net Remaining at Month End (Approx.)", f"{basic_metrics['remaining_budget']:,.2f}")

    # Transactions table
    st.markdown("### Transactions for Selected Month")
    if df.empty:
        st.info("No transactions were recorded for this month.")
    else:
        df_display = df.copy()
        df_display["date"] = df_display["date"].dt.date
        st.dataframe(df_display, use_container_width=True)








def render_to_take_to_give(data: dict) -> None:

    #This is purely for mental records and does NOT affect any financial calculations.

    st.subheader("To Take & To Give – Mental Records")
    
    st.write(
        "Keep track of money friends owe you and money you owe friends. "
        "This is just for your personal records and doesn't affect your budget calculations."
    )
    
    to_take = data.get("to_take", [])  # Money owed to you
    to_give = data.get("to_give", [])  # Money you owe
    
    # Calculate totals for quick overview
    total_to_take = sum(entry.get("amount", 0.0) for entry in to_take)
    total_to_give = sum(entry.get("amount", 0.0) for entry in to_give)
    
    # Summary metrics
    st.markdown("### Quick Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Money to Take", f"{total_to_take:,.2f}")
    with col2:
        st.metric("Total Money to Give", f"{total_to_give:,.2f}")
    
    # Money to Take Section (Friends owe you)
    st.markdown("---")
    st.markdown("### 💰 Money to Take (Friends Owe You)")
    
    # Add new entry form
    with st.expander("➕ Add New Entry - Money to Take", expanded=False):
        with st.form("add_to_take_form", clear_on_submit=True):
            person_name = st.text_input("Person Name", placeholder="Friend's name")
            amount = st.number_input("Amount", min_value=0.0, step=10.0, format="%.2f")
            description = st.text_area("Description/Notes", placeholder="What was this for? (optional)")
            entry_date = st.date_input("Date", value=date.today())
            
            submitted = st.form_submit_button("Add Entry")
            if submitted:
                if not person_name.strip():
                    st.warning("Please enter a person's name.")
                elif amount <= 0:
                    st.warning("Please enter an amount greater than zero.")
                else:
                    new_id = str(len(to_take) + len(to_give) + 1) + "-" + str(int(datetime.now().timestamp()))
                    new_entry = {
                        "id": new_id,
                        "person": person_name.strip(),
                        "amount": float(amount),
                        "description": description.strip() if description else "",
                        "date": entry_date.isoformat(),
                    }
                    to_take.append(new_entry)
                    data["to_take"] = to_take
                    save_data(data)
                    st.success(f"Entry added for {person_name}. Your records are updated.")
                    st.rerun()
    
    # Display and manage entries
    if not to_take:
        st.info("No entries yet. Add entries above to track money friends owe you.")
    else:
        for idx, entry in enumerate(to_take):
            entry_id = entry.get("id", str(idx))
            person = entry.get("person", "Unknown")
            amount = entry.get("amount", 0.0)
            description = entry.get("description", "")
            entry_date_str = entry.get("date", date.today().isoformat())
            
            try:
                entry_date_obj = datetime.fromisoformat(entry_date_str).date()
            except (ValueError, TypeError):
                entry_date_obj = date.today()
            
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{person}**")
                    if description:
                        st.caption(description)
                    st.caption(f"Date: {entry_date_obj.strftime('%Y-%m-%d')}")
                with col2:
                    st.metric("Amount", f"{amount:,.2f}")
                with col3:
                    # Edit button
                    edit_key = f"edit_take_{entry_id}"
                    if st.button("✏️ Edit", key=edit_key):
                        st.session_state[f"editing_take_{entry_id}"] = True
                
                with col4:
                    # Delete button
                    if st.button("🗑️ Delete", key=f"delete_take_{entry_id}"):
                        data["to_take"] = [e for e in to_take if e.get("id") != entry_id]
                        save_data(data)
                        st.success(f"Entry for {person} deleted.")
                        st.rerun()
                
                # Edit form (shown when edit button is clicked)
                if st.session_state.get(f"editing_take_{entry_id}", False):
                    with st.form(f"edit_take_form_{entry_id}", clear_on_submit=False):
                        new_person = st.text_input("Person Name", value=person, key=f"person_take_{entry_id}")
                        new_amount = st.number_input("Amount", min_value=0.0, value=float(amount), step=10.0, format="%.2f", key=f"amount_take_{entry_id}")
                        new_description = st.text_area("Description/Notes", value=description, key=f"desc_take_{entry_id}")
                        new_date = st.date_input("Date", value=entry_date_obj, key=f"date_take_{entry_id}")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Save Changes"):
                                entry["person"] = new_person.strip()
                                entry["amount"] = float(new_amount)
                                entry["description"] = new_description.strip()
                                entry["date"] = new_date.isoformat()
                                data["to_take"] = to_take
                                save_data(data)
                                st.session_state[f"editing_take_{entry_id}"] = False
                                st.success("Entry updated successfully.")
                                st.rerun()
                        with col_cancel:
                            if st.form_submit_button("❌ Cancel"):
                                st.session_state[f"editing_take_{entry_id}"] = False
                                st.rerun()
                
                st.divider()
    
    #Money to Give Section (You owe friends)
    st.markdown("---")
    st.markdown("### 📤 Money to Give (You Owe Friends)")
    
    # Add new entry form
    with st.expander("➕ Add New Entry - Money to Give", expanded=False):
        with st.form("add_to_give_form", clear_on_submit=True):
            person_name = st.text_input("Person Name", placeholder="Friend's name", key="give_person")
            amount = st.number_input("Amount", min_value=0.0, step=10.0, format="%.2f", key="give_amount")
            description = st.text_area("Description/Notes", placeholder="What was this for? (optional)", key="give_desc")
            entry_date = st.date_input("Date", value=date.today(), key="give_date")
            
            submitted = st.form_submit_button("Add Entry")
            if submitted:
                if not person_name.strip():
                    st.warning("Please enter a person's name.")
                elif amount <= 0:
                    st.warning("Please enter an amount greater than zero.")
                else:
                    new_id = str(len(to_take) + len(to_give) + 1) + "-" + str(int(datetime.now().timestamp()))
                    new_entry = {
                        "id": new_id,
                        "person": person_name.strip(),
                        "amount": float(amount),
                        "description": description.strip() if description else "",
                        "date": entry_date.isoformat(),
                    }
                    to_give.append(new_entry)
                    data["to_give"] = to_give
                    save_data(data)
                    st.success(f"Entry added for {person_name}. Your records are updated.")
                    st.rerun()
    
    # Display and manage entries
    if not to_give:
        st.info("No entries yet. Add entries above to track money you owe friends.")
    else:
        for idx, entry in enumerate(to_give):
            entry_id = entry.get("id", str(idx))
            person = entry.get("person", "Unknown")
            amount = entry.get("amount", 0.0)
            description = entry.get("description", "")
            entry_date_str = entry.get("date", date.today().isoformat())
            
            try:
                entry_date_obj = datetime.fromisoformat(entry_date_str).date()
            except (ValueError, TypeError):
                entry_date_obj = date.today()
            
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{person}**")
                    if description:
                        st.caption(description)
                    st.caption(f"Date: {entry_date_obj.strftime('%Y-%m-%d')}")
                with col2:
                    st.metric("Amount", f"{amount:,.2f}")
                with col3:
                    # Edit button
                    edit_key = f"edit_give_{entry_id}"
                    if st.button("✏️ Edit", key=edit_key):
                        st.session_state[f"editing_give_{entry_id}"] = True
                
                with col4:
                    # Delete button
                    if st.button("🗑️ Delete", key=f"delete_give_{entry_id}"):
                        data["to_give"] = [e for e in to_give if e.get("id") != entry_id]
                        save_data(data)
                        st.success(f"Entry for {person} deleted.")
                        st.rerun()
                
                # Edit form (shown when edit button is clicked)
                if st.session_state.get(f"editing_give_{entry_id}", False):
                    with st.form(f"edit_give_form_{entry_id}", clear_on_submit=False):
                        new_person = st.text_input("Person Name", value=person, key=f"person_give_{entry_id}")
                        new_amount = st.number_input("Amount", min_value=0.0, value=float(amount), step=10.0, format="%.2f", key=f"amount_give_{entry_id}")
                        new_description = st.text_area("Description/Notes", value=description, key=f"desc_give_{entry_id}")
                        new_date = st.date_input("Date", value=entry_date_obj, key=f"date_give_{entry_id}")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Save Changes"):
                                entry["person"] = new_person.strip()
                                entry["amount"] = float(new_amount)
                                entry["description"] = new_description.strip()
                                entry["date"] = new_date.isoformat()
                                data["to_give"] = to_give
                                save_data(data)
                                st.session_state[f"editing_give_{entry_id}"] = False
                                st.success("Entry updated successfully.")
                                st.rerun()
                        with col_cancel:
                            if st.form_submit_button("❌ Cancel"):
                                st.session_state[f"editing_give_{entry_id}"] = False
                                st.rerun()
                
                st.divider()
    
    # Note at the bottom
    st.info(
        "💡 **Note**: These records are for your personal reference only. "
        "They do not affect your budget calculations, spending analysis, or savings goals."
    )









def render_about() -> None:
    """
    Render the About tab.

    This section is intentionally simple and clearly commented so it can be
    edited quickly during a hackathon. Modify the text below to suit your use case.
    """
    st.subheader("About This App")

    st.markdown(
        """
        This student-focused allowance tracker is designed to be:

        - **Simple**: One clean dashboard with clear numbers.
        - **Supportive**: No guilt, no judgment, just information.
        - **Persistent**: Your data lives in a local JSON file,
          so it survives browser refreshes and app restarts.

        ### How it works

        - Log your **income** and **expenses** on the Dashboard.
        - Adjust your **monthly allowance** as your situation changes.
        - Use **Insights** to understand your average daily spending,
          safe daily limit, and category patterns.
        - Experiment with **CSV Analysis** using past exports from any tool.
        - Revisit **Previous Months Data** to see gentle summaries over time.

        The goal is to keep you within a **comfortable, safe spending range**
        while reducing surprise and stress around money.
        """
    )






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
        render_insights(data)
    elif page == "Savings":
        render_savings(data)
    elif page == "CSV Analysis":
        render_csv_analysis()
    elif page == "Previous Months Data":
        render_previous_months(data)
    elif page == "To Take & To Give":
        render_to_take_to_give(data)
    elif page == "About":
        render_about()

if __name__ == "__main__":
    main()
