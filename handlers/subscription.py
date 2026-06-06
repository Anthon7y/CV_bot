import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.db import get_broadcasts
from config import load_admins
from keyboards.main_menu import get_main_menu_keyboard
from middlewares.rate_limit import is_rate_limited

logger = logging.getLogger(__name__)


async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает архив рассылок (без возможности отписки)."""
    user = update.effective_user
    if is_rate_limited(user.id):
        await update.message.reply_text("Слишком много запросов. Подождите секунду.")
        return

    # Проверяем, админ ли пользователь
    admins = load_admins()
    is_admin = user.id in admins

    broadcasts = get_broadcasts(limit=5)

    if not broadcasts:
        text = "Архив рассылок\n\n"
        if is_admin:
            text += "Пока нет отправленных рассылок.\n"
            text += "Используйте команду /broadcast для отправки новой рассылки."
        else:
            text += "Пока нет отправленных рассылок. Следите за обновлениями!"

        await update.message.reply_text(
            text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    text = "Архив рассылок\n\n"
    for b in broadcasts:
        sent_at = b["sent_at"]
        text += f"{sent_at}\n"
        if b["message_text"]:
            text += f"{b['message_text'][:100]}...\n"
        text += "\n"

    if is_admin:
        text += "Используйте команду /broadcast для отправки новой рассылки.\n"
    text += "\nРассылка активна — отписаться невозможно."

    await update.message.reply_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


async def subscription_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие кнопок подписки/отписки — теперь только заглушка."""
    query = update.callback_query
    user = query.from_user

    if is_rate_limited(user.id):
        await query.answer("Слишком много запросов.", show_alert=False)
        return

    await query.answer()

    # Отписка невозможна
    await query.edit_message_text(
        "Рассылка активна — отписаться невозможно.",
        parse_mode="Markdown"
    )
