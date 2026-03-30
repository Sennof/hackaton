import pandas as pd
import numpy as np

def create_summaries(df):
    # Creating pivot tables
    day_summary = df.groupby('день_недели', as_index=False).agg({
        'продано_порций': 'sum',
        'план_порций': 'sum',
        'выручка': 'sum'
    })

    day_summary['выполнение_плана_%'] = np.where(
        day_summary['план_порций'] != 0,
        (day_summary['продано_порций'] / day_summary['план_порций'] * 100).round(1),
        0
    )

    # Summary by categories and statuses
    cat_summary = df.groupby('категория', as_index=False).agg({
        'продано_порций': 'sum',
        'план_порций': 'sum',
        'выручка': 'sum'
    })
    cat_summary['выполнение_плана_%'] = np.where(
        cat_summary['план_порций'] != 0,
        (cat_summary['продано_порций'] / cat_summary['план_порций'] * 100).round(1),
        0
    )
    status_summary = df.groupby('статус', as_index=False).size().rename(columns={'size': 'количество_позиций'})

    return day_summary, cat_summary, status_summary