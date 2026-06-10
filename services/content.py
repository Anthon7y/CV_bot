import os
import random
import logging
import re
from config import (
    DAILY_TEXTS_FILE, DAILY_IMAGES_DIR, RUNES_IMAGES_DIR,
    RUNES_VALUES_FILE, PRACTICUMS_FILE,
    STEAMPUNK_DIR, STEAMPUNK2_DIR, ADVICES_FILE,
    RUNES_VALUES_ROOT, DATA_DIR, STEAMPUNK_MAIN_DIR
)

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Путь к PRAC.jpg в папке data
PRAC_IMAGE_PATH = os.path.join(DATA_DIR, "images", "prac.jpg")

# --- Предсказания ---

def get_daily_texts() -> list[str]:
    """Читает трактовки из texts/daily.txt."""
    try:
        with open(DAILY_TEXTS_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        return lines
    except FileNotFoundError:
        logger.warning(f"Файл {DAILY_TEXTS_FILE} не найден.")
        return []


def get_random_daily_image() -> str | None:
    """Возвращает путь к случайному изображению из images/daily/."""
    try:
        files = [
            os.path.join(DAILY_IMAGES_DIR, f)
            for f in os.listdir(DAILY_IMAGES_DIR)
            if os.path.splitext(f)[1].lower() in SUPPORTED_IMAGE_EXTS
        ]
        if not files:
            return None
        return random.choice(files)
    except FileNotFoundError:
        return None


def get_random_prediction() -> tuple[str | None, str]:
    """Возвращает (путь к картинке, текст трактовки)."""
    image = get_random_daily_image()
    texts = get_daily_texts()
    text = random.choice(texts) if texts else ""
    return image, text


# --- Карты STEAMPUNK (основные 24 руны старшего футарка) ---

RUNE_NAMES_MAP = {
    1: "Феху",     # FEHU
    2: "Уруз",     # URUZ
    3: "Турисаз",  # THURIAZ
    4: "Ансуз",    # ANSUZ
    5: "Райдо",    # RAIDO
    6: "Кеназ",    # KENAZ
    7: "Гебо",     # GEBO
    8: "Вуньо",    # WUNJO
    9: "Хагалаз",  # HAGALAZ
    10: "Наутиз",  # NAUTHIZ
    11: "Иса",     # ISA
    12: "Йера",    # JERA
    13: "Эйваз",   # EIHWAZ
    14: "Перт",    # PERTH
    15: "Альгиз",  # ALGIZ
    16: "Соуло",   # SOWILO
    17: "Тейваз",  # TIWAZ
    18: "Беркана", # BERKANA
    19: "Эваз",    # EWAZ
    20: "Манназ",  # MANNAZ
    21: "Лагуз",   # LAGUZ
    22: "Ингуз",   # INGUZ
    23: "Одал",    # OTHALA
    24: "Дагаз",   # DAGAZ
}

# Обратный маппинг: имя руны -> номер
RUNE_NAME_TO_NUMBER = {v.lower(): k for k, v in RUNE_NAMES_MAP.items()}

# Маппинг имен из STEAMPUNK_MAIN на стандартные имена рун
STEAMPUNK_MAIN_NAME_MAP = {
    "FEHU": "Феху",
    "URUZ": "Уруз",
    "THURIAZ": "Турисаз",
    "ANSUZ": "Ансуз",
    "RAIDO": "Райдо",
    "KENAZ": "Кеназ",
    "GEBO": "Гебо",
    "WUNJO": "Вуньо",
    "HAGALAZ": "Хагалаз",
    "NAUTHIZ": "Наутиз",
    "ISA": "Иса",
    "JERA": "Йера",
    "EIHWAZ": "Эйваз",
    "PERTH": "Перт",
    "ALGIZ": "Альгиз",
    "SOWILO": "Соуло",
    "TIWAZ": "Тейваз",
    "BERKANA": "Беркана",
    "EWAZ": "Эваз",
    "MANNAZ": "Манназ",
    "LAGUZ": "Лагуз",
    "INGUZ": "Ингуз",
    "OTHALA": "Одал",
    "DAGAZ": "Дагаз",
    "VIRD": "Вирд",
}


def load_advices() -> dict[str, str]:
    """Читает файл Советы.txt и возвращает словарь {руна: совет}."""
    advices = {}
    try:
        with open(ADVICES_FILE, "r", encoding="windows-1251") as f:
            content = f.read()
    except FileNotFoundError:
        logger.warning(f"Файл {ADVICES_FILE} не найден.")
        return advices
    
    # Парсим по пустым строкам
    blocks = content.split("\n\n")
    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        
        first_line = lines[0]
        if " - " in first_line:
            rune_name = first_line.split(" - ")[0].strip()
            advice_text = first_line.split(" - ", 1)[1].strip()
            # Добавляем остальные строки
            for line in lines[1:]:
                advice_text += " " + line
            advices[rune_name] = advice_text
    
    return advices


def get_rune_advice(rune_name: str) -> str:
    """Возвращает совет для руны."""
    advices = load_advices()
    return advices.get(rune_name, "")


def get_steampunk_cards() -> list[dict]:
    """Возвращает список карт из папки STEAMPUNK с именами рун."""
    cards = []
    try:
        for f in os.listdir(STEAMPUNK_DIR):
            name, ext = os.path.splitext(f)
            if ext.lower() not in SUPPORTED_IMAGE_EXTS:
                continue
            if name.lower() == "рубашка":
                continue
            
            # Извлекаем номер из имени файла (например, "1fehu" -> "1")
            number = "".join(c for c in name if c.isdigit())
            if number:
                number_int = int(number)
                if number_int in RUNE_NAMES_MAP:
                    rune_name = RUNE_NAMES_MAP[number_int]
                    cards.append({
                        "path": os.path.join(STEAMPUNK_DIR, f),
                        "rune_name": rune_name,
                        "number": number
                    })
    except FileNotFoundError:
        logger.warning(f"Папка {STEAMPUNK_DIR} не найдена.")
    return cards


def get_random_steampunk_card(sphere: str = "general") -> dict | None:
    """
    Возвращает случайную карту.
    sphere: "relations" (STEAMPUNK), "money" (STEAMPUNK_MAIN), "advice" (STEAMPUNK)
    """
    if sphere == "money":
        cards = get_steampunk_main_cards()
    elif sphere == "advice":
        cards = get_steampunk_cards()
    else:
        # По умолчанию и для relations используем STEAMPUNK
        cards = get_steampunk_cards()
    
    if not cards:
        return None
    
    card = random.choice(cards)
    card["advice"] = get_rune_advice(card["rune_name"])
    return card


def get_steampunk_main_cards() -> list[dict]:
    """Возвращает список карт из папки STEAMPUNK_MAIN с именами рун."""
    cards = []
    try:
        for f in os.listdir(STEAMPUNK_MAIN_DIR):
            name, ext = os.path.splitext(f)
            if ext.lower() not in SUPPORTED_IMAGE_EXTS:
                continue
            
            # Извлекаем номер из имени файла (например, "1 - FEHU_maket.png" -> "1")
            number_match = re.match(r'^(\d+)\s*-\s*[A-Z]+', name)
            if number_match:
                number = int(number_match.group(1))
                if number in RUNE_NAMES_MAP:
                    rune_name = RUNE_NAMES_MAP[number]
                    cards.append({
                        "path": os.path.join(STEAMPUNK_MAIN_DIR, f),
                        "rune_name": rune_name,
                        "number": str(number),
                        "advice": get_rune_advice(rune_name)
                    })
    except FileNotFoundError:
        logger.warning(f"Папка {STEAMPUNK_MAIN_DIR} не найдена.")
    logger.info(f"Найдено карт из STEAMPUNK_MAIN: {len(cards)}")
    return cards


# --- Справочник рун ---

# Маппинг русских имен на английские
RUNE_NAME_MAP_RU_TO_EN = {
    "Феху": "Fehu",
    "Уруз": "Uruz",
    "Турисаз": "Thurisaz",
    "Турисаз ПП": "Thurisaz",
    "Ансуз": "Ansuz",
    "Ансуз ПП": "Ansuz",
    "Райдо": "Raido",
    "Райдо ПП": "Raido",
    "Кеназ": "Kenaz",
    "Кеназ ПП": "Kenaz",
    "Гебо": "Gebo",
    "Гебо в негативе": "Gebo",
    "Вуньо": "Wunjo",
    "Вуньо ПП": "Wunjo",
    "Хагалаз": "Hagalaz",
    "Хагалаз в негативе": "Hagalaz",
    "Наутиз": "Nauthiz",
    "Наутиз в негативе": "Nauthiz",
    "Иса": "Isa",
    "Иса в негативе": "Isa",
    "Йера": "Jera",
    "Йера в негативе": "Jera",
    "Эйваз": "Eihwaz",
    "Эйваз в негативе": "Eihwaz",
    "Перт": "Perth",
    "Перт в негативе": "Perth",
    "Альгиз": "Algiz",
    "Альгиз ПП": "Algiz",
    "Соуло": "Sowilo",
    "Соуло в негативе": "Sowilo",
    "Тейваз": "Tiwaz",
    "Тейваз в негативе": "Tiwaz",
    "Беркана": "Berkana",
    "Беркана ПП": "Berkana",
    "Эваз": "Ewaz",
    "Эваз ПП": "Ewaz",
    "Манназ": "Mannaz",
    "Манназ ПП": "Mannaz",
    "Лагуз": "Laguz",
    "Лагуз в негативе": "Laguz",
    "Ингуз": "Inguz",
    "Ингуз в негативе": "Inguz",
    "Одал": "Othala",
    "Одал ПП": "Othala",
    "Дагаз": "Dagaz",
    "Дагаз в негативе": "Dagaz",
}

def get_rune_image(rune_name: str) -> str | None:
    """Ищет изображение руны по английскому или русскому имени из папки RUNES_IMAGES_DIR."""
    # Если пришло русское имя, переводим в английское
    eng_name = RUNE_NAME_MAP_RU_TO_EN.get(rune_name, rune_name)
    
    try:
        for f in os.listdir(RUNES_IMAGES_DIR):
            name, ext = os.path.splitext(f)
            if ext.lower() not in SUPPORTED_IMAGE_EXTS:
                continue
            
            # Извлекаем английское имя из названия файла (например, '01.Fehu.jpeg' -> 'Fehu')
            # Формат: NN.RUNE_NAME.ext или просто RUNE_NAME.ext
            # Пробелы в имени руны возможны (например "Raido new")
            name_parts = name.split(".")
            if len(name_parts) >= 2:
                eng_name_from_file = name_parts[-1]  # Последняя часть после точки - английское имя
            else:
                eng_name_from_file = name
            
            # Убираем " new" если есть (для файлов вроде "Raido new.png")
            eng_name_from_file = eng_name_from_file.replace(" new", "").strip()
            
            if eng_name_from_file.lower() == eng_name.lower():
                return os.path.join(RUNES_IMAGES_DIR, f)
    except FileNotFoundError:
        pass
    return None


def get_all_rune_names() -> list[str]:
    """Возвращает список имён рун."""
    return list(RUNE_NAMES_MAP.values())


def load_runes_values() -> dict[str, dict]:
    """Читает файл Значения рун.txt из корня проекта или из data/texts/."""
    result = {}
    
    # Сначала пытаемся прочитать из data/texts/runes_values.txt
    try:
        with open(RUNES_VALUES_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        # Fallback на корневой файл
        try:
            with open(RUNES_VALUES_ROOT, "r", encoding="windows-1251") as f:
                lines = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return result
    
    # Парсим пары строк: первая = прямое, вторая = перевёрнутое/негатив
    i = 0
    while i + 1 < len(lines):
        line1 = lines[i]
        line2 = lines[i + 1]
        
        # Извлекаем имя руны из первой строки
        if " - " in line1:
            rune_name = line1.split(" - ")[0].strip()
            value = line1.split(" - ", 1)[1].strip()
        else:
            i += 2
            continue
        
        # Извлекаем второе значение
        if " - " in line2:
            value_pp = line2.split(" - ", 1)[1].strip()
        else:
            value_pp = line2
        
        result[rune_name] = {
            "value": value,
            "value_pp": value_pp
        }
        i += 2
    
    return result


def get_rune_info(rune_name: str) -> dict | None:
    """Возвращает информацию о руне."""
    runes = load_runes_values()
    return runes.get(rune_name)


# --- Практикумы ---

def load_practicums() -> str:
    """Читает файл практикумов."""
    try:
        with open(PRACTICUMS_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def save_practicums(text: str) -> None:
    """Сохраняет текст практикумов."""
    with open(PRACTICUMS_FILE, "w", encoding="utf-8") as f:
        f.write(text)


def format_admin_text(text: str) -> str:
    """
    Форматирует текст для админа по маркерам:
    *text* → жирный (HTML <b>)
    _text_ → курсив (HTML <i>)
    =text= → подчеркнутый (HTML <u>)
    $text$ → зачеркнутый (HTML <s>)
    
    Поддерживает комбинирование: =*text*= → жирный + подчеркнутый
    """
    import re
    
    # Обработка комбинированных стилей с =* и *= (сначала!)
    # =*text*= → <b><u>text</u></b>
    text = re.sub(r'=\*(.+?)\*=', r'<b><u>\1</u></b>', text)
    
    # Обработка =text= (только подчеркнутый)
    text = re.sub(r'=([^=<>]+)=', r'<u>\1</u>', text)
    
    # Обработка $text$ (зачеркнутый)
    text = re.sub(r'\$([^\$<>]+)\$', r'<s>\1</s>', text)
    
    # Обработка *text* (жирный)
    text = re.sub(r'\*([^\*<>]+)\*', r'<b>\1</b>', text)
    
    # Обработка _text_ (курсив)
    text = re.sub(r'_([^_<>]+)_', r'<i>\1</i>', text)
    
    return text
