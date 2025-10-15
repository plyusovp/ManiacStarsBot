# handlers/slots_handlers.py

import asyncio
import uuid
from typing import Tuple

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import GameCallback, SlotsCallback
from keyboards.inline import slots_stake_keyboard
from lexicon.texts import LEXICON

router = Router()


def get_reels_from_dice(value: int) -> Tuple[int, int, int]:
    """
    Разбирает значение дайса "🎰" (от 1 до 64) на три барабана.
    Символы: 0: BAR, 1: Grapes, 2: Lemon, 3: Seven
    """
    val = value - 1
    reel1 = val % 4
    reel2 = (val // 4) % 4
    reel3 = (val // 16) % 4
    return reel1, reel2, reel3


@router.callback_query(GameCallback.filter((F.name == "slots") & (F.action == "start")))
async def slots_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает или обновляет главное меню слотов с выбором ставки."""
    await state.clear()
    if not callback.message or not callback.from_user:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    user_language = await db.get_user_language(callback.from_user.id)
    text = LEXICON["slots_menu"].format(balance=balance)

    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=slots_stake_keyboard(user_language),
        photo=settings.PHOTO_SLOTS,
    )
    await callback.answer()


@router.callback_query(SlotsCallback.filter(F.action == "spin"))
async def spin_slots_handler(
    callback: CallbackQuery, callback_data: SlotsCallback, bot: Bot
):
    """Обрабатывает вращение и присылает новое сообщение с результатом и кнопками."""
    if not callback.from_user or not callback.message:
        return

    stake_from_callback = callback_data.value
    if stake_from_callback is None:
        await callback.answer("Неверная ставка.", show_alert=True)
        return

    stake = int(stake_from_callback)
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    user_language = await db.get_user_language(user_id)

    if balance < stake:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    await callback.answer()
    await safe_delete(bot, callback.message.chat.id, callback.message.message_id)

    idem_key = f"slots-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(user_id, stake, "slots_spin_cost", idem_key=idem_key)
    if not spent:
        new_balance = await db.get_user_balance(user_id)
        error_text = "Не удалось списать ставку, попробуйте снова."
        menu_text = LEXICON["slots_menu"].format(balance=new_balance)
        await bot.send_photo(
            user_id,
            settings.PHOTO_SLOTS,
            caption=f"{error_text}\n\n{menu_text}",
            reply_markup=slots_stake_keyboard(user_language),
        )
        return

    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎰")
    await asyncio.sleep(2)

    dice_value = msg.dice.value if msg.dice else 0
    reel1, reel2, reel3 = get_reels_from_dice(dice_value)
    symbol_seven = 3

    win_amount: int = 0  # Инициализируем как int
    result_text_key = "slots_lose"

    if reel1 == reel2 == reel3:
        if reel1 == symbol_seven:
            # Три семерки
            win_amount = stake * 7
            result_text_key = "slots_win"
        else:
            # Три одинаковых (не семерки)
            win_amount = stake * 2
            result_text_key = "slots_win"
    elif reel1 == reel2 or reel2 == reel3:
        # Два одинаковых подряд
        # ИСПРАВЛЕНИЕ: Преобразуем float в int
        win_amount = int(stake * 1.5)
        result_text_key = "slots_two_match"

    new_balance = await db.get_user_balance(user_id)

    if win_amount > 0:
        await db.add_balance_unrestricted(user_id, win_amount, "slots_win")
        new_balance += win_amount
        result_text = LEXICON[result_text_key].format(
            prize=win_amount, new_balance=new_balance
        )
    else:
        result_text = LEXICON["slots_lose"].format(cost=stake, new_balance=new_balance)

    menu_text = LEXICON["slots_menu"].format(balance=new_balance)
    final_text = f"{result_text}\n\n{menu_text}"

    await bot.send_photo(
        user_id,
        settings.PHOTO_SLOTS,
        caption=final_text,
        reply_markup=slots_stake_keyboard(user_language),
    )
