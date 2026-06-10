import logging
import logging.handlers
import os
import sys
import threading
import time
import urllib.request

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

import config
from config import BOT_TOKEN, load_bot_name, DATA_DIR
from services.db import init_db
from handlers.start import start_handler
from handlers.prediction import prediction_menu_handler, sphere_callback_handler
from handlers.runes import runes_menu_handler, rune_callback_handler
from handlers.about import about_handler, practicum_handler
from handlers.subscription import subscription_handler, subscription_callback_handler, follow_handler
from handlers.admin import (
    stats_handler, broadcast_conv_handler, setname_conv_handler, practicum_conv_handler,
    onas_conv_handler, onas_start, onas_receive_text, onas_cancel
)
from handlers.subscription import unfollow_handler, handle_yes_no


def setup_logging():
    """Настройка логирования."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def ensure_dirs():
    """Создаёт необходимые папки если их нет."""
    dirs = [
        DATA_DIR,
        os.path.join(DATA_DIR, "texts"),
        os.path.join(DATA_DIR, "images", "daily"),
        os.path.join(DATA_DIR, "runes"),
        os.path.join(DATA_DIR, "future_prac"),
        os.path.join(DATA_DIR, "arc_prac"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    ensure_dirs()

    # Загружаем название бота — критично, без него не стартуем
    try:
        bot_name = load_bot_name()
        logger.info(f"Название бота: {bot_name}")
    except (ValueError, FileNotFoundError) as e:
        logger.critical(f"Не удалось загрузить название бота: {e}")
        sys.exit(1)

    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN не задан. Установите переменную окружения BOT_TOKEN.")
        sys.exit(1)

    # Инициализируем БД
    init_db()

    # Строим приложение
    app = Application.builder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("unfollow", unfollow_handler))
    app.add_handler(CommandHandler("follow", follow_handler))
    app.add_handler(CommandHandler("yes", handle_yes_no))
    app.add_handler(CommandHandler("no", handle_yes_no))

    # ConversationHandlers
    app.add_handler(broadcast_conv_handler)
    app.add_handler(setname_conv_handler)
    app.add_handler(practicum_conv_handler)
    app.add_handler(onas_conv_handler)

    # Reply-кнопки главного меню
    # Reply-кнопки главного меню
    app.add_handler(MessageHandler(filters.Regex("^Предсказание на день$"), prediction_menu_handler))
    app.add_handler(MessageHandler(filters.Regex("^Значения рун$"), runes_menu_handler))
    app.add_handler(MessageHandler(filters.Regex("^Наши практикумы$"), practicum_handler))
    app.add_handler(MessageHandler(filters.Regex("^О нас$"), about_handler))
    app.add_handler(MessageHandler(filters.Regex("^Рассылка$"), subscription_handler))

    # Inline callback'и
    app.add_handler(CallbackQueryHandler(sphere_callback_handler, pattern="^sphere_"))
    app.add_handler(CallbackQueryHandler(rune_callback_handler, pattern="^rune_"))
    app.add_handler(CallbackQueryHandler(subscription_callback_handler, pattern="^(sub|unsub)$"))

    logger.info("Бот запущен. Polling...")
    import asyncio
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    # Render требует открытый порт для web-сервиса
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        def log_message(self, format, *args):
            pass  # подавляем логи HTTP

    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info(f"Health check сервер запущен на порту {port}")

    # Пингуем себя каждые 10 минут чтобы не засыпать на Render Free
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        def keep_alive():
            while True:
                time.sleep(600)
                try:
                    urllib.request.urlopen(render_url, timeout=10)
                except Exception:
                    pass
        threading.Thread(target=keep_alive, daemon=True).start()
        logger.info("Keep-alive пинг запущен")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Небольшая задержка чтобы старый инстанс успел завершиться при рестарте
    import time as _time
    _time.sleep(3)

    app.run_polling(drop_pending_updates=True, allowed_updates=[])


if __name__ == "__main__":
    main()
