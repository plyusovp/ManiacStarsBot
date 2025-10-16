# plyusovp/maniacstarsbot/ManiacStarsBot-68ffe9d3e979f3cc61bcf924e4b9ab182d77be5f/handlers/user_handlers.py

import datetime
import logging
import uuid

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from config import settings
from database import db
from gifts import GIFTS_CATALOG
from handlers.utils import safe_edit_caption, safe_edit_media
from keyboards.factories import GiftCallback, UserCallback
from keyboards.inline import (
    back_to_menu_keyboard,
    back_to_profile_keyboard,
    daily_challenges_keyboard,
    gift_confirm_keyboard,
    promo_back_keyboard,
    social_content_keyboard,
)
from keyboards.reply import get_main_menu_keyboard
from lexicon.languages import get_text

logger = logging.getLogger(__name__)
router = Router()


class PromoCodeStates(StatesGroup):
    waiting_for_promo_code = State()


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user:
        return

    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    full_name = message.from_user.full_name
    chat_id = message.chat.id
    logger.info(f"Получена команда /start от пользователя {user_id} ({username})")

    # Проверяем подписку перед регистрацией
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(message, user_id, chat_id):
        return  # Пользователь заблокирован, сообщение уже отправлено

    args = message.text.split() if message.text else []
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id_str = args[1][4:]
        if referrer_id_str.isdigit() and int(referrer_id_str) != user_id:
            referrer_id = int(referrer_id_str)

    # Добавляем пользователя в базу данных
    is_new_user = await db.add_user(
        user_id, username, full_name, referrer_id, bot=message.bot
    )

    # Проверяем достижение "Первые шаги" для новых пользователей
    if is_new_user:
        try:
            await db.grant_achievement(user_id, "first_steps", message.bot)
        except Exception as e:
            logger.warning(
                f"Failed to grant first_steps achievement for user {user_id}: {e}"
            )

    if is_new_user and referrer_id:
        try:
            idem_key = f"ref-{user_id}-{referrer_id}"
            await db.add_balance_with_checks(
                referrer_id, settings.REFERRAL_BONUS, "referral_bonus", idem_key
            )
            # Проверяем достижение "Первопроходец" для реферера
            try:
                await db.grant_achievement(referrer_id, "first_referral", message.bot)
            except Exception as e:
                logger.warning(
                    f"Failed to grant first_referral achievement for user {referrer_id}: {e}"
                )

            # Проверяем достижение "Дружелюбный" (5 рефералов)
            try:
                referrals_count = await db.get_referrals_count(referrer_id)
                if referrals_count == 5:
                    await db.grant_achievement(referrer_id, "friendly", message.bot)
            except Exception as e:
                logger.warning(
                    f"Failed to grant friendly achievement for user {referrer_id}: {e}"
                )

            # Проверяем все достижения для реферера (включая уровни и ежедневные)
            try:
                await db.check_all_achievements(referrer_id, message.bot)
            except Exception as e:
                logger.warning(
                    f"Failed to check all achievements for user {referrer_id}: {e}"
                )

            # Получаем язык реферера для уведомления
            referrer_language = await db.get_user_language(referrer_id)
            await message.bot.send_message(
                referrer_id,
                get_text(
                    "referral_success_notification",
                    referrer_language,
                    bonus=settings.REFERRAL_BONUS,
                    username=username,
                ),
            )
            logger.info(
                f"Реферальный бонус {settings.REFERRAL_BONUS} отправлен {referrer_id} за нового пользователя {user_id}"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить реферальный бонус {referrer_id}: {e}")

    # Если это новый пользователь, показываем выбор языка
    if is_new_user:
        from keyboards.inline import language_selection_keyboard

        await message.answer(
            get_text("language_selection", "ru"),  # Показываем на русском по умолчанию
            reply_markup=language_selection_keyboard(),
        )
    else:
        # Для существующих пользователей показываем обычное приветствие
        from handlers.menu_handler import show_main_menu

        await show_main_menu(message.bot, message.chat.id, state=state)


@router.message(F.text == "▶️ Старт")
async def text_start(message: Message, state: FSMContext):
    """Обработчик для кнопки '▶️ Старт'."""
    # Проверка подписки уже встроена в command_start
    await command_start(message, state)


@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message, state: FSMContext):
    """Обработчик для кнопки настроек."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    user_language = await db.get_user_language(user_id)

    # Показываем настройки языка

    from keyboards.inline import language_settings_keyboard
    from lexicon.languages import get_language_name

    text = get_text("settings_menu", user_language)
    current_lang_name = get_language_name(user_language)
    current_lang_text = get_text(
        "current_language", user_language, language=current_lang_name
    )

    full_text = f"{text}\n\n{current_lang_text}"

    await message.answer_photo(
        photo=settings.PHOTO_PROFILE,
        caption=full_text,
        reply_markup=language_settings_keyboard(user_language),
        parse_mode="Markdown",
    )


@router.callback_query(UserCallback.filter(F.action == "enter_promo"))
async def enter_promo_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromoCodeStates.waiting_for_promo_code)
    if callback.message:
        user_language = await db.get_user_language(callback.from_user.id)
        media = InputMediaPhoto(
            media=settings.PHOTO_PROMO, caption=get_text("promo_prompt", user_language)
        )
        await safe_edit_media(
            callback.bot,
            media=media,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=promo_back_keyboard(user_language),
        )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "transactions"))
async def transactions_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа истории транзакций пользователя."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id

    # Получаем текущий баланс и историю транзакций
    balance = await db.get_user_balance(user_id)
    user_language = await db.get_user_language(user_id)
    transactions = await db.get_user_transactions_history(user_id, limit=15)

    if not transactions:
        # Если транзакций нет
        text = get_text("transactions_empty", user_language, balance=balance)
    else:
        # Формируем список транзакций
        text = get_text("transactions_title", user_language, balance=balance)

        for transaction in transactions:
            # Форматируем дату
            created_at = transaction["created_at"]
            if isinstance(created_at, str):
                # Если это строка, парсим её
                try:
                    # Пробуем разные форматы
                    if "T" in created_at:
                        # ISO формат
                        date_obj = datetime.datetime.fromisoformat(
                            created_at.replace("Z", "+00:00")
                        )
                    else:
                        # Формат "YYYY-MM-DD HH:MM:SS"
                        date_obj = datetime.datetime.strptime(
                            created_at, "%Y-%m-%d %H:%M:%S"
                        )
                except Exception:
                    date_obj = datetime.datetime.now()
            else:
                # Если это число (timestamp)
                date_obj = datetime.datetime.fromtimestamp(created_at)
            date_str = date_obj.strftime("%d.%m.%Y %H:%M")

            # Определяем эмодзи и текст в зависимости от типа операции
            amount = transaction["amount"]
            reason = transaction["reason"]

            if amount > 0:
                emoji = "💰"
                amount_text = f"+{amount} ⭐"
            else:
                emoji = "💸"
                amount_text = f"{amount} ⭐"

            # Переводим причину операции на русский
            reason_text = get_transaction_reason_text(reason)

            text += get_text(
                "transaction_item",
                user_language,
                emoji=emoji,
                amount_text=amount_text,
                reason_text=reason_text,
                date=date_str,
            )

    await safe_edit_caption(
        callback.bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=back_to_profile_keyboard(user_language),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "daily_challenges"))
async def daily_challenges_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа ежедневных челленджей (заглушка)."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    user_language = await db.get_user_language(user_id)

    # Показываем заглушку вместо реальных челленджей
    text = get_text("challenges_stub", user_language)

    await safe_edit_caption(
        callback.bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=daily_challenges_keyboard(user_language),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "social_content"))
async def social_content_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа меню социального контента."""
    if not callback.from_user or not callback.message:
        return

    user_language = await db.get_user_language(callback.from_user.id)
    text = get_text("social_content", user_language)

    media = InputMediaPhoto(
        media=settings.PHOTO_PROFILE, caption=text, parse_mode="Markdown"
    )

    await safe_edit_media(
        callback.bot,
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=social_content_keyboard(user_language),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "tiktok_content"))
async def tiktok_content_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа контента для TikTok."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    user_language = await db.get_user_language(user_id)
    balance = await db.get_user_balance(user_id)
    ref_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user_id}"

    text = get_text("tiktok_content", user_language, balance=balance, ref_link=ref_link)

    media = InputMediaPhoto(
        media=settings.PHOTO_PROFILE, caption=text, parse_mode="Markdown"
    )

    await safe_edit_media(
        callback.bot,
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=social_content_keyboard(user_language),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "instagram_content"))
async def instagram_content_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа контента для Instagram."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    user_language = await db.get_user_language(user_id)
    balance = await db.get_user_balance(user_id)
    ref_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user_id}"

    text = get_text(
        "instagram_content", user_language, balance=balance, ref_link=ref_link
    )

    media = InputMediaPhoto(
        media=settings.PHOTO_PROFILE, caption=text, parse_mode="Markdown"
    )

    await safe_edit_media(
        callback.bot,
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=social_content_keyboard(user_language),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "telegram_content"))
async def telegram_content_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа контента для Telegram."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    user_language = await db.get_user_language(user_id)
    balance = await db.get_user_balance(user_id)
    ref_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user_id}"

    text = get_text(
        "telegram_content", user_language, balance=balance, ref_link=ref_link
    )

    media = InputMediaPhoto(
        media=settings.PHOTO_PROFILE, caption=text, parse_mode="Markdown"
    )

    await safe_edit_media(
        callback.bot,
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=social_content_keyboard(user_language),
    )
    await callback.answer()


