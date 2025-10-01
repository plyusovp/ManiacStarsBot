# plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/handlers/menu_handler.py

import logging
import uuid
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from config import settings
from database import db
from gifts import GIFTS_CATALOG
from handlers.utils import (
    check_subscription,
    clean_junk_message,
    generate_referral_link,
    get_user_info_text,
    safe_delete,
    safe_edit_caption,
    safe_edit_media,
)
from keyboards.factories import AchievementCallback, GiftCallback, MenuCallback
from keyboards.inline import (
    achievements_keyboard,
    back_to_achievements_keyboard,
    back_to_menu_keyboard,
    games_menu_keyboard,
    gift_confirm_keyboard,
    gifts_catalog_keyboard,
    main_menu_keyboard,
    profile_keyboard,
    resources_keyboard,
    top_users_keyboard,
)
from lexicon.texts import LEXICON, LEXICON_ERRORS

router = Router()
logger = logging.getLogger(__name__)


async def show_main_menu(
    bot: Bot,
    chat_id: int,
    message_id: Optional[int] = None,
    state: Optional[FSMContext] = None,
):
    """Отображает или обновляет главное меню."""
    balance = await db.get_user_balance(chat_id)
    caption = LEXICON["main_menu"].format(balance=balance)
    media = InputMediaPhoto(media=settings.PHOTO_MAIN_MENU, caption=caption)

    success = False
    if message_id is not None:
        # Try to edit the existing message
        success = await safe_edit_media(
            bot=bot,
            media=media,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=main_menu_keyboard(),
        )

    if not success:
        # If editing fails, delete the old one and send a new one
        if message_id:
            await safe_delete(bot, chat_id, message_id)
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=settings.PHOTO_MAIN_MENU,
                caption=caption,
                reply_markup=main_menu_keyboard(),
            )
        except Exception as e:
            logger.error(f"Failed to send main menu photo: {e}")
            await bot.send_message(
                chat_id,
                caption,
                reply_markup=main_menu_keyboard(),
            )

    # Always update the state to reflect the current view
    if state:
        await state.update_data(current_view="main_menu")


# ИСПРАВЛЕНИЕ: Регистрируем один обработчик для команды и текста через разные декораторы
@router.message(Command("menu"))
@router.message(F.text == "📖 Меню")
async def menu_handler(message: Message, state: FSMContext, bot: Bot):
    """Handler for the /menu command and '📖 Меню' button."""
    if message.chat.type == "private":
        try:
            # Удаляем сообщение пользователя (команду или текст), чтобы чат был чище
            await message.delete()
        except Exception as e:
            logger.warning(f"Could not delete message {message.message_id}: {e}")
        # Отправляем меню новым сообщением
        await show_main_menu(bot, message.chat.id, state=state)


# ИСПРАВЛЕНИЕ: Аналогично для бонуса
@router.message(Command("bonus"))
@router.message(F.text == "🎁 Бонус")
async def bonus_handler(message: Message):
    """Handler for the /bonus command and '🎁 Бонус' button."""
    if not message.from_user:
        return

    result = await db.get_daily_bonus(message.from_user.id)
    status = result.get("status")
    if status == "success":
        reward = result.get("reward", 0)
        await message.answer(f"🎁 Вы получили {reward} ⭐ дневного бонуса!")
    elif status == "wait":
        seconds = result.get("seconds_left", 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        await message.answer(f"⏳ Бонус будет доступен через {hours} ч {minutes} м.")
    else:
        # ДОБАВЛЕНО ЛОГИРОВАНИЕ ОШИБКИ
        logger.error(
            "Failed to get daily bonus for user %d via command. Status: %s, Result: %s",
            message.from_user.id,
            status,
            result,
        )
        await message.answer("❌ Не удалось получить бонус. Попробуйте позже.")


@router.callback_query(MenuCallback.filter(F.name == "main_menu"))
async def back_to_main_menu_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
):
    """Central handler for all 'Back to main menu' buttons."""
    data = await state.get_data()
    # Prevent re-editing if already on the main menu
    if data.get("current_view") == "main_menu":
        await callback.answer()
        return

    await state.clear()
    await clean_junk_message(state, bot)
    if callback.message:
        await show_main_menu(
            bot, callback.message.chat.id, callback.message.message_id, state
        )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "profile"))
async def profile_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await clean_junk_message(state, bot)
    if callback.message:
        profile_text = await get_user_info_text(callback.from_user.id)
        media = InputMediaPhoto(media=settings.PHOTO_PROFILE, caption=profile_text)
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=profile_keyboard(),
        )
        await state.update_data(current_view="profile")
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "earn_bread"))
async def referral_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await clean_junk_message(state, bot)
    if callback.message:
        referral_link = generate_referral_link(callback.from_user.id)
        referrals_count = await db.get_referrals_count(callback.from_user.id)
        text = LEXICON["referral_menu"].format(
            ref_link=referral_link,
            invited_count=referrals_count,
            ref_bonus=settings.REFERRAL_BONUS,
        )
        media = InputMediaPhoto(media=settings.PHOTO_EARN_STARS, caption=text)
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=back_to_menu_keyboard(),
        )
        await state.update_data(current_view="earn_bread")
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "top_users"))
async def top_users_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await clean_junk_message(state, bot)
    if callback.message:
        top_users = await db.get_top_referrers()
        top_users_text = ""
        if top_users:
            for i, user in enumerate(top_users, 1):
                top_users_text += (
                    f"{i}. {user['full_name']} — {user['ref_count']} 🙋‍♂️\n"
                )
        else:
            top_users_text = "Пока никто не пригласил друзей."

        text = LEXICON["top_menu"].format(top_users_text=top_users_text)
        media = InputMediaPhoto(media=settings.PHOTO_TOP, caption=text)
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=top_users_keyboard(),
        )
        await state.update_data(current_view="top_users")
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "gifts"))
async def gifts_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await clean_junk_message(state, bot)
    if not callback.message:
        return await callback.answer()

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    referrals = await db.get_referrals_count(user_id)

    text = LEXICON["gifts_menu"].format(
        balance=balance,
        min_refs=settings.MIN_REFERRALS_FOR_WITHDRAW,
        referrals_count=referrals,
    )
    media = InputMediaPhoto(media=settings.PHOTO_WITHDRAW, caption=text)

    await safe_edit_media(
        bot=bot,
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=gifts_catalog_keyboard(),
    )
    await state.update_data(current_view="gifts")
    await callback.answer()


