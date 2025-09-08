# keyboards/reply.py
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def persistent_menu_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с постоянной кнопкой 'Меню'."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Меню")]],
        resize_keyboard=True,
        input_field_placeholder="Используйте меню для навигации",
    )
    return keyboard
