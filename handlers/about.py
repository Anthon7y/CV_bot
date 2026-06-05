import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import get_about_text, get_bot_name
from services.content import load_practicums
from keyboards.main_menu import get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_about_text()
    bot_name = get_bot_name()

    if not text:
        text = "Информация о нас пока не добавлена."

    await update.message.reply_text(
        f"ℹ️ *{bot_name}*\n\n{text}",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


async def practicum_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает практикумы."""
    practicum_text = load_practicums()
    bot_name = get_bot_name()

    if practicum_text:
        await update.message.reply_text(
            f"🎓 *Наши практикумы*\n\n{practicum_text}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🎓 *Наши практикумы*\n\n"
            "Практикумы пока не добавлены. Следите за обновлениями! 🌿",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
