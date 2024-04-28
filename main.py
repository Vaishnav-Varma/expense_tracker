import streamlit as st
import pandas as pd
from PIL import Image
import pytesseract
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import re

# Set Tesseract executable path explicitly
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Set page title and favicon
st.set_page_config(page_title='Expense Tracker', page_icon=':dollar:', layout='wide')


import json
from auth import register_user, authenticate_user

# Create an empty users.json file if it doesn't exist
try:
    with open('users.json', 'r') as file:
        pass
except FileNotFoundError:
    with open('users.json', 'w') as file:
        json.dump({'users': []}, file)

# Global variable to store the current user
current_user = None


# Load sample expense data
def load_data():
    data = pd.read_csv('expense_data.csv')
    data['Date'] = pd.to_datetime(data['Date'])  # Convert 'Date' column to datetime
    return data

# Initialize expense_data
expense_data = load_data()

# Function to perform OCR on uploaded receipt image
def ocr_extraction(image):
    extracted_text = pytesseract.image_to_string(image)
    return extracted_text

# Function to add expense to the database
def add_expense(description, category, amount, date):
    global expense_data
    new_expense = {'Description': description, 'Category': category, 'Amount': amount, 'Date': date}
    expense_data = expense_data.append(new_expense, ignore_index=True)
    # Update CSV file
    expense_data.to_csv('expense_data.csv', index=False)

import plotly.express as px


def calculate_expense_statistics(data):
    data['Date'] = pd.to_datetime(data['Date'])
    monthly_expenses = data.groupby([data['Date'].dt.year, data['Date'].dt.month])['Amount'].sum().reset_index(drop=True)
    weekly_expenses = data.groupby([data['Date'].dt.year, data['Date'].dt.week])['Amount'].sum().reset_index(drop=True)
    yearly_expenses = data.groupby(data['Date'].dt.year)['Amount'].sum().reset_index(drop=True)
    return monthly_expenses, weekly_expenses, yearly_expenses

# Function to set budget limits and display budget charts
def set_budget():
    st.title("Set Budget")
    st.write("Set budget limits for expense categories:")
    
    categories = pd.unique(expense_data['Category'])  # Get unique categories from expense_data
    category_budgets = {}
    
    for category in categories:
        default_budget = suggest_budget(category)  # Get suggested budget based on previous spending
        budget_limit = st.number_input(f"Budget for {category}", value=default_budget, min_value=0.0, step=100.0)
        category_budgets[category] = budget_limit
    
    save_button = st.button("Save Budget Limits")
    if save_button:
        # Store budget limits in a file or database for future reference
        st.write("Budget limits saved successfully!")
        
        # Display pie chart for budget allocation across categories
        st.write("## Budget Allocation Across Categories")
        plot_pie_chart(category_budgets, "Budget Allocation")
        
        # Calculate and display budget usage for the current month
        current_month_expenses = expense_data[expense_data['Date'].dt.month == datetime.today().month]
        category_expenses = current_month_expenses.groupby('Category')['Amount'].sum()
        
        # Calculate percentage of budget used per category for the current month
        budget_usage = {category: category_expenses.get(category, 0) / category_budgets.get(category, 1) * 100 for category in categories}
        
        st.write("## Budget Usage for Current Month")
        st.write("Percentage of Budget Used per Category:")
        st.write(pd.Series(budget_usage).sort_index())
        st.write("## Budget Usage Chart for Current Month")
        plot_pie_chart(budget_usage, "Budget Usage for Current Month")

# Function to suggest budget for a specific category based on previous spending
def suggest_budget(category):
    # Calculate average spending for the category over the last few months (e.g., 3 months)
    recent_months = 3
    today = datetime.today()
    start_date = today - pd.DateOffset(months=recent_months)
    
    category_expenses = expense_data[(expense_data['Category'] == category) & (expense_data['Date'] >= start_date)]
    average_spending = category_expenses['Amount'].mean()
    
    # Suggest 110% of the average spending as the budget limit
    suggested_budget = average_spending * 1.1 if not pd.isnull(average_spending) else 0.0
    
    return suggested_budget

# Function to plot a pie chart
def plot_pie_chart(data_dict, title):
    labels = list(data_dict.keys())
    sizes = list(data_dict.values())
    
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.set_title(title)
    
    st.pyplot(fig)

import re
from datetime import datetime

def parse_extracted_text(extracted_text):
    descriptions = []
    amounts = []
    date = None

    # Extract date
    match = re.search(r'\d{2}/\d{2}/\d{2}', extracted_text)
    if match:
        date_str = match.group()
        date = datetime.strptime(date_str, '%m/%d/%y').date()

    # Extract item descriptions and amounts
    lines = extracted_text.split('\n')
    in_item_list = False
    for line in lines:
        line = line.strip()

        # Check for the start of the item list
        if line.startswith('ITEM'):
            in_item_list = True
            continue

        if in_item_list:
            # Extract item description
            match = re.search(r'^(\d+)\s+(.+?)\s+\d+', line)
            if match:
                item_number, description = match.groups()
                descriptions.append(description)

            # Extract item amount
            match = re.search(r'\$(\d+\.\d{2})', line)
            if match:
                amount = float(match.group(1))
                amounts.append(amount)

    return descriptions, amounts, date


# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Dashboard", "All Expenses", "Upload Receipt", "Set Budget", "Login/Register", "Manage Categories"])


