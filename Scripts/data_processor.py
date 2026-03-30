import pandas as pd


# Combining tables and calculating their components
def merge_and_calc(menu_plan, sales_fact):
    merged = menu_plan.merge(sales_fact, on=['дата', 'день_недели', 'id_блюда'], how='left')
    merged['продано_порций'] = merged['продано_порций'].fillna(0).astype(int)
    merged['выполнение_плана_%'] = (merged['продано_порций'] / merged['план_порций'] * 100).round(1)
    merged['выручка'] = (merged['продано_порций'] * merged['цена']).round(2)
    merged['статус'] = 'Норма'
    merged.loc[merged['продано_порций'] > merged['остаток_на_начало'], 'статус'] = 'Перерасход'
    merged.loc[(merged['продано_порций'] <= merged['остаток_на_начало']) &
               (merged['выполнение_плана_%'] < 70), 'статус'] = 'Риск'
    return merged