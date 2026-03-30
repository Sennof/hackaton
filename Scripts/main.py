import pandas as pd
import matplotlib.pyplot as plt


# ------------------------------
# 1. Загрузка данных
# ------------------------------
def load_data():
    menu_plan = pd.read_csv('menu_plan.csv')
    sales_fact = pd.read_csv('sales_fact.csv')
    return menu_plan, sales_fact


# ------------------------------
# 2. Объединение и расчёт метрик
# ------------------------------
def merge_and_calc(menu_plan, sales_fact):
    merged = menu_plan.merge(sales_fact, on=['дата', 'день_недели', 'id_блюда'], how='left')
    merged['продано_порций'] = merged['продано_порций'].fillna(0).astype(int)

    merged['выполнение_плана_%'] = (merged['продано_порций'] / merged['план_порций'] * 100).round(1)
    merged['выручка'] = (merged['продано_порций'] * merged['цена']).round(2)

    # Определение статуса (приоритет: перерасход > риск > норма)
    merged['статус'] = 'Норма'
    merged.loc[merged['продано_порций'] > merged['остаток_на_начало'], 'статус'] = 'Перерасход'
    merged.loc[(merged['продано_порций'] <= merged['остаток_на_начало']) &
               (merged['выполнение_плана_%'] < 70), 'статус'] = 'Риск'
    return merged


# ------------------------------
# 3. Агрегации для сводок
# ------------------------------
def create_summaries(df):
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


# ------------------------------
# 4. Рекомендации по корректировке плана
# ------------------------------
def recommend_plan_adjustments(df):
    # Для каждого блюда определяем наиболее частый статус за неделю
    dish_status = df.groupby('id_блюда')['статус'].agg(
        lambda x: x.mode()[0] if not x.mode().empty else 'Норма'
    ).reset_index()

    coeff_map = {'Перерасход': 1.2, 'Риск': 0.8, 'Норма': 1.0}
    dish_status['коэффициент'] = dish_status['статус'].map(coeff_map)

    # Средний план на день по каждому блюду
    dish_plan = df.groupby(['id_блюда', 'блюдо', 'категория'])['план_порций'].mean().reset_index()

    # Слияние со статусами (добавляем столбец 'статус')
    dish_plan = dish_plan.merge(dish_status[['id_блюда', 'статус', 'коэффициент']], on='id_блюда')

    dish_plan['план_рекомендуемый'] = (dish_plan['план_порций'] * dish_plan['коэффициент']).round().astype(int)
    dish_plan['комментарий'] = dish_plan['статус'].apply(
        lambda s: 'Увеличить план на 20% из-за перерасхода' if s == 'Перерасход'
        else 'Уменьшить план на 20% из-за низких продаж' if s == 'Риск'
        else 'Оставить без изменений'
    )
    return dish_plan[['id_блюда', 'блюдо', 'категория', 'план_порций', 'план_рекомендуемый', 'комментарий']]


# ------------------------------
# 5. Сохранение отчёта Excel
# ------------------------------
def save_report(df, day_summary, cat_summary, status_summary, recommendations):
    with pd.ExcelWriter('report.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Детальные данные', index=False)
        day_summary.to_excel(writer, sheet_name='Сводка по дням', index=False)
        cat_summary.to_excel(writer, sheet_name='Сводка по категориям', index=False)
        status_summary.to_excel(writer, sheet_name='Сводка по статусам', index=False)
        recommendations.to_excel(writer, sheet_name='Рекомендации по плану', index=False)


# ------------------------------
# 6. Построение графиков
# ------------------------------
def create_charts(day_summary, cat_summary, status_summary):
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


