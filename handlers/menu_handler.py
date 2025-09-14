# handlers/menu_handler.py
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto

from config import settings
from database import db
from handlers.utils import (
    clean_junk_message,
    safe_delete,
    safe_edit_caption,
    safe_edit_media,
)
from keyboards.factories import AchievementCallback, MenuCallback
from keyboards.inline import (
    achievements_keyboard,
    back_to_achievements_keyboard,
    games_menu_keyboard,
    main_menu_keyboard,
    resources_keyboard,
)
from lexicon.texts import LEXICON

router = Router()


async def show_main_menu(bot: Bot, chat_id: int, message_id: Optional[int] = None):
    """Отображает или обновляет главное меню."""
    balance = await db.get_user_balance(chat_id)
    caption = LEXICON["main_menu"].format(balance=balance)
    media = InputMediaPhoto(media=settings.PHOTO_MAIN_MENU, caption=caption)

    success = False
    if message_id is not None:
        success = await safe_edit_media(
            bot=bot,
            media=media,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=main_menu_keyboard(),
        )

    if not success:
        if message_id:
            await safe_delete(bot, chat_id, message_id)
        await bot.send_photo(
            chat_id=chat_id,
            photo=settings.PHOTO_MAIN_MENU,
            caption=caption,
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(MenuCallback.filter(F.name == "games"))
async def games_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает меню 'Игры'."""
    await state.clear()
    await clean_junk_message(state, bot)
    media = InputMediaPhoto(
        media=settings.PHOTO_GAMES_MENU, caption=LEXICON["games_menu"]
    )
    if callback.message:
        await safe_edit_media(
            bot=bot,
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=games_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "resources"))
async def resources_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает меню 'Наши ресурсы'."""
    await state.clear()
    await clean_junk_message(state, bot)
    media = InputMediaPhoto(
        media=settings.PHOTO_RESOURCES, caption=LEXICON["resources_menu"]
    )
    if callback.message:
        await safe_edit_media(
            bot=bot,
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=resources_keyboard(),
        )
    await callback.answer()


# --- Новые обработчики для меню игр ---
@router.callback_query(MenuCallback.filter(F.name == "placeholder_game"))
async def placeholder_game_handler(callback: CallbackQuery):
    """Обработчик для игр в разработке."""
    await callback.answer("Эта игра скоро появится!", show_alert=True)


@router.callback_query(MenuCallback.filter(F.name == "passive_income"))
async def passive_income_handler(callback: CallbackQuery):
    """Обработчик для кнопки пассивного дохода."""
    text = (
        "Вы можете разместить реферальную ссылку на нашего бота в описании "
        "своего профиля и получать 1 ⭐ каждый день.\n\n"
        "(Функция автоматической проверки находится в разработке)"
    )
    await callback.answer(text, show_alert=True)


@router.callback_query(MenuCallback.filter(F.name == "get_daily_bonus"))
async def get_daily_bonus_callback_handler(callback: CallbackQuery):
    """Обработчик для кнопки ежедневного бонуса."""
    if not callback.from_user:
        return

    result = await db.get_daily_bonus(callback.from_user.id)
    status = result.get("status")
    if status == "success":
        reward = result.get("reward", 0)
        await callback.answer(
            f"🎁 Вы получили {reward} ⭐ дневного бонуса!", show_alert=True
        )
    elif status == "wait":
        seconds = result.get("seconds_left", 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        await callback.answer(
            f"⏳ Бонус будет доступен через {hours} ч {minutes} м.", show_alert=True
        )
    else:
        await callback.answer(
            "❌ Не удалось получить бонус. Попробуйте позже.", show_alert=True
        )


@router.callback_query(MenuCallback.filter(F.name == "achievements"))
async def achievements_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot, callback_data: MenuCallback
):
    """Отображает список достижений (первая страница)."""
    await clean_junk_message(state, bot)
    user_id = callback.from_user.id
    page = 1
    limit = 5

    all_achs = await db.get_all_achievements()
    user_achs_set = set(await db.get_user_achievements(user_id))

    total_pages = (len(all_achs) + limit - 1) // limit if all_achs else 1
    start_index = (page - 1) * limit
    end_index = start_index + limit
    current_page_achs = all_achs[start_index:end_index]

    text = f"📜 Ваши достижения ({len(user_achs_set)}/{len(all_achs)})"
    media = InputMediaPhoto(media=settings.PHOTO_ACHIEVEMENTS, caption=text)

    if callback.message:
        await safe_edit_media(
            bot=bot,
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=achievements_keyboard(
                current_page_achs, user_achs_set, page, total_pages
            ),
        )
    await callback.answer()


@router.callback_query(AchievementCallback.filter(F.action == "page"))
async def achievements_page_handler(
    callback: CallbackQuery, callback_data: AchievementCallback, bot: Bot
):
    """Обрабатывает переключение страниц в достижениях."""
    page = callback_data.page or 1
    limit = 5
    user_id = callback.from_user.id

    all_achs = await db.get_all_achievements()
    user_achs_set = set(await db.get_user_achievements(user_id))

    total_pages = (len(all_achs) + limit - 1) // limit if all_achs else 1
    start_index = (page - 1) * limit
    end_index = start_index + limit
    current_page_achs = all_achs[start_index:end_index]

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=achievements_keyboard(
                current_page_achs, user_achs_set, page, total_pages
            )
        )
    await callback.answer()


@router.callback_query(AchievementCallback.filter(F.action == "info"))
async def achievement_info_handler(
    callback: CallbackQuery, callback_data: AchievementCallback, bot: Bot
):
    """Показывает детальную информацию о достижении."""
    ach_id = callback_data.ach_id
    if not ach_id:
        return await callback.answer()
    details = await db.get_achievement_details(ach_id)
    if not details:
        await callback.answer("Достижение не найдено.", show_alert=True)
        return

    user_achs_set = set(await db.get_user_achievements(callback.from_user.id))
    status = "✅ Получено" if ach_id in user_achs_set else "❌ Не получено"

    text = (
        f"<b>{details['name']}</b> ({details['rarity']})\n\n"
        f"<i>{details['description']}</i>\n\n"
        f"<b>Награда:</b> {details['reward']} ⭐\n"
        f"<b>Статус:</b> {status}"
    )
    if callback.message:
        await safe_edit_caption(
            bot=bot,
            caption=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=back_to_achievements_keyboard(),
        )
    await callback.answer()
