# plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/handlers/menu_handler.py

import logging
import time
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from config import settings
from database import db
from handlers.utils import (
    clean_junk_message,
    escape_markdown_v1,
    generate_referral_link,
    get_safe_media,
    get_user_info_text,
    safe_delete,
    safe_edit_caption,
    safe_edit_media,
)
from keyboards.factories import AchievementCallback, MenuCallback
from keyboards.inline import (
    achievements_keyboard,
    back_to_achievements_keyboard,
    back_to_menu_keyboard,
    faq_keyboard,
    games_menu_keyboard,
    gifts_catalog_keyboard,
    language_settings_keyboard,
    main_menu_keyboard,
    profile_keyboard,
    resources_keyboard,
    settings_keyboard,
    terms_keyboard,
    top_users_keyboard,
)
from lexicon.languages import get_text

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
    user_language = await db.get_user_language(chat_id)
    caption = get_text("main_menu", user_language, balance=balance)
    media = get_safe_media(settings.PHOTO_MAIN_MENU, caption)

    success = False
    if message_id is not None:
        # Try to edit the existing message
        success = await safe_edit_media(
            bot=bot,
            media=media,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=main_menu_keyboard(user_language),
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
                reply_markup=main_menu_keyboard(user_language),
            )
        except Exception as e:
            logger.error(f"Failed to send main menu photo: {e}")
            await bot.send_message(
                chat_id,
                caption,
                reply_markup=main_menu_keyboard(user_language),
            )

    # Always update the state to reflect the current view
    if state:
        await state.update_data(current_view="main_menu")


