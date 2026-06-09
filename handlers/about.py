import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from config import get_about_text, get_bot_name, DATA_DIR
from services.content import load_practicums, PRAC_IMAGE_PATH
from keyboards.main_menu import get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_about_text()

    if not text:
        text = "Информация о нас пока не добавлена."

    await update.message.reply_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


async def practicum_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает практикумы."""
    practicum_text = load_practicums()

    if practicum_text:
        # Отправляем текст практикума с фото PRAC.jpg
        if os.path.exists(PRAC_IMAGE_PATH):
            with open(PRAC_IMAGE_PATH, "rb") as img:
                await update.message.reply_photo(
                    photo=img,
                    caption=practicum_text
                )
        else:
            await update.message.reply_text(
                practicum_text
            )
    else:
        await update.message.reply_text(
            "Практикумы пока не добавлены. Следите за обновлениями!"
        )
