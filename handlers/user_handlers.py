# plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/handlers/user_handlers.py

import logging
import uuid

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import settings
from database import db
from keyboards.inline import promo_back_keyboard
from keyboards.reply import get_main_menu_keyboard

# ИСПРАВЛЕНИЕ: Импортируем словарь LEXICON, а не несуществующий класс Lexicon
from lexicon.texts import LEXICON

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
    logger.info(f"/start command received from user {user_id} ({username})")

    args = message.text.split() if message.text else []
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id_str = args[1][4:]
        if referrer_id_str.isdigit() and int(referrer_id_str) != user_id:
            referrer_id = int(referrer_id_str)

    is_new_user = await db.add_user(user_id, username, full_name, referrer_id)

    if is_new_user and referrer_id:
        try:
            # Создаем уникальный ключ для этой конкретной операции
            idem_key = f"ref-{user_id}-{referrer_id}"
            await db.add_balance_with_checks(
                referrer_id, settings.REFERRAL_BONUS, "referral_bonus", idem_key
            )
            # ИСПРАВЛЕНИЕ: Используем правильный синтаксис для доступа к словарю и верный ключ
            await message.bot.send_message(
                referrer_id,
                LEXICON["referral_success_notification"].format(
                    bonus=settings.REFERRAL_BONUS, username=username
                ),
            )
            logger.info(
                f"Referral bonus {settings.REFERRAL_BONUS} sent to {referrer_id} for new user {user_id}"
            )
        except Exception as e:
            logger.error(f"Failed to send referral bonus to {referrer_id}: {e}")

    # ИСПРАВЛЕНИЕ: Используем правильный ключ "start_message" и переменную full_name
    await message.answer(
        LEXICON["start_message"].format(full_name=message.from_user.full_name),
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text == "▶️ Старт")
async def text_start(message: Message, state: FSMContext):
    """Handler for the '▶️ Старт' button."""
    await command_start(message, state)


@router.message(Command("promo"))
async def promo_command(message: Message, state: FSMContext):
    await state.set_state(PromoCodeStates.waiting_for_promo_code)
    # ИСПРАВЛЕНИЕ: Используем правильный ключ "promo_prompt"
    await message.answer(LEXICON["promo_prompt"], reply_markup=promo_back_keyboard())


@router.message(F.text, StateFilter(PromoCodeStates.waiting_for_promo_code))
async def process_promo_code(message: Message, state: FSMContext):
    await state.clear()
    promo_code = message.text or ""
    if not message.from_user:
        return
    user_id = message.from_user.id
    # Создаем уникальный ключ для этой конкретной операции
    idem_key = f"promo-{user_id}-{promo_code}-{uuid.uuid4()}"

    try:
        # В db.activate_promo возвращается кортеж, а не одно значение.
        # Возвращает: "not_found", "already_activated", "error" или amount
        result = await db.activate_promo(user_id, promo_code, idem_key)

        if isinstance(result, int):  # Успешная активация, если вернулось число
            await message.answer(
                # ИСПРАВЛЕНИЕ: Используем новый ключ "promo_success"
                LEXICON["promo_success"].format(amount=result),
                reply_markup=get_main_menu_keyboard(),
            )
        else:  # Если вернулась строка с ошибкой
            await message.answer(
                # ИСПРАВЛЕНИЕ: Используем новый ключ "promo_fail"
                LEXICON["promo_fail"].format(reason=result),
                reply_markup=get_main_menu_keyboard(),
            )
    except Exception as e:
        logger.error(
            f"Error processing promo code '{promo_code}' for user {user_id}: {e}"
        )
        await message.answer(
            LEXICON["promo_fail"].format(reason="Произошла внутренняя ошибка."),
            reply_markup=get_main_menu_keyboard(),
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
    