def get_transaction_reason_text(reason: str) -> str:
    """Переводит причину транзакции на русский язык."""
    reason_translations = {
        "referral_bonus": "Бонус за приглашение",
        "daily_bonus": "Ежедневный бонус",
        "passive_income": "Пассивный доход",
        "promo_activation": "Активация промокода",
        "duel_win": "Победа в дуэли",
        "duel_loss": "Поражение в дуэли",
        "duel_boost": "Усиление карты в дуэли",
        "duel_reroll": "Смена руки в дуэли",
        "duel_stake_hold": "Ставка в дуэли",
        "coinflip_win": "Победа в орел/решка",
        "coinflip_loss": "Поражение в орел/решка",
        "slots_win": "Выигрыш в слотах",
        "slots_loss": "Проигрыш в слотах",
        "dice_win": "Победа в кубиках",
        "dice_loss": "Поражение в кубиках",
        "bowling_win": "Победа в боулинге",
        "bowling_loss": "Поражение в боулинге",
        "basketball_win": "Победа в баскетболе",
        "basketball_loss": "Поражение в баскетболе",
        "football_win": "Победа в футболе",
        "football_loss": "Поражение в футболе",
        "darts_win": "Победа в дартс",
        "darts_loss": "Поражение в дартс",
        "timer_win": "Победа в таймере",
        "timer_loss": "Поражение в таймере",
        "reward_request": "Заявка на вывод",
        "admin_adjustment": "Корректировка администратора",
        "admin_grant": "Начисление администратора",
        "level_up_bonus": "Бонус за повышение уровня",
        "streak_bonus": "Бонус за стрик",
        "daily_challenge": "Ежедневный челлендж",
    }
    return reason_translations.get(reason, reason)


