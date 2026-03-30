import data_loader
import data_processor
import aggregations
import recommendations
import report_saver
import chart_builder

def main():
    # 1. Загрузка данных
    menu_plan, sales_fact = data_loader.load_data()

    # 2. Обработка и расчёт
    merged = data_processor.merge_and_calc(menu_plan, sales_fact)

    # 3. Сводки
    day_summary, cat_summary, status_summary = aggregations.create_summaries(merged)

    # 4. Рекомендации по корректировке плана
    rec_df = recommendations.recommend_plan_adjustments(merged)

    # 5. Сохранение отчёта
    report_saver.save_report(merged, day_summary, cat_summary, status_summary, rec_df)

    # 6. Построение графиков
    chart_builder.create_charts(day_summary, cat_summary, status_summary)

    # 7. Вывод текстовых рекомендаций
    recommendations.print_recommendations(merged, day_summary, cat_summary, rec_df)

    print("Готово! Созданы файлы:")
    print(" - report.xlsx")
    print(" - chart_plan_by_day.png")
    print(" - chart_revenue_by_category.png")
    print(" - chart_status_distribution.png")

if __name__ == "__main__":
    main()