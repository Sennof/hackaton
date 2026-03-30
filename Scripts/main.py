import data_loader
import data_processor
import aggregations
import recommendations
import report_saver
import chart_builder
import stability_analyzer  # новый модуль

def main():
    #loading data
    menu_plan, sales_fact = data_loader.load_data()

    #core
    merged = data_processor.merge_and_calc(menu_plan, sales_fact)
    day_summary, cat_summary, status_summary = aggregations.create_summaries(merged)
    rec_df = recommendations.recommend_plan_adjustments(merged)
    stability_df = stability_analyzer.calculate_cv(merged)  # новый расчёт
    report_saver.save_report(merged, day_summary, cat_summary, status_summary, rec_df, stability_df)
    chart_builder.create_charts(day_summary, cat_summary, status_summary, stability_df)  # передаём stability_df
    recommendations.print_recommendations(merged, day_summary, cat_summary)
    stability_analyzer.print_stability_summary(stability_df)  # вывод в консоль

    #logging
    print("Готово! Созданы файлы:")
    print(" - report.xlsx")
    print(" - chart_plan_by_day.png")
    print(" - chart_revenue_by_category.png")
    print(" - chart_status_distribution.png")
    print(" - chart_stability.png")  # новый график

if __name__ == "__main__":
    main()