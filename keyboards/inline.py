from telegram import InlineKeyboardMarkup, InlineKeyboardButton

SPHERES = [
    ("Отношения", "sphere_relations"),
    ("Деньги", "sphere_money"),
    ("Совет", "sphere_advice"),
]


def get_sphere_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура выбора сферы предсказания."""
    buttons = [[InlineKeyboardButton(text, callback_data=cb)] for text, cb in SPHERES]
    return InlineKeyboardMarkup(buttons)


def get_runes_keyboard(rune_names: list[str]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура со списком рун (по 3 в ряд)."""
    buttons = []
    row = []
    for i, name in enumerate(rune_names):
        row.append(InlineKeyboardButton(name, callback_data=f"rune_{name}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def get_subscription_keyboard(subscribed: bool) -> InlineKeyboardMarkup:
    if subscribed:
        btn = InlineKeyboardButton("Отписаться от рассылки", callback_data="unsub")
    else:
        btn = InlineKeyboardButton("Подписаться на рассылку", callback_data="sub")
    return InlineKeyboardMarkup([[btn]])
