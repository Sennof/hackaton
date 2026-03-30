import pandas as pd

#excel
def save_report(df, day_summary, cat_summary, status_summary, recommendations):
    with pd.ExcelWriter('report.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Детальные данные', index=False)
        day_summary.to_excel(writer, sheet_name='Сводка по дням', index=False)
        cat_summary.to_excel(writer, sheet_name='Сводка по категориям', index=False)
        status_summary.to_excel(writer, sheet_name='Сводка по статусам', index=False)
        recommendations.to_excel(writer, sheet_name='Рекомендации по плану', index=False)