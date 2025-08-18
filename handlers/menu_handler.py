# handlers/menu_handler.py
from aiogram import Router, Bot
from aiogram.types import Message, InputMediaPhoto
from keyboards.inline import main_menu
from config import PHOTO_MAIN_MENU

router = Router()

async def show_main_menu(bot: Bot, chat_id: int, user_id: int, message_id: int = None):
    """
    Отправляет или редактирует главное меню.
    Если message_id передан - редактирует, иначе отправляет новое.
    """
    text = f"""
🔪 <b>Добро пожаловать в Maniac Stars!</b> 🔪

Это главный экран. Используй кнопки ниже для навигации по разделам.

Здесь ты можешь играть, соревноваться с друзьями и получать за это звёзды! 💫
"""
    
    # Если есть ID сообщения, пытаемся его отредактировать
    if message_id:
        try:
            await bot.edit_message_media(
                media=InputMediaPhoto(media=PHOTO_MAIN_MENU, caption=text),
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=main_menu()
            )
            return
        except Exception: # Если не вышло (например, сообщение было удалено), просто отправим новое
            pass

    # Если редактирование не удалось или не требовалось, отправляем новое сообщение
    await bot.send_photo(chat_id=chat_id, photo=PHOTO_MAIN_MENU, caption=text, reply_markup=main_menu())