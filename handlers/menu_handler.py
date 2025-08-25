# handlers/menu_handler.py
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto

from config import settings
from database import db
from handlers.utils import clean_junk_message
from keyboards.inline import (achievements_keyboard,
                              back_to_achievements_keyboard,
                              entertainment_menu_keyboard, main_menu_keyboard)
from lexicon.texts import LEXICON

router = Router()


async def show_main_menu(bot: Bot, chat_id: int, user_id: int, message_id: int = None):
    """Отображает или обновляет главное меню."""
    balance = await db.get_user_balance(user_id)
    text = LEXICON["main_menu"].format(balance=balance)
    media = InputMediaPhoto(
        media=settings.PHOTO_MAIN_MENU,
        caption=text
    )
    
    if message_id:
        try:
            await bot.edit_message_media(
                media=media,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=main_menu_keyboard(),
            )
        except Exception:
            await bot.send_photo(
                chat_id=chat_id,
                photo=settings.PHOTO_MAIN_MENU,
                caption=text,
                reply_markup=main_menu_keyboard(),
            )
    else:
        await bot.send_photo(
            chat_id=chat_id,
            photo=settings.PHOTO_MAIN_MENU,
            caption=text,
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(F.data == "entertainment")
async def entertainment_handler(callback: CallbackQuery, state: FSMContext):
    """Отображает меню 'Развлечения'."""
    await clean_junk_message(callback, state)
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=settings.PHOTO_MAIN_MENU, 
            caption=LEXICON["entertainment_menu"]
        ),
        reply_markup=entertainment_menu_keyboard(),
    )


@router.callback_query(F.data == "achievements")
async def achievements_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Отображает список достижений (первая страница)."""
    await clean_junk_message(callback, state)
    user_id = callback.from_user.id
    page = 1
    limit = 5

    all_achs = await db.get_all_achievements()
    user_achs = await db.get_user_achievements(user_id)
    
    total_pages = (len(all_achs) + limit - 1) // limit
    start_index = (page - 1) * limit
    end_index = start_index + limit
    current_page_achs = all_achs[start_index:end_index]

    text = f"📜 Ваши достижения ({len(user_achs)}/{len(all_achs)})"
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=settings.PHOTO_ACHIEVEMENTS, 
            caption=text
        ),
        reply_markup=achievements_keyboard(current_page_achs, user_achs, page, total_pages),
    )


@router.callback_query(F.data.startswith("ach_page_"))
async def achievements_page_handler(callback: CallbackQuery, bot: Bot):
    """Обрабатывает переключение страниц в достижениях."""
    page = int(callback.data.split("_")[-1])
    limit = 5
    user_id = callback.from_user.id

    all_achs = await db.get_all_achievements()
    user_achs = await db.get_user_achievements(user_id)
    
    total_pages = (len(all_achs) + limit - 1) // limit
    start_index = (page - 1) * limit
    end_index = start_index + limit
    current_page_achs = all_achs[start_index:end_index]

    await callback.message.edit_reply_markup(
        reply_markup=achievements_keyboard(current_page_achs, user_achs, page, total_pages)
    )


@router.callback_query(F.data.startswith("ach_info_"))
async def achievement_info_handler(callback: CallbackQuery):
    """Показывает детальную информацию о достижении."""
    ach_id = callback.data.split("_")[-1]
    details = await db.get_achievement_details(ach_id)
    if not details:
        return await callback.answer("Достижение не найдено.", show_alert=True)

    name, description, reward, rarity = details
    user_achs = await db.get_user_achievements(callback.from_user.id)
    status = "✅ Получено" if ach_id in user_achs else "❌ Не получено"

    text = (
        f"<b>{name}</b> ({rarity})\n\n"
        f"<i>{description}</i>\n\n"
        f"<b>Награда:</b> {reward} ⭐\n"
        f"<b>Статус:</b> {status}"
    )

    await callback.message.edit_caption(
        caption=text,
        reply_markup=back_to_achievements_keyboard()
    )

