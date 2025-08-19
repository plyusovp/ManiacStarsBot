# handlers/menu_handler.py
from aiogram import Router, Bot
from aiogram.types import Message, InputMediaPhoto
from keyboards.inline import main_menu
from config import PHOTO_MAIN_MENU
from texts.texts import LEXICON

router = Router()

async def show_main_menu(bot: Bot, chat_id: int, user_id: int, message_id: int = None):
    """
    Отправляет или редактирует главное меню.
    Если message_id передан - редактирует, иначе отправляет новое.
    """
    text = LEXICON['main_menu']

    if message_id:
        try:
            await bot.edit_message_media(
                media=InputMediaPhoto(media=PHOTO_MAIN_MENU, caption=text),
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=main_menu()
            )
            return
        except Exception:
            pass

    await bot.send_photo(chat_id=chat_id, photo=PHOTO_MAIN_MENU, caption=text, reply_markup=main_menu())