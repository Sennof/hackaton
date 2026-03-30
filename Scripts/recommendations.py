import pandas as pd


def recommend_plan_adjustments(df):
    dish_status = df.groupby('id_блюда')['статус'].agg(
        lambda x: x.mode()[0] if not x.mode().empty else 'Норма'
    ).reset_index()

    coeff_map = {'Перерасход': 1.2, 'Риск': 0.8, 'Норма': 1.0}
    dish_status['коэффициент'] = dish_status['статус'].map(coeff_map)

    dish_plan = df.groupby(['id_блюда', 'блюдо', 'категория'])['план_порций'].mean().reset_index()

    dish_plan = dish_plan.merge(dish_status[['id_блюда', 'статус', 'коэффициент']], on='id_блюда')

    dish_plan['план_рекомендуемый'] = (dish_plan['план_порций'] * dish_plan['коэффициент']).round().astype(int)
    dish_plan['комментарий'] = dish_plan['статус'].apply(
        lambda s: 'Увеличить план на 20% из-за перерасхода' if s == 'Перерасход'
        else 'Уменьшить план на 20% из-за низких продаж' if s == 'Риск'
        else 'Оставить без изменений'
    )
    return dish_plan[['id_блюда', 'блюдо', 'категория', 'план_порций', 'план_рекомендуемый', 'комментарий']]

# Display recommendations by category
def print_recommendations(df, day_summary, cat_summary):
    print("🎯<b>РЕКОМЕНДАЦИИ АНАЛИТИКА ПО ФОРМИРОВАНИЮ ПЛАНА НА СЛЕДУЮЩУЮ НЕДЕЛЮ</b>🎯\n")

    print("1. <i>Анализ по дням недели:</i>")
    has_day_deviations = False
    for _, row in day_summary.iterrows():
        if row['выполнение_плана_%'] < 80:
            print(
                f"   - {row['день_недели']}: выполнение плана {row['выполнение_плана_%']:.1f}% – ниже целевого. Скорректируйте план вниз.")
            has_day_deviations = True
        elif row['выполнение_плана_%'] > 120:
            print(
                f"   - {row['день_недели']}: выполнение плана {row['выполнение_плана_%']:.1f}% – превышение. Увеличьте план.")
            has_day_deviations = True
    if not has_day_deviations:
        print("   Ни один день не имеет выполнения плана ниже 80% или выше 120%.")

    print("2. <i>Категории с наибольшими отклонениями:</i>")
    has_cat_deviations = False
    for _, row in cat_summary.iterrows():
        if row['выполнение_плана_%'] < 70:
            print(f"   - {row['категория']}: выполнение {row['выполнение_плана_%']:.1f}% – снизьте план.")
            has_cat_deviations = True
        elif row['выполнение_плана_%'] > 130:
            print(f"   - {row['категория']}: выполнение {row['выполнение_плана_%']:.1f}% – увеличьте план.")
            has_cat_deviations = True
    if not has_cat_deviations:
        print("   Ни одна категория не имеет выполнения плана ниже 70% или выше 130%.")

    print("3. <i>Анализ статусов:</i>")
    print(
        f"   - Перерасход: {len(df[df['статус'] == 'Перерасход'])} записей – увеличьте план и остатки для этих позиций.")
    print(f"   - Риск: {len(df[df['статус'] == 'Риск'])} записей – пересмотрите план вниз или проведите промо.")
    print(f"   - Норма: {len(df[df['статус'] == 'Норма'])} записей – план можно оставить без изменений.")

    print("4. <i>Ключевые позиции для корректировки (первые 5 перерасходов и 5 рисков):</i>")
    over = df[df['статус'] == 'Перерасход'].groupby('блюдо')['продано_порций'].sum().sort_values(ascending=False).head(
        5)
    risk = df[df['статус'] == 'Риск'].groupby('блюдо')['продано_порций'].sum().sort_values(ascending=False).head(5)
    if not over.empty:
        print("   Перерасход (увеличить план):")
        for dish, qty in over.items():
            print(f"      - {dish}: продано {qty} порций &gt; остатка")
    else:
        print("   Нет позиций с перерасходом.")
    if not risk.empty:
        print("   Риск (уменьшить план):")
        for dish, qty in risk.items():
            print(f"      - {dish}: продано {qty} порций, выполнение &lt;70%")
    else:
        print("   Нет позиций с риском низких продаж.")

    print("5. <i>Недельные закономерности:</i>")
    weekend = df[df['день_недели'].isin(['Суббота', 'Воскресенье'])]
    weekday = df[~df['день_недели'].isin(['Суббота', 'Воскресенье'])]
    cat_weekend = weekend.groupby('категория')['продано_порций'].sum()
    cat_weekday = weekday.groupby('категория')['продано_порций'].sum()
    has_weekend_pattern = False
    for cat in cat_weekend.index:
        ratio = cat_weekend[cat] / (cat_weekday[cat] + 1) * 100
        if ratio > 150:
            print(f"   - {cat}: в выходные продажи на {ratio:.0f}% выше, чем в будни – увеличьте план на выходные.")
            has_weekend_pattern = True
    if not has_weekend_pattern:
        print("   Не выявлено категорий с ростом продаж в выходные более чем на 150%.")

    print("6. <i>Общие рекомендации:</i>")
    print("   - Используйте скорректированный план из листа 'Рекомендации по плану' отчёта.")
    print("   - Увеличьте остатки на начало дня для позиций с перерасходом.")
    print("   - Внедрите динамическое планирование: каждую неделю пересматривайте планы на основе данных.")
    print("   - Учитывайте сезонные факторы (погода, праздники) при планировании.")