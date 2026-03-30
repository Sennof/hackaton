import os
import io
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

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

# Импортируем наши модули
import data_loader
import data_processor
import aggregations
import recommendations
import report_saver
import chart_builder
import stability_analyzer
import abc_analyzer

# Состояния разговора
WAIT_SALES, WAIT_MENU, CALCULATE = range(3)

# Хранилище путей к загруженным файлам в user_data
USER_DATA_SALES = "sales_path"
USER_DATA_MENU = "menu_path"

def validate_filename(filename: str, expected_name: str) -> bool:
    """Проверяет, что имя файла соответствует expected_name и имеет расширение .csv"""
    return filename.lower() == f"{expected_name.lower()}.csv"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start — начало диалога"""
    # Сбрасываем данные пользователя
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! Я помогу вам проанализировать продажи кафе.\n"
        "Пожалуйста, отправьте файл с фактическими продажами (sales_fact.csv)."
    )
    return WAIT_SALES

async def handle_sales_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка файла sales_fact.csv"""
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

    # Скачиваем файл во временную директорию
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
    """Обработка файла menu_plan.csv"""
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

    # Скачиваем файл
    file = await document.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        await file.download_to_drive(tmp.name)
        context.user_data[USER_DATA_MENU] = tmp.name

    # Показываем кнопку "Рассчитать"
    keyboard = [[InlineKeyboardButton("Рассчитать", callback_data="calculate")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Всё готово! Нажмите кнопку, чтобы начать расчёт.",
        reply_markup=reply_markup
    )
    return CALCULATE

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запуск расчётов после нажатия кнопки"""
    query = update.callback_query
    await query.answer()

    # Получаем пути к загруженным файлам
    sales_path = context.user_data.get(USER_DATA_SALES)
    menu_path = context.user_data.get(USER_DATA_MENU)
    if not sales_path or not menu_path:
        await query.edit_message_text("Ошибка: файлы не найдены. Начните заново с /start")
        return ConversationHandler.END

    # Отправляем сообщение о начале расчёта
    await query.edit_message_text("Выполняю расчёт... Это может занять несколько секунд.")

    try:
        # Загружаем данные
        menu_plan = pd.read_csv(menu_path)
        sales_fact = pd.read_csv(sales_path)

        # Основные вычисления
        merged = data_processor.merge_and_calc(menu_plan, sales_fact)
        day_summary, cat_summary, status_summary = aggregations.create_summaries(merged)
        rec_df = recommendations.recommend_plan_adjustments(merged)
        stability_df = stability_analyzer.calculate_cv(merged)
        abc_df = abc_analyzer.perform_abc_analysis(merged)

        # Сохраняем отчёт Excel
        report_saver.save_report(merged, day_summary, cat_summary, status_summary, rec_df, stability_df, abc_df)

        # Сохраняем графики
        chart_builder.create_charts(day_summary, cat_summary, status_summary, stability_df, abc_df)

        # Собираем текстовый вывод, перенаправляя stdout
        with io.StringIO() as buf, redirect_stdout(buf):
            recommendations.print_recommendations(merged, day_summary, cat_summary)
            stability_analyzer.print_stability_summary(stability_df)
            abc_analyzer.print_abc_summary(abc_df)
            text_output = buf.getvalue()

        # Отправляем текст пользователю
        await query.message.reply_text(text_output)

        # Отправляем графики
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
                os.remove(chart)  # удаляем после отправки

        # Отправляем Excel-отчёт
        with open("report.xlsx", "rb") as f:
            await query.message.reply_document(f)

        # Удаляем временные файлы
        os.remove(sales_path)
        os.remove(menu_path)
        if os.path.exists("report.xlsx"):
            os.remove("report.xlsx")

        # Завершаем разговор
        await query.message.reply_text("Готово! Чтобы начать заново, введите /start")
        return ConversationHandler.END

    except Exception as e:
        await query.message.reply_text(f"Произошла ошибка при расчёте:\n{str(e)}")
        # Возвращаем в начальное состояние
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога (на всякий случай)"""
    await update.message.reply_text("Диалог отменён. Для начала введите /start")
    return ConversationHandler.END

def main() -> None:
    """Запуск бота"""
    # Вставьте ваш токен
    TOKEN = "8441656746:AAFnpinvijAfsIVXK3Bjxy1cLTsf6qiVwFU"

    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAIT_SALES: [MessageHandler(filters.Document.ALL, handle_sales_file)],
            WAIT_MENU: [MessageHandler(filters.Document.ALL, handle_menu_file)],
            CALCULATE: [CallbackQueryHandler(calculate, pattern="^calculate$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Не реагируем на другие сообщения
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()