# ------------------------------
# 7. Текстовые рекомендации
# ------------------------------
def print_recommendations(df, day_summary, cat_summary, recommendations):
    print("\n" + "=" * 60)
    print("РЕКОМЕНДАЦИИ АНАЛИТИКА ПО ФОРМИРОВАНИЮ ПЛАНА НА СЛЕДУЮЩУЮ НЕДЕЛЮ")
    print("=" * 60)

    # 1. Общие выводы по дням недели
    print("\n1. Анализ по дням недели:")
    for _, row in day_summary.iterrows():
        if row['выполнение_плана_%'] < 80:
            print(
                f"   - {row['день_недели']}: выполнение плана {row['выполнение_плана_%']:.1f}% – ниже целевого. Скорректируйте план вниз.")
        elif row['выполнение_плана_%'] > 120:
            print(
                f"   - {row['день_недели']}: выполнение плана {row['выполнение_плана_%']:.1f}% – превышение. Увеличьте план.")

    # 2. По категориям
    print("\n2. Категории с наибольшими отклонениями:")
    for _, row in cat_summary.iterrows():
        if row['выполнение_плана_%'] < 70:
            print(f"   - {row['категория']}: выполнение {row['выполнение_плана_%']:.1f}% – снизьте план.")
        elif row['выполнение_плана_%'] > 130:
            print(f"   - {row['категория']}: выполнение {row['выполнение_плана_%']:.1f}% – увеличьте план.")

    # 3. По статусам
    print("\n3. Анализ статусов:")
    print(
        f"   - Перерасход: {len(df[df['статус'] == 'Перерасход'])} записей – увеличьте план и остатки для этих позиций.")
    print(f"   - Риск: {len(df[df['статус'] == 'Риск'])} записей – пересмотрите план вниз или проведите промо.")
    print(f"   - Норма: {len(df[df['статус'] == 'Норма'])} записей – план можно оставить без изменений.")

    # 4. Конкретные позиции
    print("\n4. Ключевые позиции для корректировки (первые 5 перерасходов и 5 рисков):")
    over = df[df['статус'] == 'Перерасход'].groupby('блюдо')['продано_порций'].sum().sort_values(ascending=False).head(
        5)
    risk = df[df['статус'] == 'Риск'].groupby('блюдо')['продано_порций'].sum().sort_values(ascending=False).head(5)
    if not over.empty:
        print("   Перерасход (увеличить план):")
        for dish, qty in over.items():
            print(f"      - {dish}: продано {qty} порций > остатка")
    if not risk.empty:
        print("   Риск (уменьшить план):")
        for dish, qty in risk.items():
            print(f"      - {dish}: продано {qty} порций, выполнение <70%")

    # 5. Недельные закономерности
    print("\n5. Недельные закономерности:")
    weekend = df[df['день_недели'].isin(['Суббота', 'Воскресенье'])]
    weekday = df[~df['день_недели'].isin(['Суббота', 'Воскресенье'])]
    cat_weekend = weekend.groupby('категория')['продано_порций'].sum()
    cat_weekday = weekday.groupby('категория')['продано_порций'].sum()
    for cat in cat_weekend.index:
        ratio = cat_weekend[cat] / (cat_weekday[cat] + 1) * 100
        if ratio > 150:
            print(f"   - {cat}: в выходные продажи на {ratio:.0f}% выше, чем в будни – увеличьте план на выходные.")

    # 6. Общие рекомендации
    print("\n6. Общие рекомендации:")
    print("   - Используйте скорректированный план из листа 'Рекомендации по плану' отчёта.")
    print("   - Увеличьте остатки на начало дня для позиций с перерасходом.")
    print("   - Внедрите динамическое планирование: каждую неделю пересматривайте планы на основе данных.")
    print("   - Учитывайте сезонные факторы (погода, праздники) при планировании.")
    print("=" * 60 + "\n")


# ------------------------------
# 8. Основная функция
# ------------------------------
def main():
    menu_plan, sales_fact = load_data()
    merged = merge_and_calc(menu_plan, sales_fact)
    day_summary, cat_summary, status_summary = create_summaries(merged)
    recommendations = recommend_plan_adjustments(merged)

    save_report(merged, day_summary, cat_summary, status_summary, recommendations)
    create_charts(day_summary, cat_summary, status_summary)
    print_recommendations(merged, day_summary, cat_summary, recommendations)

    print("Готово! Созданы файлы:")
    print(" - report.xlsx")
    print(" - chart_plan_by_day.png")
    print(" - chart_revenue_by_category.png")
    print(" - chart_status_distribution.png")


if __name__ == "__main__":
    main()