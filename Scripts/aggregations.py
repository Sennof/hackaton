import pandas as pd

def create_summaries(df):
    """Создаёт сводные таблицы по дням, категориям и статусам."""
    # Сводка по дням
    day_summary = df.groupby('день_недели', as_index=False).agg({
        'продано_порций': 'sum',
        'план_порций': 'sum',
        'выручка': 'sum'
    })
    day_summary['выполнение_плана_%'] = (day_summary['продано_порций'] / day_summary['план_порций'] * 100).round(1)

    # Сводка по категориям
    cat_summary = df.groupby('категория', as_index=False).agg({
        'продано_порций': 'sum',
        'план_порций': 'sum',
        'выручка': 'sum'
    })
    cat_summary['выполнение_плана_%'] = (cat_summary['продано_порций'] / cat_summary['план_порций'] * 100).round(1)

    # Сводка по статусам
    status_summary = df.groupby('статус', as_index=False).size().rename(columns={'size': 'количество_позиций'})

    return day_summary, cat_summary, status_summary