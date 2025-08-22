# handlers/menu_handler.py
from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputMediaPhoto

from config import PHOTO_MAIN_MENU
from keyboards.inline import main_menu
from lexicon.texts import LEXICON

router = Router()


async def show_main_menu(bot: Bot, chat_id: int, user_id: int, message_id: int = None):
    """
    Отправляет или редактирует главное меню.
    Если message_id передан - редактирует, иначе отправляет новое.
    """
    text = LEXICON["main_menu"]

    try:
        if message_id:
            await bot.edit_message_media(
                media=InputMediaPhoto(media=PHOTO_MAIN_MENU, caption=text),
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=main_menu(),
            )
        else:
            await bot.send_photo(
                chat_id=chat_id,
                photo=PHOTO_MAIN_MENU,
                caption=text,
                reply_markup=main_menu(),
            )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass  # Игнорируем ошибку, если сообщение не изменилось
        else:
            # Если редактирование не удалось по другой причине, отправляем новое сообщение
            try:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=PHOTO_MAIN_MENU,
                    caption=text,
                    reply_markup=main_menu(),
                )
            except Exception as final_e:
                print(
                    f"Не удалось ни отредактировать, ни отправить главное меню: {final_e}"
                )
