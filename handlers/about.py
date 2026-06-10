import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from config import get_about_text, get_bot_name, DATA_DIR, RUNES_FOLDER_DIR
from services.content import load_practicums, PRAC_IMAGE_PATH
from keyboards.main_menu import get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from services.content import format_admin_text
    text = get_about_text()

    if not text:
        text = "Информация о нас пока не добавлена."

    # Применяем форматирование
    formatted_text = format_admin_text(text)

    await update.message.reply_text(
        formatted_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )


async def practicum_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает практикумы."""
    from services.content import load_practicums, PRAC_IMAGE_PATH, format_admin_text
    practicum_text = load_practicums()

    if practicum_text:
        # Применяем форматирование
        formatted_text = format_admin_text(practicum_text)
        
        # Отправляем текст практикума с фото PRAC.jpg
        if os.path.exists(PRAC_IMAGE_PATH):
            with open(PRAC_IMAGE_PATH, "rb") as img:
                await update.message.reply_photo(
                    photo=img,
                    caption=formatted_text,
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                formatted_text,
                parse_mode="HTML"
            )
    else:
        await update.message.reply_text(
            "Практикумы пока не добавлены. Следите за обновлениями!"
        )
