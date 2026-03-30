import pandas as pd

# excel
def save_report(df, day_summary, cat_summary, status_summary, recommendations, stability_df, abc_df):
    with pd.ExcelWriter('report.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Детальные данные', index=False)
        day_summary.to_excel(writer, sheet_name='Сводка по дням', index=False)
        cat_summary.to_excel(writer, sheet_name='Сводка по категориям', index=False)
        status_summary.to_excel(writer, sheet_name='Сводка по статусам', index=False)
        recommendations.to_excel(writer, sheet_name='Рекомендации по плану', index=False)
        stability_df.to_excel(writer, sheet_name='Анализ стабильности', index=False)
        abc_df.to_excel(writer, sheet_name='ABC-анализ', index=False)