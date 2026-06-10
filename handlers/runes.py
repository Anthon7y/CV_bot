import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from services.content import get_all_rune_names, get_rune_info, get_rune_image
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
    """Отправляет только картинку руны без текста."""
    query = update.callback_query
    user = query.from_user

    if is_rate_limited(user.id):
        await query.answer("Слишком много запросов.", show_alert=False)
        return

    await query.answer()

    rune_name = query.data.replace("rune_", "", 1)

    # Считаем статистику
    increment_rune_stat(rune_name)

    # Получаем картинку руны
    image_path = get_rune_image(rune_name)

    # Отправляем только картинку
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img:
                await query.message.reply_photo(photo=img)
            # Удаляем сообщение с выбором руны
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Не удалось отправить картинку {image_path}: {e}")
    else:
        # Если картинки нет - ничего не отправляем
        pass