# ИСПРАВЛЕНИЕ: Регистрируем один обработчик для команды и текста через разные декораторы
@router.message(Command("menu"))
@router.message(F.text == "📖 Меню")
async def menu_handler(message: Message, state: FSMContext, bot: Bot):
    """Handler for the /menu command and '📖 Меню' button."""
    if not message.from_user:
        return

    # Проверяем подписку перед показом меню
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        message, message.from_user.id, message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

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

    # Проверяем подписку перед выдачей бонуса
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        message, message.from_user.id, message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

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
    if not callback.from_user:
        return

    # Проверяем подписку перед показом главного меню
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

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
    if not callback.from_user:
        return

    # Проверяем подписку перед показом профиля
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    await clean_junk_message(state, bot)
    if callback.message:
        # Проверяем достижение "Любопытный" при заходе в профиль
        try:
            await db.grant_achievement(callback.from_user.id, "curious", bot)
        except Exception as e:
            logger.warning(
                f"Failed to grant curious achievement for user {callback.from_user.id}: {e}"
            )

        profile_text = await get_user_info_text(callback.from_user.id)
        media = InputMediaPhoto(media=settings.PHOTO_PROFILE, caption=profile_text)
        user_language = await db.get_user_language(callback.from_user.id)
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=profile_keyboard(user_language),
        )
        await state.update_data(current_view="profile")
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "earn_bread"))
async def referral_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not callback.from_user:
        return

    # Проверяем подписку перед показом реферального меню
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    await clean_junk_message(state, bot)
    if callback.message:
        referral_link = generate_referral_link(callback.from_user.id)
        referral_link_escaped = escape_markdown_v1(referral_link)
        referrals_count = await db.get_referrals_count(callback.from_user.id)
        # Вычисляем заработанную сумму
        earned = referrals_count * settings.REFERRAL_BONUS

        user_language = await db.get_user_language(callback.from_user.id)
        text = get_text(
            "referral_menu",
            user_language,
            ref_link=referral_link_escaped,
            invited_count=referrals_count,
            ref_bonus=settings.REFERRAL_BONUS,
            earned=earned,
        )
        media = InputMediaPhoto(media=settings.PHOTO_EARN_STARS, caption=text)
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=back_to_menu_keyboard(user_language),
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

        user_language = await db.get_user_language(callback.from_user.id)
        text = get_text("top_menu", user_language, top_users_text=top_users_text)
        media = InputMediaPhoto(media=settings.PHOTO_TOP, caption=text)
        await bot.edit_message_media(
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=top_users_keyboard(user_language),
        )
        await state.update_data(current_view="top_users")
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "gifts"))
async def gifts_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not callback.from_user:
        return

    # Проверяем подписку перед показом подарков
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    await state.clear()
    await clean_junk_message(state, bot)
    if not callback.message:
        return await callback.answer()

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    referrals = await db.get_referrals_count(user_id)

    user_language = await db.get_user_language(user_id)
    text = get_text(
        "gifts_menu",
        user_language,
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
        reply_markup=gifts_catalog_keyboard(user_language),
    )
    await state.update_data(current_view="gifts")
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "games"))
async def games_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает меню 'Игры'."""
    if not callback.from_user:
        return

    # Проверяем подписку перед показом игр
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    await state.clear()
    await clean_junk_message(state, bot)
    user_language = await db.get_user_language(callback.from_user.id)
    media = InputMediaPhoto(
        media=settings.PHOTO_GAMES_MENU, caption=get_text("games_menu", user_language)
    )
    if callback.message:
        await safe_edit_media(
            bot=bot,
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=games_menu_keyboard(user_language),
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
    user_language = await db.get_user_language(callback.from_user.id)
    caption = get_text("resources_menu", user_language)
    # Используем фото для ресурсов
    media = InputMediaPhoto(media=settings.PHOTO_RESOURCES, caption=caption)

    # Пытаемся изменить существующее сообщение
    await safe_edit_media(
        bot=bot,
        media=media,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=resources_keyboard(user_language),
    )

    await state.update_data(current_view="resources")
    await callback.answer()


# --- Game placeholder handlers ---
@router.callback_query(MenuCallback.filter(F.name == "placeholder_game"))
async def placeholder_game_handler(callback: CallbackQuery):
    """Обработчик для игр в разработке."""
    await callback.answer("Эта игра скоро появится!", show_alert=True)


@router.callback_query(MenuCallback.filter(F.name == "passive_income"))
async def passive_income_handler(callback: CallbackQuery, bot: Bot):
    """Обработчик для кнопки пассивного дохода."""
    if not callback.from_user:
        return

    user_id = callback.from_user.id

    # Получаем статус пассивного дохода
    status = await db.get_passive_income_status(user_id)

    # Проверяем, есть ли ссылка в био
    has_link = await db.check_user_bio_for_bot_link(bot, user_id, settings.BOT_USERNAME)

    if has_link and not status["enabled"]:
        # Активируем пассивный доход
        await db.update_passive_income_status(user_id, True)
        text = (
            "🎉 **Пассивный доход активирован!**\n\n"
            "Отлично! Вы разместили ссылку на бота в своем профиле.\n\n"
            "💰 **Теперь вы будете получать:**\n"
            "• 1 ⭐ каждый день\n"
            "• 30 ⭐ в месяц автоматически\n\n"
            "🔄 Выдача происходит автоматически каждые 24 часа\n"
            "📩 Вы получите уведомление о начислении\n\n"
            "⚠️ **Важно:** Не удаляйте ссылку из профиля!"
        )
    elif has_link and status["enabled"]:
        # Пользователь уже активировал, показываем статус
        current_time = int(time.time())
        last_income = status["last_income_time"]

        if last_income == 0:
            text = (
                "✅ **Пассивный доход активен!**\n\n"
                "💰 **Ваши доходы:**\n"
                "• 1 ⭐ каждый день\n"
                "• 30 ⭐ в месяц автоматически\n\n"
                "🎁 Первое начисление произойдет в течение 24 часов"
            )
        else:
            time_since_last = current_time - last_income
            if time_since_last >= 24 * 3600:
                text = (
                    "✅ **Пассивный доход активен!**\n\n"
                    "💰 **Ваши доходы:**\n"
                    "• 1 ⭐ каждый день\n"
                    "• 30 ⭐ в месяц автоматически\n\n"
                    "🎁 Новое начисление готово к выдаче!"
                )
            else:
                hours_left = (24 * 3600 - time_since_last) // 3600
                minutes_left = ((24 * 3600 - time_since_last) % 3600) // 60
                text = (
                    "✅ **Пассивный доход активен!**\n\n"
                    "💰 **Ваши доходы:**\n"
                    "• 1 ⭐ каждый день\n"
                    "• 30 ⭐ в месяц автоматически\n\n"
                    f"⏰ Следующее начисление через: {hours_left}ч {minutes_left}м"
                )
    else:
        # Ссылки нет в bio или пассивный доход отключен
        text = (
            "📈 **Пассивный доход**\n\n"
            "💰 **Зарабатывайте автоматически:**\n"
            "• 1 ⭐ каждый день\n"
            "• 30 ⭐ в месяц пассивно\n\n"
            "🔗 **Что нужно сделать:**\n"
            f"Разместите эту ссылку в своем профиле:\n`t.me/{settings.BOT_USERNAME}`\n\n"
            "📝 **Пошаговая инструкция:**\n"
            "1. Откройте настройки Telegram\n"
            "2. Нажмите «Изменить профиль»\n"
            "3. В поле «О себе» добавьте ссылку\n"
            "4. Сохраните изменения\n"
            "5. Вернитесь сюда и нажмите кнопку снова\n\n"
            "🔄 После активации деньги будут приходить автоматически!\n"
            "📩 Вы получите уведомление о каждом начислении\n\n"
            "⚠️ **Важно:** Ссылка должна оставаться в профиле"
        )

    await callback.answer(text, show_alert=True)


@router.callback_query(MenuCallback.filter(F.name == "get_daily_bonus"))
async def get_daily_bonus_callback_handler(callback: CallbackQuery):
    """Обработчик для кнопки ежедневного бонуса."""
    if not callback.from_user:
        return

    # Проверяем подписку перед выдачей бонуса
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    result = await db.get_daily_bonus(callback.from_user.id)
    status = result.get("status")
    if status == "success":
        reward = result.get("reward", 0)

        # Проверяем достижение "Охотник за бонусами"
        try:
            await db.grant_achievement(
                callback.from_user.id, "bonus_hunter", callback.bot
            )
        except Exception as e:
            logger.warning(
                f"Failed to grant bonus_hunter achievement for user {callback.from_user.id}: {e}"
            )

        # Проверяем достижения за стрик
        try:
            await db.check_streak_achievements(callback.from_user.id, callback.bot)
        except Exception as e:
            logger.warning(
                f"Failed to check streak achievements for user {callback.from_user.id}: {e}"
            )

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
    if not callback.from_user:
        return

    # Проверяем подписку перед показом достижений
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

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
        f"**{details['name']}** ({details['rarity']})\n\n"
        f"_{details['description']}_\n\n"
        f"**Награда:** {details['reward']} ⭐\n"
        f"**Статус:** {status}"
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


# --- Settings Handlers ---
@router.callback_query(MenuCallback.filter(F.name == "settings"))
async def settings_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает меню настроек."""
    if not callback.from_user:
        return

    # Проверяем подписку перед показом настроек
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    await clean_junk_message(state, bot)
    user_language = await db.get_user_language(callback.from_user.id)
    text = get_text("settings_menu", user_language)

    if callback.message:
        # Проверяем, есть ли фото в текущем сообщении
        if callback.message.photo:
            # Редактируем существующее фото
            await safe_edit_caption(
                bot=bot,
                caption=text,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=settings_keyboard(user_language),
            )
        else:
            # Удаляем текстовое сообщение и отправляем новое с фото
            await safe_delete(
                bot, callback.message.chat.id, callback.message.message_id
            )
            new_msg = await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=settings.PHOTO_MAIN_MENU,
                caption=text,
                reply_markup=settings_keyboard(user_language),
            )
            await state.update_data(last_bot_message_id=new_msg.message_id)
        await state.update_data(current_view="settings")
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "faq"))
async def faq_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает FAQ."""
    if not callback.from_user:
        return

    # Проверяем подписку перед показом FAQ
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    await clean_junk_message(state, bot)
    user_language = await db.get_user_language(callback.from_user.id)
    text = get_text("faq_menu", user_language)

    if callback.message:
        # Удаляем старое сообщение и отправляем новое текстовое с HTML-форматированием
        await safe_delete(bot, callback.message.chat.id, callback.message.message_id)
        new_msg = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=text,
            reply_markup=faq_keyboard(user_language),
            parse_mode="HTML",  # Используем HTML для стабильного форматирования длинных текстов
        )
        await state.update_data(
            current_view="faq", last_bot_message_id=new_msg.message_id
        )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "terms"))
async def terms_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает пользовательское соглашение."""
    if not callback.from_user:
        return

    # Проверяем подписку перед показом соглашения
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    await clean_junk_message(state, bot)
    user_language = await db.get_user_language(callback.from_user.id)

    # Добавляем текущую дату в текст соглашения
    from datetime import datetime

    current_date = datetime.now().strftime("%d.%m.%Y")
    text = get_text("terms_of_service", user_language, current_date=current_date)

    if callback.message:
        # Удаляем старое сообщение и отправляем новое текстовое с HTML-форматированием
        await safe_delete(bot, callback.message.chat.id, callback.message.message_id)
        new_msg = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=text,
            reply_markup=terms_keyboard(user_language),
            parse_mode="HTML",  # Используем HTML для стабильного форматирования длинных текстов
        )
        await state.update_data(
            current_view="terms", last_bot_message_id=new_msg.message_id
        )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "language_settings"))
async def language_settings_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
):
    """Отображает настройки языка."""
    if not callback.from_user:
        return

    # Проверяем подписку перед показом настроек языка
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        callback, callback.from_user.id, callback.message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    await clean_junk_message(state, bot)
    user_language = await db.get_user_language(callback.from_user.id)
    text = get_text(
        "language_settings",
        user_language,
        default="🌍 **Настройки языка** 🌍\n\nВыберите язык интерфейса:",
    )

    if callback.message:
        await safe_edit_caption(
            bot=bot,
            caption=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=language_settings_keyboard(user_language),
        )
        await state.update_data(current_view="language_settings")
    await callback.answer()
