import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from services.db import get_broadcasts, toggle_subscription, is_user_subscribed
from config import load_admins, DATA_DIR
from keyboards.main_menu import get_main_menu_keyboard
from middlewares.rate_limit import is_rate_limited

logger = logging.getLogger(__name__)

# Путь к картинкам
UNSUB_IMAGE_PATH = os.path.join(DATA_DIR, "images", "UNSUB.jpg")
SUB_IMAGE_PATH = os.path.join(DATA_DIR, "images", "SUB.jpg")

# Состояние ожидания подтверждения отписки
WAITING_UNSUB_CONFIRMATION = 1


async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает архив рассылок и кнопки подписки/отписки."""
    user = update.effective_user
    if is_rate_limited(user.id):
        await update.message.reply_text("Слишком много запросов. Подождите секунду.")
        return

    # Проверяем, админ ли пользователь
    admins = load_admins()
    is_admin = user.id in admins

    # Проверяем статус подписки
    subscribed = is_user_subscribed(user.id)

    broadcasts = get_broadcasts(limit=5)

    if not broadcasts:
        text = "Архив рассылок\n\n"
        if is_admin:
            text += "Пока нет отправленных рассылок.\n"
            text += "Используйте команду /broadcast для отправки новой рассылки."
        else:
            text += "Пока нет отправленных рассылок. Следите за обновлениями!"

        if subscribed:
            text += "\n\nРассылка активна! Чтобы отписаться напишите /unfollow"
        
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
    
    if subscribed:
        text += "\nРассылка активна! Чтобы отписаться напишите /unfollow"
    else:
        text += "\nРассылка отключена. Чтобы подписаться, используйте кнопку ниже."

    await update.message.reply_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


async def subscription_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие кнопок подписки/отписки."""
    query = update.callback_query
    user = query.from_user

    if is_rate_limited(user.id):
        await query.answer("Слишком много запросов.", show_alert=False)
        return

    await query.answer()

    # Получаем текущий статус подписки
    subscribed = is_user_subscribed(user.id)
    
    if subscribed:
        # Пользователь подписан - показываем кнопку отписки
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = [[InlineKeyboardButton("Отписаться", callback_data="unsub")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Рассылка активна! Чтобы отписаться, нажмите кнопку ниже.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        # Пользователь отписан - показываем кнопку подписки
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = [[InlineKeyboardButton("Подписаться", callback_data="sub")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Рассылка отключена. Чтобы подписаться, нажмите кнопку ниже.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )


async def unfollow_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /unfollow - запрос подтверждения отписки."""
    user = update.effective_user
    
    if is_user_subscribed(user.id):
        # Пользователь подписан - показываем картинку с вопросом
        if os.path.exists(UNSUB_IMAGE_PATH):
            with open(UNSUB_IMAGE_PATH, "rb") as img:
                await update.message.reply_photo(
                    photo=img,
                    caption="Вы уверены? /yes /no"
                )
        else:
            await update.message.reply_text("Вы уверены? /yes /no")
        
        # Сохраняем состояние
        context.user_data["awaiting_unsub_confirmation"] = True
    else:
        await update.message.reply_text(
            "Вы не подписаны на рассылку.",
            reply_markup=get_main_menu_keyboard()
        )


async def handle_yes_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ на подтверждение отписки (/yes или /no)."""
    user = update.effective_user
    
    if context.user_data.get("awaiting_unsub_confirmation"):
        command = update.message.text.strip().lower()
        
        if command == "/yes":
            toggle_subscription(user.id, False)
            context.user_data["awaiting_unsub_confirmation"] = False
            await update.message.reply_text(
                "Вы отписаны от рассылки.",
                reply_markup=get_main_menu_keyboard()
            )
        elif command == "/no":
            context.user_data["awaiting_unsub_confirmation"] = False
            await update.message.reply_text(
                "Рассылка активна!",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        # Если пользователь ввел /yes или /no не в контексте отписки
        await update.message.reply_text(
            "Используйте команду /unfollow для отписки от рассылки.",
            reply_markup=get_main_menu_keyboard()
        )
