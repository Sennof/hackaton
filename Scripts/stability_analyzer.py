import pandas as pd
import numpy as np


def calculate_cv(df):
    """
    Рассчитывает коэффициент вариации продаж для каждого блюда по дням недели.
    Возвращает DataFrame с полями: id_блюда, блюдо, категория, cv, стабильность, рекомендация.
    """
    # Группируем по блюду и дню недели, суммируем продажи
    daily_sales = df.groupby(['id_блюда', 'блюдо', 'категория', 'день_недели'])['продано_порций'].sum().reset_index()

    # Получаем список всех дней недели для полноты (если в какой-то день не было продаж, будет 0)
    days_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    full_days = pd.DataFrame({'день_недели': days_order})

    # Для каждого блюда создаём полную таблицу дней
    result = []
    for (id_, dish, cat), group in daily_sales.groupby(['id_блюда', 'блюдо', 'категория']):
        # Слияние с полным списком дней, заполняем пропуски 0
        merged = full_days.merge(group, on='день_недели', how='left')
        merged['продано_порций'] = merged['продано_порций'].fillna(0).astype(int)
        sales = merged['продано_порций'].values
        mean = np.mean(sales)
        if mean > 0:
            cv = (np.std(sales) / mean) * 100
        else:
            cv = 0

        # Классификация стабильности
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


def print_stability_summary(stability_df):
    """Выводит в консоль краткую сводку по стабильности."""
    print("\n\n🧮<b>АНАЛИЗ СТАБИЛЬНОСТИ ПРОДАЖ</b>🧮")
    summary = stability_df.groupby('стабильность').size().reset_index(name='количество')
    for _, row in summary.iterrows():
        print(f"   - {row['стабильность']}: {row['количество']} позиций")

    # Показываем топ-3 самых нестабильных и самых стабильных
    if not stability_df.empty:
        print("\n   <i>Самые нестабильные позиции</i> (топ-3):")
        top_unstable = stability_df.nlargest(3, 'коэффициент_вариации_%')
        for _, row in top_unstable.iterrows():
            print(f"      - {row['блюдо']}: CV = {row['коэффициент_вариации_%']}%")

        print("\n   <i>Самые стабильные позиции</i> (топ-3):")
        top_stable = stability_df.nsmallest(3, 'коэффициент_вариации_%')
        for _, row in top_stable.iterrows():
            print(f"      - {row['блюдо']}: CV = {row['коэффициент_вариации_%']}%")