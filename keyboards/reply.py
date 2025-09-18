from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Генерирует основную клавиатуру с кнопками 'Бонус', 'Старт' и 'Меню'."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🎁 Бонус"),
        KeyboardButton(text="▶️ Старт"),
        KeyboardButton(text="📖 Меню"),
    )
    return builder.as_markup(resize_keyboard=True)
