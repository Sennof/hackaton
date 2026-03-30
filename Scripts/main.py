import data_loader
import data_processor
import aggregations
import recommendations
import report_saver
import chart_builder

def main():
    #loading data
    menu_plan, sales_fact = data_loader.load_data()

    #core
    merged = data_processor.merge_and_calc(menu_plan, sales_fact)
    day_summary, cat_summary, status_summary = aggregations.create_summaries(merged)
    rec_df = recommendations.recommend_plan_adjustments(merged)
    report_saver.save_report(merged, day_summary, cat_summary, status_summary, rec_df)
    chart_builder.create_charts(day_summary, cat_summary, status_summary)
    recommendations.print_recommendations(merged, day_summary, cat_summary, rec_df)

    #logging
    print("Готово! Созданы файлы:")
    print(" - report.xlsx")
    print(" - chart_plan_by_day.png")
    print(" - chart_revenue_by_category.png")
    print(" - chart_status_distribution.png")

if __name__ == "__main__":
    main()