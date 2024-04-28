import pandas as pd
import random
from datetime import datetime, timedelta

# Define the number of sample expenses to generate
num_expenses = 100

# Define lists of sample categories and descriptions
categories = ['Groceries', 'Utilities', 'Entertainment', 'Transportation', 'Dining', 'Shopping']
descriptions = ['Supermarket', 'Electric bill', 'Movie ticket', 'Taxi ride', 'Restaurant', 'Clothing store']

# Generate sample expense data
data = {
    'Date': [datetime.today() - timedelta(days=random.randint(1, 365)) for _ in range(num_expenses)],
    'Description': [random.choice(descriptions) for _ in range(num_expenses)],
    'Category': [random.choice(categories) for _ in range(num_expenses)],
    'Amount': [round(random.uniform(10, 200), 2) for _ in range(num_expenses)]
}

# Create a DataFrame
expense_df = pd.DataFrame(data)

# Save DataFrame to CSV file
expense_df.to_csv('expense_data.csv', index=False)

print(f"Sample expense data saved to expense_data.csv with {num_expenses} entries.")
