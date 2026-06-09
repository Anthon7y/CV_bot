import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.db import upsert_user
from keyboards.main_menu import get_main_menu_keyboard
from config import get_bot_name

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        last_name=user.last_name or "",
    )

    bot_name = get_bot_name()
    # Новое приветственное сообщение с отступами и жирным
    await update.message.reply_text(
        f"*Привет, {user.first_name}!*\n\n"
        f"*Добро пожаловать к Кибер Вёльве.*\n\n"
        f"Здесь тебя ждут ежедневные предсказания рун, справочник значений и многое другое.\n"
        f"Выбери раздел в меню ниже",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
