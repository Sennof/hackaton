import os
import io
import tempfile
import threading
import pandas as pd
from contextlib import redirect_stdout
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram.constants import ParseMode
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

import data_loader
import data_processor
import aggregations
import recommendations
import report_saver
import chart_builder
import stability_analyzer
import abc_analyzer

def start_health_server():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
            else:
                self.send_response(404)
                self.end_headers()

    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()

WAIT_SALES, WAIT_MENU, CALCULATE = range(3)

USER_DATA_SALES = "sales_path"
USER_DATA_MENU = "menu_path"

def validate_filename(filename: str, expected_name: str) -> bool:
    return filename.lower() == f"{expected_name.lower()}.csv"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "👋<b>Привет! Я помогу вам проанализировать продажи кафе.</b>👋\n"
        "Пожалуйста, отправьте файл с фактическими продажами (sales_fact.csv).",
        parse_mode=ParseMode.HTML,
    )
    return WAIT_SALES

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "😔<i>Сообщение не распознано</i>😔",
        parse_mode=ParseMode.HTML
    )

async def handle_sales_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    if not document:
        await update.message.reply_text(
            "👇Пожалуйста, отправьте <i>файл.</i>👇",
            parse_mode=ParseMode.HTML
        )
        return WAIT_SALES

    filename = document.file_name
    if not validate_filename(filename, "sales_fact"):
        await update.message.reply_text(
            "😔<b>Неверный файл.</b>😔\nНужен файл с именем <i>sales_fact.csv.</i>\n"
            "Попробуйте ещё раз.",
            parse_mode=ParseMode.HTML
        )
        return WAIT_SALES

    file = await document.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        await file.download_to_drive(tmp.name)
        context.user_data[USER_DATA_SALES] = tmp.name

    await update.message.reply_text(
        "🔥<b>Файл sales_fact.csv принят.</b>🔥\n"
        "Теперь отправьте файл с планом <i>(menu_plan.csv)</i>.",
        parse_mode=ParseMode.HTML
    )
    return WAIT_MENU

async def handle_menu_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    if not document:
        await update.message.reply_text(
            "📄Пожалуйста, отправьте <i>файл.</i>📄",
            parse_mode=ParseMode.HTML
        )
        return WAIT_MENU

    filename = document.file_name
    if not validate_filename(filename, "menu_plan"):
        await update.message.reply_text(
            "😔<b>Неверный файл.</b>😔"
            "\nНужен файл с именем <i>menu_plan.csv.</i>"
            "\nПопробуйте ещё раз.",
            parse_mode=ParseMode.HTML
        )
        return WAIT_MENU

    file = await document.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        await file.download_to_drive(tmp.name)
        context.user_data[USER_DATA_MENU] = tmp.name

    keyboard = [[InlineKeyboardButton("Рассчитать!", callback_data="calculate")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔥<b>Всё готово!</b>🔥"
        "\n<i>Нажмите кнопку,</i> чтобы начать расчёт.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )
    return CALCULATE

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    sales_path = context.user_data.get(USER_DATA_SALES)
    menu_path = context.user_data.get(USER_DATA_MENU)
    if not sales_path or not menu_path:
        await query.edit_message_text(
            "😔<b>Ошибка: файлы не найдены.</b>😔"
            "\nНачните заново с <i>/start</i>",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "😉<i>Выполняю расчёт...😉"
        "\nЭто может занять несколько секунд.</i>",
        parse_mode=ParseMode.HTML
    )

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

        await query.message.reply_text(
            text_output,
            parse_mode="HTML"
        )

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

        await query.message.reply_text(
            "🔥<b>Готово!</b>🔥"
            "\nЧтобы начать заново, введите <i>/start</i>",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    except Exception as e:
        await query.message.reply_text(
            f"😔<b>Произошла ошибка при расчёте:</b>😔"
            f"\n{str(e)}",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "👋<b>Программа остановлена.</b>👋"
        "\nДанные сброшены. Чтобы начать заново, введите <i>/start</i>",
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

def main() -> None:
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена.")
        return

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
            CommandHandler("stop", stop),
        ],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()