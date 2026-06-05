import time
import logging
from collections import defaultdict
from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

# Максимум запросов в секунду на пользователя
RATE_LIMIT = 5
_user_timestamps: dict[int, list[float]] = defaultdict(list)


def is_rate_limited(user_id: int) -> bool:
    """Возвращает True если пользователь превысил лимит запросов."""
    now = time.monotonic()
    window = 1.0  # секунда
    timestamps = _user_timestamps[user_id]

    # Убираем старые метки
    _user_timestamps[user_id] = [t for t in timestamps if now - t < window]

    if len(_user_timestamps[user_id]) >= RATE_LIMIT:
        return True

    _user_timestamps[user_id].append(now)
    return False


async def rate_limit_middleware(update: Update, context: CallbackContext, next_handler):
    """Middleware для ограничения частоты запросов."""
    user = update.effective_user
    if user and is_rate_limited(user.id):
        if update.callback_query:
            await update.callback_query.answer("Слишком много запросов. Подождите секунду.", show_alert=False)
        return
    return await next_handler(update, context)
