# plyusovp/maniacstarsbot/ManiacStarsBot-68ffe9d3e979f3cc61bcf924e4b9ab182d77be5f/handlers/user_handlers.py

import logging
import uuid

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import settings
from database import db
from gifts import GIFTS_CATALOG
from handlers.utils import check_subscription, safe_edit_caption
from keyboards.factories import GiftCallback, UserCallback
from keyboards.inline import (
    back_to_menu_keyboard,
    gift_confirm_keyboard,
    promo_back_keyboard,
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

    # 2. Проверка количества рефералов
    referrals_count = await db.get_referrals_count(user_id)
    if referrals_count < settings.MIN_REFERRALS_FOR_WITHDRAW:
        error_text = LEXICON_ERRORS["error_not_enough_referrals"].format(
            min_refs=settings.MIN_REFERRALS_FOR_WITHDRAW, current_refs=referrals_count
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
    