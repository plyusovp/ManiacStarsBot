# plyusovp/maniacstarsbot/ManiacStarsBot-68ffe9d3e979f3cc61bcf924e4b9ab182d77be5f/handlers/user_handlers.py

import datetime
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ContentType, InputMediaPhoto, Message

from config import settings
from database import db
from gifts import GIFTS_CATALOG
from handlers.utils import check_subscription, safe_edit_caption, safe_edit_media
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
from lexicon.texts import LEXICON, LEXICON_ERRORS

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
    logger.info(f"Получена команда /start от пользователя {user_id} ({username})")

    args = message.text.split() if message.text else []
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id_str = args[1][4:]
        if referrer_id_str.isdigit() and int(referrer_id_str) != user_id:
            referrer_id = int(referrer_id_str)

    is_new_user = await db.add_user(user_id, username, full_name, referrer_id)

    if is_new_user and referrer_id:
        try:
            idem_key = f"ref-{user_id}-{referrer_id}"
            await db.add_balance_with_checks(
                referrer_id, settings.REFERRAL_BONUS, "referral_bonus", idem_key
            )
            await message.bot.send_message(
                referrer_id,
                LEXICON["referral_success_notification"].format(
                    bonus=settings.REFERRAL_BONUS, username=username
                ),
            )
            logger.info(
                f"Реферальный бонус {settings.REFERRAL_BONUS} отправлен {referrer_id} за нового пользователя {user_id}"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить реферальный бонус {referrer_id}: {e}")

    await message.answer(
        LEXICON["start_message"].format(full_name=message.from_user.full_name),
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text == "▶️ Старт")
async def text_start(message: Message, state: FSMContext):
    """Обработчик для кнопки '▶️ Старт'."""
    await command_start(message, state)


@router.callback_query(UserCallback.filter(F.action == "enter_promo"))
async def enter_promo_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromoCodeStates.waiting_for_promo_code)
    if callback.message:
        await safe_edit_caption(
            callback.bot,
            caption=LEXICON["promo_prompt"],
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=promo_back_keyboard(),
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
    transactions = await db.get_user_transactions_history(user_id, limit=15)

    if not transactions:
        # Если транзакций нет
        text = LEXICON["transactions_empty"].format(balance=balance)
    else:
        # Формируем список транзакций
        text = LEXICON["transactions_title"].format(balance=balance)

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

            text += LEXICON["transaction_item"].format(
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
        reply_markup=back_to_profile_keyboard(),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "daily_challenges"))
async def daily_challenges_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа ежедневных челленджей."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id

    # Получаем количество рефералов за сегодня
    today_referrals = await db.get_daily_referrals_count(user_id)

    text = LEXICON["daily_challenges"].format(today_referrals=today_referrals)

    await safe_edit_caption(
        callback.bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=daily_challenges_keyboard(),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "social_content"))
async def social_content_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа меню социального контента."""
    if not callback.from_user or not callback.message:
        return

    text = LEXICON["social_content"]

    media = InputMediaPhoto(
        media=settings.PHOTO_PROFILE, caption=text, parse_mode="Markdown"
    )

    await safe_edit_media(
        callback.bot,
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=social_content_keyboard(),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "tiktok_content"))
async def tiktok_content_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа контента для TikTok."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    ref_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user_id}"

    text = LEXICON["tiktok_content"].format(balance=balance, ref_link=ref_link)

    media = InputMediaPhoto(
        media=settings.PHOTO_PROFILE, caption=text, parse_mode="Markdown"
    )

    await safe_edit_media(
        callback.bot,
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=social_content_keyboard(),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "instagram_content"))
async def instagram_content_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа контента для Instagram."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    ref_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user_id}"

    text = LEXICON["instagram_content"].format(balance=balance, ref_link=ref_link)

    media = InputMediaPhoto(
        media=settings.PHOTO_PROFILE, caption=text, parse_mode="Markdown"
    )

    await safe_edit_media(
        callback.bot,
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=social_content_keyboard(),
    )
    await callback.answer()


@router.callback_query(UserCallback.filter(F.action == "telegram_content"))
async def telegram_content_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик для показа контента для Telegram."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    ref_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user_id}"

    text = LEXICON["telegram_content"].format(balance=balance, ref_link=ref_link)

    media = InputMediaPhoto(
        media=settings.PHOTO_PROFILE, caption=text, parse_mode="Markdown"
    )

    await safe_edit_media(
        callback.bot,
        media=media,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=social_content_keyboard(),
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
    await state.set_state(PromoCodeStates.waiting_for_promo_code)
    await message.answer(LEXICON["promo_prompt"], reply_markup=promo_back_keyboard())


@router.message(StateFilter(PromoCodeStates.waiting_for_promo_code), F.text)
async def process_promo_code(message: Message, state: FSMContext):
    await state.clear()
    promo_code = message.text or ""
    if not message.from_user:
        return
    user_id = message.from_user.id
    idem_key = f"promo-{user_id}-{promo_code}-{uuid.uuid4()}"

    try:
        result = await db.activate_promo(user_id, promo_code, idem_key)
        if isinstance(result, int):
            await message.answer(
                LEXICON["promo_success"].format(amount=result),
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            await message.answer(
                LEXICON["promo_fail"].format(reason=result),
                reply_markup=get_main_menu_keyboard(),
            )
    except Exception as e:
        logger.error(
            f"Ошибка при обработке промокода '{promo_code}' для пользователя {user_id}: {e}"
        )
        await message.answer(
            LEXICON["promo_fail"].format(reason="Произошла внутренняя ошибка."),
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

    text = LEXICON["gift_confirm"].format(
        cost=cost, emoji=gift["emoji"], name=gift["name"]
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

    # 2. Проверка количества рефералов (пропускаем для админов)
    if user_id not in settings.ADMIN_IDS:
        referrals_count = await db.get_referrals_count(user_id)
        if referrals_count < settings.MIN_REFERRALS_FOR_WITHDRAW:
            error_text = LEXICON_ERRORS["error_not_enough_referrals"].format(
                min_refs=settings.MIN_REFERRALS_FOR_WITHDRAW,
                current_refs=referrals_count,
            )
            await callback.answer(error_text, show_alert=True)
            return

    # 3. Проверка подписки на канал
    is_subscribed = await check_subscription(bot, user_id)
    if not is_subscribed:
        await callback.answer(LEXICON_ERRORS["error_not_subscribed"], show_alert=True)
        return

    # Все проверки пройдены, создаем заявку
    idem_key = f"reward-{user_id}-{item_id}-{uuid.uuid4()}"
    result = await db.create_reward_request(user_id, item_id, cost, idem_key)

    if result.get("success"):
        gift = next((g for g in GIFTS_CATALOG if g["id"] == item_id), None)
        if gift:
            success_text = LEXICON["withdrawal_success"].format(
                emoji=gift["emoji"], name=gift["name"], amount=cost
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
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=get_main_menu_keyboard())


@router.message(Command("id"))
async def get_id(message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id
    await message.answer(
        f"Твой ID: <code>{user_id}</code>\n"
        f"Твой юзернейм: @{username}\n"
        f"ID чата: <code>{chat_id}</code>"
    )


