import pandas as pd
import numpy as np


# Calculation of the coefficient of variation of sales for each dish by day of the week
def calculate_cv(df):
    daily_sales = df.groupby(['id_блюда', 'блюдо', 'категория', 'день_недели'])['продано_порций'].sum().reset_index()
    days_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    full_days = pd.DataFrame({'день_недели': days_order})

    result = []
    for (id_, dish, cat), group in daily_sales.groupby(['id_блюда', 'блюдо', 'категория']):
        merged = full_days.merge(group, on='день_недели', how='left')
        merged['продано_порций'] = merged['продано_порций'].fillna(0).astype(int)
        sales = merged['продано_порций'].values
        mean = np.mean(sales)
        if mean > 0:
            cv = (np.std(sales) / mean) * 100
        else:
            cv = 0

        # Classification of stability
        if cv < 30:
            stability = 'Стабильные'
            recommendation = 'План можно оставить без изменений, прогноз простой.'
        elif cv <= 70:
            stability = 'Средняя стабильность'
            recommendation = 'Рекомендуется небольшой запас (5-10% сверх плана).'
        else:
            stability = 'Нестабильные'
            recommendation = 'Увеличить страховой запас (20-30%), чаще мониторить.'

        result.append({
            'id_блюда': id_,
            'блюдо': dish,
            'категория': cat,
            'коэффициент_вариации_%': round(cv, 1),
            'стабильность': stability,
            'рекомендация': recommendation
        })

    return pd.DataFrame(result)

# Output to the console
def print_stability_summary(stability_df):
    print("\n" + "=" * 60)
    print("АНАЛИЗ СТАБИЛЬНОСТИ ПРОДАЖ")
    print("=" * 60)
    summary = stability_df.groupby('стабильность').size().reset_index(name='количество')
    for _, row in summary.iterrows():
        print(f"   - {row['стабильность']}: {row['количество']} позиций")

    if not stability_df.empty:
        print("\n   Самые нестабильные позиции (топ-3):")
        top_unstable = stability_df.nlargest(3, 'коэффициент_вариации_%')
        for _, row in top_unstable.iterrows():
            print(f"      - {row['блюдо']}: CV = {row['коэффициент_вариации_%']}%")

        print("\n   Самые стабильные позиции (топ-3):")
        top_stable = stability_df.nsmallest(3, 'коэффициент_вариации_%')
        for _, row in top_stable.iterrows():
            print(f"      - {row['блюдо']}: CV = {row['коэффициент_вариации_%']}%")
    print("=" * 60 + "\n")