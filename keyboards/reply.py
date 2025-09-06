from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def persistent_menu_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с постоянной кнопкой 'Меню'."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Меню")]],
        resize_keyboard=True,
    )
    return keyboard
