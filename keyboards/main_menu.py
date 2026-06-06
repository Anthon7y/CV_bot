from telegram import ReplyKeyboardMarkup, KeyboardButton
from config import get_bot_name


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню с динамическим названием бота."""
    bot_name = get_bot_name()
    keyboard = [
        [KeyboardButton("Предсказание на день")],
        [KeyboardButton("Значения рун"), KeyboardButton("Наши практикумы")],
        [KeyboardButton("О нас"), KeyboardButton("Рассылка")],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder=f"Главное меню | {bot_name}"
    )
