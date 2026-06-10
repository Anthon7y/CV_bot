import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from services.db import get_broadcasts, toggle_subscription, is_user_subscribed
from services.content import format_admin_text
from config import load_admins, DATA_DIR
from keyboards.main_menu import get_main_menu_keyboard
from middlewares.rate_limit import is_rate_limited

logger = logging.getLogger(__name__)

# Путь к картинкам
UNSUB_IMAGE_PATH = os.path.join(DATA_DIR, "images", "UNSUB.jpg")
SUB_IMAGE_PATH = os.path.join(DATA_DIR, "images", "SUB.jpg")

# Состояние ожидания подписки
WAITING_SUB_CONFIRMATION = 1


async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает состояние подписки."""
    user = update.effective_user
    if is_rate_limited(user.id):
        await update.message.reply_text("Слишком много запросов. Подождите секунду.")
        return

    # Проверяем, админ ли пользователь
    admins = load_admins()
    is_admin = user.id in admins

    # Проверяем статус подписки
    subscribed = is_user_subscribed(user.id)

    if subscribed:
        # Пользователь подписан - показываем кнопку отписки
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = [[InlineKeyboardButton("Отписаться", callback_data="unsub")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            format_admin_text("*Рассылка активна!* _Чтобы отписаться_, нажмите кнопку ниже."),
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        # Пользователь отписан - предлагаем подписаться
        await update.message.reply_text(
            format_admin_text("_Рассылка отключена._\n\nЧтобы подписаться на рассылку, используйте команду /follow"),
            parse_mode="HTML"
        )


async def follow_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /follow для подписки на рассылку."""
    user = update.effective_user
    
    if is_user_subscribed(user.id):
        await update.message.reply_text(
            format_admin_text("*Вы уже подписаны* на рассылку!"),
            parse_mode="HTML"
        )
        return
    
    # Подписываем пользователя
    toggle_subscription(user.id, True)
    
    await update.message.reply_text(
        format_admin_text("_Рассылка активна!_ Чтобы отписаться напишите /unfollow"),
        parse_mode="HTML"
    )


async def subscription_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие кнопки отписки."""
    query = update.callback_query
    user = query.from_user

    if is_rate_limited(user.id):
        await query.answer("Слишком много запросов.", show_alert=False)
        return

    await query.answer()

    # Пользователь нажал кнопку отписки
    subscribed = is_user_subscribed(user.id)
    
    if subscribed:
        # Показываем картинку с вопросом
        if os.path.exists(UNSUB_IMAGE_PATH):
            with open(UNSUB_IMAGE_PATH, "rb") as img:
                await query.message.reply_photo(
                    photo=img,
                    caption=format_admin_text("*Вы уверены?* /yes /no"),
                    parse_mode="HTML"
                )
        else:
            await query.message.reply_text(
                format_admin_text("*Вы уверены?* /yes /no"),
                parse_mode="HTML"
            )
        
        # Удаляем сообщение с кнопкой
        await query.message.delete()
        # Сохраняем состояние
        context.user_data["awaiting_unsub_confirmation"] = True
    else:
        await query.edit_message_text(
            format_admin_text("_Рассылка отключена._\n\nЧтобы подписаться, используйте команду /follow"),
            parse_mode="HTML"
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
                    caption=format_admin_text("*Вы уверены?* /yes /no"),
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                format_admin_text("*Вы уверены?* /yes /no"),
                parse_mode="HTML"
            )
        
        # Сохраняем состояние
        context.user_data["awaiting_unsub_confirmation"] = True
    else:
        await update.message.reply_text(
            format_admin_text("_Вы не подписаны_ на рассылку."),
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
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
                format_admin_text("*Вы отписаны* от рассылки."),
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
            )
        elif command == "/no":
            context.user_data["awaiting_unsub_confirmation"] = False
            await update.message.reply_text(
                format_admin_text("_Рассылка активна!_"),
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
            )
    else:
        # Если пользователь ввел /yes или /no не в контексте отписки
        await update.message.reply_text(
            format_admin_text("Используйте команду /unfollow для отписки от рассылки."),
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