if page == "Dashboard":
    st.title("Expense Tracker Dashboard")
    st.write("## Add Quick Expense")
    with st.form(key='quick_expense_form'):
        description = st.text_input("Description")
        new_category = st.text_input("New Category (if not listed)")
        category = new_category if new_category else st.selectbox("Category", pd.unique(expense_data['Category']))
        amount = st.number_input("Amount", min_value=0.01, step=0.01)
        date = st.date_input("Date", value=datetime.today())
        submit_button = st.form_submit_button(label='Add Expense')
        if submit_button:
            add_expense(description, category, amount, date)
            st.success("Expense added successfully!")
            # Reload data after adding expense
            expense_data = load_data()

    st.write("## Expense Visualizations")
    monthly_expenses, weekly_expenses, yearly_expenses = calculate_expense_statistics(expense_data)

    st.write("### Monthly Expenses")
    fig = px.line(monthly_expenses, x=monthly_expenses.index, y="Amount", title="Monthly Expenses")
    st.plotly_chart(fig)

    st.write("### Weekly Expenses")
    fig = px.bar(weekly_expenses, x=weekly_expenses.index, y="Amount", title="Weekly Expenses")
    st.plotly_chart(fig)

    st.write("### Yearly Expenses")
    fig = px.pie(yearly_expenses, values="Amount", names=yearly_expenses.index, title="Yearly Expenses")
    st.plotly_chart(fig)

elif page == "All Expenses":
    st.title("All Expenses")
    expense_data = load_data()

    search_term = st.text_input("Search expenses")
    category_filter = st.multiselect("Filter by category", pd.unique(expense_data["Category"]))
    start_date = datetime.combine(st.date_input("Start date", value=expense_data["Date"].min().date()), datetime.min.time())
    end_date = datetime.combine(st.date_input("End date", value=expense_data["Date"].max().date()), datetime.max.time())

    filtered_data = expense_data.copy()
    if search_term:
        filtered_data = filtered_data[filtered_data["Description"].str.contains(search_term, case=False)]
    if category_filter:
        filtered_data = filtered_data[filtered_data["Category"].isin(category_filter)]
    filtered_data = filtered_data[(filtered_data["Date"] >= start_date) & (filtered_data["Date"] <= end_date)]

    st.write(filtered_data)
    st.write("## Expenses per Category")
    expenses_by_category = filtered_data.groupby("Category")["Amount"].sum()
    st.bar_chart(expenses_by_category)

elif page == "Upload Receipt":
    st.title("Upload Receipt")
    uploaded_file = st.file_uploader("Choose a receipt image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        receipt_image = Image.open(uploaded_file)
        st.image(receipt_image, caption='Uploaded Receipt', use_column_width=True)
        extract_button = st.button("Extract Expense Information")
        if extract_button:
            extracted_text = ocr_extraction(receipt_image)
            st.write("### Extracted Text:")
            st.write(extracted_text)
            descriptions, amounts, date = parse_extracted_text(extracted_text)
            if descriptions and amounts and date:
                for desc, amt in zip(descriptions, amounts):
                    add_expense(desc, "Groceries", amt, date)
                st.success("Expense details extracted and added successfully!")
            else:
                st.warning("Failed to extract expense details from the text.")

elif page == "Set Budget":
    set_budget()

elif page == "Manage Categories":
    st.title("Manage Expense Categories")

    categories = pd.unique(expense_data['Category'])
    selected_category = st.selectbox("Select a Category", categories)

    if st.button("Add Category"):
        new_category = st.text_input("Enter new category name")
        if new_category:
            expense_data["Category"] = expense_data["Category"].replace(np.nan, new_category, inplace=True)
            expense_data = expense_data.drop_duplicates(subset=["Description", "Category", "Amount", "Date"], keep="last")
            expense_data.to_csv("expense_data.csv", index=False)
            st.success(f"Category '{new_category}' added successfully!")

    if st.button("Edit Category"):
        new_name = st.text_input("Enter new category name", selected_category)
        if new_name:
            expense_data.loc[expense_data["Category"] == selected_category, "Category"] = new_name
            expense_data.to_csv("expense_data.csv", index=False)
            st.success(f"Category '{selected_category}' renamed to '{new_name}'!")

    if st.button("Delete Category"):
        confirm = st.checkbox("Confirm deletion")
        if confirm:
            expense_data = expense_data[expense_data["Category"] != selected_category]
            expense_data.to_csv("expense_data.csv", index=False)
            st.success(f"Category '{selected_category}' deleted successfully!")

elif page == "Login/Register":
    st.title("Login/Register")

    login_or_register = st.radio("Select an option", ["Login", "Register"])

    if login_or_register == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.button("Login")
        if login_button:
            if authenticate_user(username, password):
                st.success(f"Logged in as {username}")
                current_user = username
            else:
                st.error("Invalid username or password")

    elif login_or_register == "Register":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        email = st.text_input("Email")
        register_button = st.button("Register")
        if register_button:
            if register_user(username, password, email):
                st.success(f"User '{username}' registered successfully!")
            else:
                st.error("Registration failed. Please try again with a different username.")








import time

def export_data(format):
    if format == "CSV":
        expense_data.to_csv("expense_data.csv", index=False)
        st.success("Expense data exported successfully as CSV file.")
    elif format == "Excel":
        expense_data.to_excel("expense_data.xlsx", index=False)
        st.success("Expense data exported successfully as Excel file.")

def backup_data():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_file = f"expense_data_backup_{timestamp}.csv"
    expense_data.to_csv(backup_file, index=False)
    st.success(f"Expense data backed up successfully as '{backup_file}'.")

if st.sidebar.button("Export Data"):
    export_format = st.selectbox("Select export format", ["CSV", "Excel"])
    export_data(export_format)

if st.sidebar.button("Backup Data"):
    backup_data()

def logout():
    global current_user
    current_user = None
    st.success("Logged out successfully.")

logout_button = st.sidebar.button("Logout")
if logout_button:
    logout()

# Display footer
st.sidebar.text("© 2024 Expense Tracker App")
