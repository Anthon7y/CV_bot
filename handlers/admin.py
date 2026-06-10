import logging
import os
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from services.db import get_stats
from services.broadcast import broadcast_message
from services.content import load_practicums, save_practicums, format_admin_text
from config import load_admins, set_bot_name, PRACTICUMS_FILE, ABOUT_US_FILE, ABOUT_US_ROOT

logger = logging.getLogger(__name__)

# Состояния ConversationHandler
WAITING_BROADCAST = 1
WAITING_NEW_NAME = 2
WAITING_PRACTICUMS = 3
WAITING_ONAS_TEXT = 4


def admin_only(func):
    """Декоратор: пропускает только администраторов."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        admins = load_admins()
        if user_id not in admins:
            await update.message.reply_text("У вас нет доступа к этой команде.")
            return ConversationHandler.END
        return await func(update, context)
    return wrapper


@admin_only
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stats — статистика пользователей."""
    stats = get_stats()
    await update.message.reply_text(
        f"Статистика\n\n"
        f"Всего пользователей: {stats['total']}\n"
        f"Подписаны на рассылку: {stats['subscribed']}\n"
        f"Отписаны: {stats['unsubscribed']}\n"
        f"Активны сегодня (предсказание): {stats['active_today']}",
        parse_mode="Markdown"
    )


# --- /broadcast - рассылка ВСЕМ пользователям ---

@admin_only
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/broadcast — начало рассылки."""
    from services.db import get_subscribed_users
    total = len(get_subscribed_users())
    await update.message.reply_text(
        f"Режим рассылки\n\n"
        f"Сообщение будет отправлено *всем {total} подписанным пользователям* бота.\n\n"
        f"Отправьте сообщение (текст, фото, видео, документ).\n"
        f"Для отмены введите /cancel",
        parse_mode="Markdown"
    )
    return WAITING_BROADCAST


async def broadcast_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает сообщение и запускает рассылку."""
    user_id = update.effective_user.id
    admins = load_admins()
    if user_id not in admins:
        return ConversationHandler.END

    # Сохраняем сообщение для возможности удаления
    context.user_data["last_broadcast_msg"] = update.message.message_id

    status_msg = await update.message.reply_text("Рассылка запущена...")

    # Отправляем только подписанным пользователям
    success, failed = await broadcast_message(context.bot, update.message)

    # Сохраняем рассылку в БД
    from services.db import save_broadcast
    text = update.message.text or update.message.caption or ""
    save_broadcast(message_text=text)

    try:
        await status_msg.edit_text(
            f"Рассылка завершена!\n\n"
            f"Отправлено: {success}\n"
            f"Ошибок: {failed}"
        )
    except:
        pass
    
    # ВАЖНО: явно завершаем conversation
    return ConversationHandler.END


async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Рассылка отменена. Напишите /start для возврата в меню.")
    return ConversationHandler.END


# --- /setname ---

@admin_only
async def setname_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/setname — смена названия бота."""
    current = get_bot_name()
    await update.message.reply_text(
        f"Текущее название: *{current}*\n\n"
        f"Отправьте новое название бота.\n"
        f"Для отмены введите /cancel",
        parse_mode="Markdown"
    )
    return WAITING_NEW_NAME


async def setname_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    if user_id not in admins:
        return ConversationHandler.END

    new_name = update.message.text.strip()
    if not new_name:
        await update.message.reply_text("Название не может быть пустым. Попробуйте ещё раз или /cancel")
        return WAITING_NEW_NAME

    set_bot_name(new_name)
    await update.message.reply_text(
        f"Название бота обновлено: *{new_name}*\n\n"
        f"Изменение вступило в силу немедленно.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def setname_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Смена названия отменена.")
    return ConversationHandler.END


# --- /prac - управление практикумами ---

@admin_only
async def practicum_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/prac — редактирование практикумов."""
    current = load_practicums()
    
    if current:
        text = f"Текущие практикумы:\n\n{current}\n\n"
    else:
        text = "Практикумы пока не добавлены.\n\n"
    
    text += "Отправьте новый текст практикумов.\n"
    text += "Для отмены введите /cancel"
    
    await update.message.reply_text(text, parse_mode="Markdown")
    return WAITING_PRACTICUMS


