import os
import threading
import logging
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

logger = logging.getLogger(__name__)

# Путь к корню проекта
ROOT_DIR = os.path.dirname(__file__)

# Путь к папке с данными
DATA_DIR = os.path.join(ROOT_DIR, "data")

ABOUT_US_FILE = os.path.join(DATA_DIR, "about_us.txt")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.txt")
DB_FILE = os.path.join(DATA_DIR, "bot.db")
DAILY_TEXTS_FILE = os.path.join(DATA_DIR, "texts", "daily.txt")
DAILY_IMAGES_DIR = os.path.join(DATA_DIR, "images", "daily")
RUNES_IMAGES_DIR = os.path.join(ROOT_DIR, "Руны для бота")
RUNES_VALUES_FILE = os.path.join(DATA_DIR, "texts", "runes_values.txt")
PRACTICUMS_FILE = os.path.join(DATA_DIR, "practicums.txt")

# Папка с картинками рун
RUNES_FOLDER_DIR = os.path.join(ROOT_DIR, "Руны для бота")

# Файлы в корне проекта
ABOUT_US_ROOT = os.path.join(ROOT_DIR, "about_us.txt")
RUNES_VALUES_ROOT = os.path.join(ROOT_DIR, "Значения рун.txt")
ADVICES_FILE = os.path.join(ROOT_DIR, "Советы.txt")

# Папки с картами для предсказаний
STEAMPUNK_DIR = os.path.join(ROOT_DIR, "STEAMPUNK")
STEAMPUNK2_DIR = os.path.join(ROOT_DIR, "STEAMPUNK2")
STEAMPUNK_MAIN_DIR = os.path.join(ROOT_DIR, "STEAMPUNK_MAIN")

# Ссылка на покупку колоды (замените на реальную)
SHOP_LINK = os.getenv("SHOP_LINK", "")

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Глобальное название бота и блокировка файла
_bot_name_lock = threading.Lock()
BOT_NAME = "таро и руны"


def load_bot_name() -> str:
    """Читает первую строку about_us.txt и возвращает название бота."""
    global BOT_NAME
    with _bot_name_lock:
        try:
            with open(ABOUT_US_FILE, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            if not first_line:
                logger.critical("about_us.txt пуст или первая строка пустая. Бот не может запуститься.")
                raise ValueError("about_us.txt: первая строка пустая")
            BOT_NAME = first_line
            return BOT_NAME
        except FileNotFoundError:
            logger.critical(f"Файл {ABOUT_US_FILE} не найден.")
            raise


def get_bot_name() -> str:
    """Возвращает текущее название бота (потокобезопасно)."""
    with _bot_name_lock:
        return BOT_NAME


def set_bot_name(new_name: str) -> None:
    """Обновляет название бота в памяти и в файле about_us.txt."""
    global BOT_NAME
    with _bot_name_lock:
        try:
            with open(ABOUT_US_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []

        if lines:
            lines[0] = new_name + "\n"
        else:
            lines = [new_name + "\n"]

        with open(ABOUT_US_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)

        BOT_NAME = new_name


def load_admins() -> set[int]:
    """Читает admins.txt и возвращает множество ID администраторов."""
    admins = set()
    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    admins.add(int(line))
    except FileNotFoundError:
        logger.warning(f"Файл {ADMINS_FILE} не найден. Нет администраторов.")
    return admins


def get_about_text() -> str:
    """Возвращает текст 'О нас' из корневого файла."""
    try:
        with open(ABOUT_US_ROOT, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return "Информация о нас пока не добавлена."
        return content
    except (FileNotFoundError, UnicodeDecodeError):
        pass
    
    # Fallback на data/about_us.txt
    try:
        with open(ABOUT_US_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > 1:
            return "".join(lines[1:]).strip()
        elif len(lines) == 1:
            return lines[0].strip()
        return "Информация о нас пока не добавлена."
    except FileNotFoundError:
        return "Информация о нас пока не добавлена."


def set_about_text(text: str) -> None:
    """Устанавливает текст 'О нас' в корневом файле."""
    try:
        with open(ABOUT_US_ROOT, "r", encoding="windows-1251") as f:
            lines = f.readlines()
    except FileNotFoundError:
        try:
            with open(ABOUT_US_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []
    
    # Обновляем текст (все строки кроме первой)
    lines = lines[:1] if lines else ["таро и руны\n"]
    
    # Добавляем новый текст
    if text:
        lines.append("\n" + text)
    
    # Записываем в корневой файл
    try:
        with open(ABOUT_US_ROOT, "w", encoding="windows-1251") as f:
            f.writelines(lines)
    except Exception:
        # Если не удалось записать в корневой, пробуем в data
        with open(ABOUT_US_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