@router.callback_query(GiftCallback.filter(F.action == "select"))
async def select_gift_handler(
    callback: CallbackQuery, callback_data: GiftCallback, bot: Bot
):
    """Handles the selection of a gift and shows the confirmation screen."""
    item_id = callback_data.item_id
    cost = callback_data.cost

    gift = next((g for g in GIFTS_CATALOG if g["id"] == item_id), None)
    if not gift or not callback.message:
        await callback.answer("Подарок не найден!", show_alert=True)
        return

    text = LEXICON["gift_confirm"].format(
        cost=cost,
        emoji=gift["emoji"],
        name=gift["name"],
    )

    await safe_edit_caption(
        bot=bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=gift_confirm_keyboard(item_id, cost),
    )
    await callback.answer()


@router.callback_query(GiftCallback.filter(F.action == "confirm"))
async def confirm_gift_handler(
    callback: CallbackQuery, callback_data: GiftCallback, bot: Bot, state: FSMContext
):
    """Handles the final confirmation and processes the withdrawal request."""
    if not callback.from_user:
        return
    user_id = callback.from_user.id
    cost = callback_data.cost
    item_id = callback_data.item_id

    # --- Pre-checks ---
    errors = []
    is_admin = user_id in settings.ADMIN_IDS

    if not is_admin:
        # 1. Subscription check for regular users
        is_subscribed = await check_subscription(bot, user_id)
        if not is_subscribed:
            errors.append(LEXICON_ERRORS["error_not_subscribed"])

        # 2. Referrals check for regular users
        referrals_count = await db.get_referrals_count(user_id)
        if referrals_count < settings.MIN_REFERRALS_FOR_WITHDRAW:
            errors.append(
                LEXICON_ERRORS["error_not_enough_referrals"].format(
                    min_refs=settings.MIN_REFERRALS_FOR_WITHDRAW,
                    current_refs=referrals_count,
                )
            )

    # 3. Balance check (for everyone)
    balance = await db.get_user_balance(user_id)
    if balance < cost:
        errors.append("Недостаточно средств на балансе.")

    if errors:
        error_text = "\n\n".join(errors)
        await callback.answer(error_text, show_alert=True)
        return

    # --- Processing ---
    idem_key = f"reward-{user_id}-{uuid.uuid4()}"
    result = await db.create_reward_request(user_id, item_id, cost, idem_key)

    if result.get("success"):
        gift = next((g for g in GIFTS_CATALOG if g["id"] == item_id), None)
        if gift:
            success_text = LEXICON["withdrawal_success"].format(
                emoji=gift["emoji"], name=gift["name"], amount=cost
            )
            await callback.answer(success_text, show_alert=True)
            # Go back to main menu
            if callback.message:
                await show_main_menu(
                    bot, callback.message.chat.id, callback.message.message_id, state
                )
    else:
        reason = result.get("reason", "unknown_error")
        await callback.answer(f"Ошибка: {reason}. Попробуйте позже.", show_alert=True)


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
        await state.update_data(current_view="games")
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "resources"))
async def resources_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает меню 'Наши ресурсы' с фотографией из раздела выводов."""
    await state.clear()
    await clean_junk_message(state, bot)

    if not callback.message:
        await callback.answer()
        return

    chat_id = callback.message.chat.id
    message_id = callback.message.message_id
    caption = LEXICON["resources_menu"]
    # Используем фото из раздела выводов
    media = InputMediaPhoto(media=settings.PHOTO_WITHDRAW, caption=caption)

    # Пытаемся изменить существующее сообщение
    await safe_edit_media(
        bot=bot,
        media=media,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=resources_keyboard(),
    )

    await state.update_data(current_view="resources")
    await callback.answer()


# --- Game placeholder handlers ---
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
        # ДОБАВЛЕНО ЛОГИРОВАНИЕ ОШИБКИ
        logger.error(
            "Failed to get daily bonus for user %d via callback. Status: %s, Result: %s",
            callback.from_user.id,
            status,
            result,
        )
        await callback.answer(
            "❌ Не удалось получить бонус. Попробуйте позже.", show_alert=True
        )


# --- Achievements Section ---
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
        await state.update_data(current_view="achievements")
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
    callback: CallbackQuery,
    callback_data: AchievementCallback,
    bot: Bot,
    state: FSMContext,
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
        await state.update_data(current_view="achievement_info")
    await callback.answer()
