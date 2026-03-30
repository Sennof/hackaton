import pandas as pd
import matplotlib.pyplot as plt

def create_charts(day_summary, cat_summary, status_summary):
    """Строит и сохраняет три графика."""
    # График 1: выполнение плана по дням недели
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

    # График 2: выручка по категориям
    plt.figure(figsize=(10, 5))
    plt.bar(cat_summary['категория'], cat_summary['выручка'], color='lightgreen')
    plt.title('Выручка по категориям, руб.')
    plt.xlabel('Категория')
    plt.ylabel('Выручка, руб.')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('chart_revenue_by_category.png', dpi=150)
    plt.close()

    # График 3: распределение статусов
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