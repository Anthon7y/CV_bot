import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.content import get_all_rune_names, get_rune_info
from services.db import increment_rune_stat
from keyboards.inline import get_runes_keyboard
from keyboards.main_menu import get_main_menu_keyboard
from middlewares.rate_limit import is_rate_limited

logger = logging.getLogger(__name__)


async def runes_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает клавиатуру с рунами."""
    user = update.effective_user
    if is_rate_limited(user.id):
        await update.message.reply_text("Слишком много запросов. Подождите секунду.")
        return

    rune_names = get_all_rune_names()

    if not rune_names:
        await update.message.reply_text(
            "Значения рун\n\n"
            "Раздел скоро будет доступен. Следите за обновлениями!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        "Значения рун\n\nВыбери руну, чтобы узнать её значение:",
        reply_markup=get_runes_keyboard(rune_names),
        parse_mode="Markdown"
    )


async def rune_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет информацию по выбранной руне."""
    query = update.callback_query
    user = query.from_user

    if is_rate_limited(user.id):
        await query.answer("Слишком много запросов.", show_alert=False)
        return

    await query.answer()

    rune_name = query.data.replace("rune_", "", 1)

    # Считаем статистику
    increment_rune_stat(rune_name)

    # Получаем информацию о руне
    info = get_rune_info(rune_name)

    if not info:
        await query.message.reply_text(
            f"*{rune_name}*\n\n"
            f"Описание руны пока недоступно.",
            parse_mode="Markdown"
        )
        return

    text = f"*{rune_name}*\n\n"
    
    if info.get("value"):
        text += f"{info['value']}\n\n"
    
    if info.get("value_pp"):
        text += f"{info['value_pp']}"

    await query.message.reply_text(text, parse_mode="Markdown")
