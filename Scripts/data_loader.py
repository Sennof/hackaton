import pandas as pd


# Uploading data from CSV
def load_data():
    menu_plan = pd.read_csv('menu_plan.csv')
    sales_fact = pd.read_csv('sales_fact.csv')
    return menu_plan, sales_fact