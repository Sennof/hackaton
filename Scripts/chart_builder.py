import pandas as pd
import matplotlib.pyplot as plt

def create_charts(day_summary, cat_summary, status_summary, stability_df, abc_df):
    # Plan execution by day of the week
    plt.figure(figsize=(10, 5))
    days_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    day_summary['день_недели'] = pd.Categorical(day_summary['день_недели'], categories=days_order, ordered=True)
    day_summary = day_summary.sort_values('день_недели')
    plt.bar(day_summary['день_недели'], day_summary['выполнение_плана_%'], color='skyblue')
    plt.title('Выполнение плана по дням недели, %')
    plt.xlabel('День недели')
    plt.ylabel('Выполнение плана, %')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('chart_plan_by_day.png', dpi=150)
    plt.close()

    # Revenue by category
    plt.figure(figsize=(10, 5))
    plt.bar(cat_summary['категория'], cat_summary['выручка'], color='lightgreen')
    plt.title('Выручка по категориям, руб.')
    plt.xlabel('Категория')
    plt.ylabel('Выручка, руб.')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('chart_revenue_by_category.png', dpi=150)
    plt.close()

    # Distribution of statuses
    plt.figure(figsize=(8, 5))
    colors = {'Перерасход': 'red', 'Риск': 'orange', 'Норма': 'green'}
    status_summary['color'] = status_summary['статус'].map(colors)
    plt.bar(status_summary['статус'], status_summary['количество_позиций'], color=status_summary['color'])
    plt.title('Количество позиций по статусам')
    plt.xlabel('Статус')
    plt.ylabel('Количество позиций')
    plt.tight_layout()
    plt.savefig('chart_status_distribution.png', dpi=150)
    plt.close()

    # Distribution of stability categories
    plt.figure(figsize=(8, 5))
    stability_counts = stability_df.groupby('стабильность').size().reset_index(name='количество')
    stability_counts = stability_counts.sort_values('стабильность', ascending=False)
    colors = {'Стабильные': 'green', 'Средняя стабильность': 'orange', 'Нестабильные': 'red'}
    plt.bar(stability_counts['стабильность'], stability_counts['количество'],
            color=[colors[cat] for cat in stability_counts['стабильность']])
    plt.title('Распределение позиций по стабильности продаж')
    plt.xlabel('Стабильность')
    plt.ylabel('Количество позиций')
    plt.tight_layout()
    plt.savefig('chart_stability.png', dpi=150)
    plt.close()

    # ABC distribution
    plt.figure(figsize=(8, 5))
    abc_counts = abc_df.groupby('abc_категория').size().reset_index(name='количество')
    abc_counts = abc_counts.sort_values('abc_категория')
    colors_abc = {'A': 'gold', 'B': 'silver', 'C': 'peru'}
    plt.bar(abc_counts['abc_категория'], abc_counts['количество'],
            color=[colors_abc[cat] for cat in abc_counts['abc_категория']])
    plt.title('Количество позиций по категориям ABC')
    plt.xlabel('Категория ABC')
    plt.ylabel('Количество позиций')
    plt.tight_layout()
    plt.savefig('chart_abc_distribution.png', dpi=150)
    plt.close()