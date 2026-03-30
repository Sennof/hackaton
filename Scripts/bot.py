import os
import io
import tempfile
from contextlib import redirect_stdout

import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# Import our modules
import data_loader
import data_processor
import aggregations
import recommendations
import report_saver
import chart_builder
import stability_analyzer
import abc_analyzer

# Conversation states
WAIT_SALES, WAIT_MENU, CALCULATE = range(3)

# Storage keys for user data
USER_DATA_SALES = "sales_path"
USER_DATA_MENU = "menu_path"

#Check that filename matches expected name and has .csv extension
def validate_filename(filename: str, expected_name: str) -> bool:
    return filename.lower() == f"{expected_name.lower()}.csv"

#Handle /start command — initiate the conversation.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! Я помогу вам проанализировать продажи кафе.\n"
        "Пожалуйста, отправьте файл с фактическими продажами (sales_fact.csv)."
    )
    return WAIT_SALES

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Сообщение не распознано")

async def handle_sales_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    if not document:
        await update.message.reply_text("Пожалуйста, отправьте файл.")
        return WAIT_SALES

    filename = document.file_name
    if not validate_filename(filename, "sales_fact"):
        await update.message.reply_text(
            "Неверный файл. Нужен файл с именем sales_fact.csv.\n"
            "Попробуйте ещё раз."
        )
        return WAIT_SALES

    file = await document.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        await file.download_to_drive(tmp.name)
        context.user_data[USER_DATA_SALES] = tmp.name

    await update.message.reply_text(
        "Файл sales_fact.csv принят.\n"
        "Теперь отправьте файл с планом (menu_plan.csv)."
    )
    return WAIT_MENU

async def handle_menu_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    if not document:
        await update.message.reply_text("Пожалуйста, отправьте файл.")
        return WAIT_MENU

    filename = document.file_name
    if not validate_filename(filename, "menu_plan"):
        await update.message.reply_text(
            "Неверный файл. Нужен файл с именем menu_plan.csv.\n"
            "Попробуйте ещё раз."
        )
        return WAIT_MENU

    file = await document.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        await file.download_to_drive(tmp.name)
        context.user_data[USER_DATA_MENU] = tmp.name

    keyboard = [[InlineKeyboardButton("Рассчитать", callback_data="calculate")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Всё готово! Нажмите кнопку, чтобы начать расчёт.",
        reply_markup=reply_markup
    )
    return CALCULATE

#Run the analysis after user clicks the button.
async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    sales_path = context.user_data.get(USER_DATA_SALES)
    menu_path = context.user_data.get(USER_DATA_MENU)
    if not sales_path or not menu_path:
        await query.edit_message_text("Ошибка: файлы не найдены. Начните заново с /start")
        return ConversationHandler.END

    await query.edit_message_text("Выполняю расчёт... Это может занять несколько секунд.")

    try:
        menu_plan = pd.read_csv(menu_path)
        sales_fact = pd.read_csv(sales_path)

        merged = data_processor.merge_and_calc(menu_plan, sales_fact)
        day_summary, cat_summary, status_summary = aggregations.create_summaries(merged)
        rec_df = recommendations.recommend_plan_adjustments(merged)
        stability_df = stability_analyzer.calculate_cv(merged)
        abc_df = abc_analyzer.perform_abc_analysis(merged)

        report_saver.save_report(merged, day_summary, cat_summary, status_summary, rec_df, stability_df, abc_df)
        chart_builder.create_charts(day_summary, cat_summary, status_summary, stability_df, abc_df)

        with io.StringIO() as buf, redirect_stdout(buf):
            recommendations.print_recommendations(merged, day_summary, cat_summary)
            stability_analyzer.print_stability_summary(stability_df)
            abc_analyzer.print_abc_summary(abc_df)
            text_output = buf.getvalue()

        await query.message.reply_text(text_output)

        charts = [
            "chart_plan_by_day.png",
            "chart_revenue_by_category.png",
            "chart_status_distribution.png",
            "chart_stability.png",
            "chart_abc_distribution.png"
        ]
        for chart in charts:
            if os.path.exists(chart):
                with open(chart, "rb") as f:
                    await query.message.reply_photo(f)
                os.remove(chart)

        with open("report.xlsx", "rb") as f:
            await query.message.reply_document(f)

        os.remove(sales_path)
        os.remove(menu_path)
        if os.path.exists("report.xlsx"):
            os.remove("report.xlsx")

        await query.message.reply_text("Готово! Чтобы начать заново, введите /start")
        return ConversationHandler.END

    except Exception as e:
        await query.message.reply_text(f"Произошла ошибка при расчёте:\n{str(e)}")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменён. Для начала введите /start")
    return ConversationHandler.END

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Программа остановлена, данные сброшены. Чтобы начать заново, введите /start")
    return ConversationHandler.END

def main() -> None:
    TOKEN = "8441656746:AAFnpinvijAfsIVXK3Bjxy1cLTsf6qiVwFU"

    application = Application.builder().token(TOKEN).build()

    unknown_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAIT_SALES: [
                MessageHandler(filters.Document.ALL, handle_sales_file),
                unknown_handler,
            ],
            WAIT_MENU: [
                MessageHandler(filters.Document.ALL, handle_menu_file),
                unknown_handler,
            ],
            CALCULATE: [
                CallbackQueryHandler(calculate, pattern="^calculate$"),
                unknown_handler,
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("stop", stop),
        ],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()