@router.message(Command("promo"))
async def promo_command(message: Message, state: FSMContext):
    if not message.from_user:
        return

    # Проверяем подписку перед показом промо
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        message, message.from_user.id, message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    user_language = await db.get_user_language(message.from_user.id)
    await state.set_state(PromoCodeStates.waiting_for_promo_code)
    await message.answer(
        get_text("promo_prompt", user_language),
        reply_markup=promo_back_keyboard(user_language),
    )


@router.message(StateFilter(PromoCodeStates.waiting_for_promo_code), F.text)
async def process_promo_code(message: Message, state: FSMContext):
    await state.clear()
    promo_code = message.text or ""
    if not message.from_user:
        return
    user_id = message.from_user.id
    idem_key = f"promo-{user_id}-{promo_code}-{uuid.uuid4()}"

    user_language = await db.get_user_language(user_id)
    try:
        result = await db.activate_promo(user_id, promo_code, idem_key)
        if isinstance(result, int):
            # Проверяем достижение "Взломщик кодов" при успешной активации промокода
            try:
                await db.grant_achievement(user_id, "code_breaker", message.bot)
            except Exception as e:
                logger.warning(
                    f"Failed to grant code_breaker achievement for user {user_id}: {e}"
                )

            # Проверяем все достижения связанные с промокодами
            try:
                await db.check_promo_achievements(user_id, message.bot)
            except Exception as e:
                logger.warning(
                    f"Failed to check promo achievements for user {user_id}: {e}"
                )

            await message.answer(
                get_text("promo_success", user_language, amount=result),
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            await message.answer(
                get_text("promo_fail", user_language, reason=result),
                reply_markup=get_main_menu_keyboard(),
            )
    except Exception as e:
        logger.error(
            f"Ошибка при обработке промокода '{promo_code}' для пользователя {user_id}: {e}"
        )
        await message.answer(
            get_text(
                "promo_fail", user_language, reason="Произошла внутренняя ошибка."
            ),
            reply_markup=get_main_menu_keyboard(),
        )


# --- ОБРАБОТЧИКИ ВЫВОДА ПОДАРКОВ ---


@router.callback_query(GiftCallback.filter(F.action == "select"))
async def select_gift_handler(
    callback: CallbackQuery, callback_data: GiftCallback, bot: Bot
):
    """Показывает подтверждение для вывода подарка."""
    item_id = callback_data.item_id
    cost = callback_data.cost

    gift = next((g for g in GIFTS_CATALOG if g["id"] == item_id), None)
    if not gift:
        await callback.answer("Подарок не найден!", show_alert=True)
        return

    user_language = await db.get_user_language(callback.from_user.id)
    text = get_text(
        "gift_confirm", user_language, cost=cost, emoji=gift["emoji"], name=gift["name"]
    )

    if callback.message:
        await safe_edit_caption(
            bot,
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=gift_confirm_keyboard(item_id, cost),
        )
    await callback.answer()


@router.callback_query(GiftCallback.filter(F.action == "confirm"))
async def confirm_gift_handler(
    callback: CallbackQuery, callback_data: GiftCallback, bot: Bot
):
    """Обрабатывает подтверждение вывода и создает заявку."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    item_id = callback_data.item_id
    cost = callback_data.cost

    # 1. Проверка баланса
    balance = await db.get_user_balance(user_id)
    if balance < cost:
        await callback.answer("У вас недостаточно средств.", show_alert=True)
        return

    # 2. Проверка количества рефералов
    referrals_count = await db.get_referrals_count(user_id)
    user_language = await db.get_user_language(user_id)
    if referrals_count < settings.MIN_REFERRALS_FOR_WITHDRAW:
        error_text = get_text(
            "error_not_enough_referrals",
            user_language,
            min_refs=settings.MIN_REFERRALS_FOR_WITHDRAW,
            current_refs=referrals_count,
        )
        await callback.answer(error_text, show_alert=True)
        return

    # 3. Проверка подписки на канал через SubGram
    from handlers.subscription_checker import check_subscription_silent

    if not await check_subscription_silent(user_id, callback.message.chat.id):
        await callback.answer(
            "Для вывода необходимо подписаться на каналы. Используйте /start для проверки подписки.",
            show_alert=True,
        )
        return

    # Все проверки пройдены, создаем заявку
    idem_key = f"reward-{user_id}-{item_id}-{uuid.uuid4()}"
    result = await db.create_reward_request(user_id, item_id, cost, idem_key)

    if result.get("success"):
        gift = next((g for g in GIFTS_CATALOG if g["id"] == item_id), None)
        if gift:
            success_text = get_text(
                "withdrawal_success",
                user_language,
                emoji=gift["emoji"],
                name=gift["name"],
                amount=cost,
            )
            await safe_edit_caption(
                bot,
                success_text,
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=back_to_menu_keyboard(),
            )
            await callback.answer("✅ Заявка создана!", show_alert=True)
    else:
        reason = result.get("reason", "unknown_error")
        await callback.answer(
            f"Не удалось создать заявку. Ошибка: {reason}", show_alert=True
        )


@router.message(F.text == "❌ Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    user_language = await db.get_user_language(message.from_user.id)
    await state.clear()
    await message.answer(
        get_text("cancel", user_language), reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("id"))
async def get_id(message: Message):
    if not message.from_user:
        return

    # Проверяем подписку перед показом ID
    from handlers.subscription_checker import check_subscription_and_block

    if not await check_subscription_and_block(
        message, message.from_user.id, message.chat.id
    ):
        return  # Пользователь заблокирован, сообщение уже отправлено

    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id
    await message.answer(
        f"Твой ID: <code>{user_id}</code>\n"
        f"Твой юзернейм: @{username}\n"
        f"ID чата: <code>{chat_id}</code>"
    )
