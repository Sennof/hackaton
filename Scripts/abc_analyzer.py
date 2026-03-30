import pandas as pd


def perform_abc_analysis(df):
    """
    Выполняет ABC-анализ по сумме выручки блюд за неделю.
    Возвращает DataFrame с полями: блюдо, категория, общая_выручка, доля_%, кумулятивная_доля_%, abc_категория.
    """
    # Группируем по блюду и категории, суммируем выручку
    dish_revenue = df.groupby(['блюдо', 'категория'])['выручка'].sum().reset_index()
    dish_revenue = dish_revenue.sort_values('выручка', ascending=False).reset_index(drop=True)

    # Общая выручка
    total_revenue = dish_revenue['выручка'].sum()

    # Расчёт доли и кумулятивной доли
    dish_revenue['доля_%'] = (dish_revenue['выручка'] / total_revenue * 100).round(1)
    dish_revenue['кумулятивная_доля_%'] = dish_revenue['доля_%'].cumsum().round(1)

    # Присвоение категорий ABC
    conditions = [
        dish_revenue['кумулятивная_доля_%'] <= 80,
        (dish_revenue['кумулятивная_доля_%'] > 80) & (dish_revenue['кумулятивная_доля_%'] <= 95),
        dish_revenue['кумулятивная_доля_%'] > 95
    ]
    choices = ['A', 'B', 'C']
    dish_revenue['abc_категория'] = pd.Series(pd.NA, index=dish_revenue.index)
    dish_revenue['abc_категория'] = dish_revenue['abc_категория'].fillna('')
    for i, cond in enumerate(conditions):
        dish_revenue.loc[cond, 'abc_категория'] = choices[i]

    # Добавляем рекомендации по управлению
    rec_map = {
        'A': 'Основные позиции: поддерживать наличие, контролировать запасы, проводить акции с осторожностью.',
        'B': 'Стабильные позиции: поддерживать план, возможно умеренное продвижение.',
        'C': 'Позиции с низкой выручкой: пересмотреть необходимость, возможно исключить или заменить.'
    }
    dish_revenue['рекомендация'] = dish_revenue['abc_категория'].map(rec_map)

    return dish_revenue


def print_abc_summary(abc_df):
    """Выводит в консоль краткую сводку ABC-анализа."""
    print("\n\nABC-АНАЛИЗ БЛЮД (ПО ВЫРУЧКЕ)")
    summary = abc_df.groupby('abc_категория').agg({
        'блюдо': 'count',
        'выручка': 'sum'
    }).rename(columns={'блюдо': 'количество_позиций', 'выручка': 'общая_выручка'}).reset_index()
    summary['доля_выручки_%'] = (summary['общая_выручка'] / summary['общая_выручка'].sum() * 100).round(1)

    for _, row in summary.iterrows():
        print(f"   Категория {row['abc_категория']}: {row['количество_позиций']} позиций, "
              f"выручка {row['общая_выручка']:,.0f} руб. ({row['доля_выручки_%']}%)")

    print("\n   Топ-5 позиций категории A:")
    top_a = abc_df[abc_df['abc_категория'] == 'A'].head(5)
    for _, row in top_a.iterrows():
        print(f"      - {row['блюдо']}: {row['выручка']:,.0f} руб. ({row['доля_%']}%)")

    print("\n   Позиции категории C (можно пересмотреть):")
    c_items = abc_df[abc_df['abc_категория'] == 'C']
    if not c_items.empty:
        for _, row in c_items.iterrows():
            print(f"      - {row['блюдо']}: {row['выручка']:,.0f} руб. ({row['доля_%']}%)")
    else:
        print("      Нет позиций категории C.")