async def practicum_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    if user_id not in admins:
        return ConversationHandler.END

    new_text = update.message.text.strip()
    if not new_text:
        await update.message.reply_text("Текст не может быть пустым. Попробуйте ещё раз или /cancel")
        return WAITING_PRACTICUMS

    save_practicums(new_text)
    await update.message.reply_text(
        "Практикумы обновлены!\n\n"
        "Изменение вступило в силу немедленно.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def practicum_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Редактирование практикумов отменено.")
    return ConversationHandler.END


# ConversationHandler для /prac (алиас для /practicums)
prac_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("prac", practicum_start),
        CommandHandler("practicums", practicum_start)
    ],
    states={
        WAITING_PRACTICUMS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, practicum_receive)
        ],
    },
    fallbacks=[CommandHandler("cancel", practicum_cancel)],
    per_user=True,
)


# Старый handler для совместимости
practicum_conv_handler = prac_conv_handler


# ConversationHandler для /broadcast
broadcast_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("broadcast", broadcast_start)],
    states={
        WAITING_BROADCAST: [
            MessageHandler(
                (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND,
                broadcast_receive
            )
        ],
    },
    fallbacks=[CommandHandler("cancel", broadcast_cancel)],
    per_user=True,
    per_chat=True,
    conversation_timeout=60,  # 1 минута таймаут
)

# ConversationHandler для /setname
setname_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("setname", setname_start)],
    states={
        WAITING_NEW_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, setname_receive)
        ],
    },
    fallbacks=[CommandHandler("cancel", setname_cancel)],
    per_user=True,
)

# --- /onas - управление разделом "О нас" ---

@admin_only
async def onas_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/onas — редактирование раздела "О нас".""" 
    from config import ABOUT_US_ROOT, ABOUT_US_FILE
    # Читаем весь файл целиком
    try:
        with open(ABOUT_US_ROOT, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > 1:
            current = "".join(lines[1:]).strip()
        else:
            current = ""
    except FileNotFoundError:
        current = ""
    
    text = "Отправьте новый текст для раздела 'О нас'.\n"
    text += "Этот текст будет отображаться в разделе 'О нас' без заголовка.\n"
    text += "Для отмены введите /cancel"
    
    if current:
        text += f"\n\nТекущий текст:\n{current}"
    
    await update.message.reply_text(text, parse_mode="Markdown")
    return WAITING_ONAS_TEXT


async def onas_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    if user_id not in admins:
        return ConversationHandler.END

    new_text = update.message.text.strip()
    if not new_text:
        await update.message.reply_text("Текст не может быть пустым. Попробуйте ещё раз или /cancel")
        return WAITING_ONAS_TEXT

    try:
        # Записываем весь текст в корневой файл (ABOUT_US_ROOT)
        with open(ABOUT_US_ROOT, "w", encoding="utf-8") as f:
            f.write(new_text + "\n")
        
        await update.message.reply_text(
            "Раздел 'О нас' обновлен!\n\n"
            "Изменение вступило в силу немедленно.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении 'О нас': {e}")
        await update.message.reply_text("Ошибка при сохранении. Попробуйте ещё раз.")
    
    return ConversationHandler.END


async def onas_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Редактирование 'О нас' отменено.")
    return ConversationHandler.END


# ConversationHandler для /onas
onas_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("onas", onas_start)],
    states={
        WAITING_ONAS_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, onas_receive)
        ],
    },
    fallbacks=[CommandHandler("cancel", onas_cancel)],
    per_user=True,
)


# ConversationHandler для /practicums
practicum_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("practicums", practicum_start)],
    states={
        WAITING_PRACTICUMS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, practicum_receive)
        ],
    },
    fallbacks=[CommandHandler("cancel", practicum_cancel)],
    per_user=True,
)
