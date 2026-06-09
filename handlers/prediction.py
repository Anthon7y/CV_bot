import logging
from datetime import date
from telegram import Update
from telegram.ext import ContextTypes
from services.db import get_last_prediction_date, set_last_prediction_date, upsert_user
from services.content import get_random_steampunk_card
from keyboards.inline import get_sphere_keyboard
from keyboards.main_menu import get_main_menu_keyboard
from middlewares.rate_limit import is_rate_limited

logger = logging.getLogger(__name__)


async def prediction_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает выбор сферы предсказания."""
    user = update.effective_user
    if is_rate_limited(user.id):
        await update.message.reply_text("Слишком много запросов. Подождите секунду.")
        return

    # Убедимся что пользователь есть в БД
    upsert_user(user.id, user.username or "", user.first_name or "", user.last_name or "")

    # Строгая проверка лимита — одно предсказание в день
    last_date = get_last_prediction_date(user.id)
    today = date.today().isoformat()

    if last_date and last_date == today:
        await update.message.reply_text(
            "Ты уже получил своё предсказание сегодня.\n\n"
            "Руны говорят один раз в день — возвращайся завтра!",
            reply_markup=get_main_menu_keyboard()
        )
        return

    await update.message.reply_text(
        "Предсказание на день\n\nВыбери сферу, о которой хочешь узнать:",
        reply_markup=get_sphere_keyboard(),
        parse_mode="Markdown"
    )


async def sphere_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор сферы и выдаёт предсказание."""
    query = update.callback_query
    user = query.from_user

    if is_rate_limited(user.id):
        await query.answer("Слишком много запросов.", show_alert=False)
        return

    await query.answer()

    # Убедимся что пользователь есть в БД
    upsert_user(user.id, user.username or "", user.first_name or "", user.last_name or "")

    # Строгая проверка лимита
    last_date = get_last_prediction_date(user.id)
    today = date.today().isoformat()

    if last_date and last_date == today:
        await query.edit_message_text(
            "Ты уже получил своё предсказание сегодня.\n\nВозвращайся завтра!"
        )
        return

    # Определяем сферу и выбираем колоду
    sphere_map = {
        "sphere_relations": ("Отношения", "relations"),
        "sphere_money": ("Деньги", "money"),
        "sphere_advice": ("Совет", "advice"),
    }
    sphere_label, sphere_type = sphere_map.get(query.data, ("", "general"))

    # Получаем случайную карту
    card = get_random_steampunk_card(sphere_type)

    if not card:
        await query.edit_message_text(
            "Карты пока недоступны. Добавьте изображения в папку STEAMPUNK/"
        )
        return

    # Формируем текст предсказания (подпись — Ваши А&А)
    caption = f"Предсказание на день — {sphere_label}\n\n"
    caption += f"*{card['rune_name']}*\n\n"
    
    if card.get("advice"):
        caption += f"Совет:\n{card['advice']}\n\n"
    
    caption += f"— Ваши А&А"

    # Записываем дату предсказания ДО отправки
    set_last_prediction_date(user.id, date.today())

    # Отправляем карту с текстом
    # Для больших картинок используем reply_photo с предварительной загрузкой
    # или отправляем только текст если картинка не загружается
    
    try:
        with open(card["path"], "rb") as img:
            # Используем reply_photo вместо edit_message_text для новой картинки
            await query.message.reply_photo(
                photo=img,
                caption=caption,
                parse_mode="Markdown"
            )
        # Удаляем сообщение с выбором сферы
        await query.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось отправить картинку {card['path']}: {e}")
        # Если картинка не отправилась, отправляем только текст
        await query.edit_message_text(caption, parse_mode="Markdown")
