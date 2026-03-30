import pandas as pd

def load_data():
    """Загружает плановые и фактические данные из CSV."""
    menu_plan = pd.read_csv('menu_plan.csv')
    sales_fact = pd.read_csv('sales_fact.csv')
    return menu_plan, sales_fact