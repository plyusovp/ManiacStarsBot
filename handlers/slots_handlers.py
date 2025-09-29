# plyusovp/maniacstarsbot/ManiacStarsBot-67d43495a3d8b0b5689fd3311461f2c73499ed96/handlers/slots_handlers.py

import asyncio
import uuid
from typing import Dict, Tuple

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import GameCallback, SlotsCallback
from keyboards.inline import slots_stake_keyboard
from lexicon.texts import LEXICON

router = Router()

# Экономика: джекпот x12, два первых совпадения - возврат ставки
SLOTS_PRIZES: Dict[int, int] = {
    1: 12,
    3: 36,
    5: 60,
    10: 120,
}


def get_reels_from_dice(value: int) -> Tuple[int, int, int]:
    """
    Разбирает значение дайса "🎰" (от 0 до 63) на три барабана (от 0 до 3).
    """
    # Значения в aiogram для "🎰" начинаются с 1, а логика основана на 0-63.
    # Поэтому вычитаем 1.
    val = value - 1
    reel1 = val // 16
    reel2 = (val % 16) // 4
    reel3 = val % 4
    return reel1, reel2, reel3


@router.callback_query(GameCallback.filter((F.name == "slots") & (F.action == "start")))
async def slots_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает или обновляет главное меню слотов с выбором ставки."""
    await state.clear()
    if not callback.message or not callback.from_user:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["slots_menu"].format(balance=balance)

    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=slots_stake_keyboard(),
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
    if stake not in SLOTS_PRIZES:
        await callback.answer("Неверная ставка.", show_alert=True)
        return

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
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
        await bot.send_message(
            user_id, f"{error_text}\n\n{menu_text}", reply_markup=slots_stake_keyboard()
        )
        return

    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎰")
    await asyncio.sleep(2)

    dice_value = msg.dice.value if msg.dice else 0
    reel1, reel2, reel3 = get_reels_from_dice(dice_value)

    # Определяем результат: ПРОВЕРКА ПЕРВЫХ ДВУХ БАРАБАНОВ, БЛЯТЬ.
    is_jackpot = reel1 == reel2 == reel3
    is_two_match = reel1 == reel2 and reel1 != reel3

    if is_jackpot:
        win_amount = SLOTS_PRIZES[stake]
        await db.add_balance_unrestricted(user_id, win_amount, "slots_win_jackpot")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["slots_win"].format(
            prize=win_amount, new_balance=new_balance
        )
    elif is_two_match:
        # Возвращаем ставку
        win_amount = stake
        await db.add_balance_unrestricted(user_id, win_amount, "slots_win_return")
        new_balance = await db.get_user_balance(user_id)
        result_text = f"🤷‍♂️ Считай, что это был бесплатный спин. 🤷‍♂️\n\nВселенная даёт тебе ещё один шанс не быть лузером. Твоя ставка в {win_amount} ⭐ вернулась.\n💰 Ваш новый баланс: {new_balance} ⭐"
    else:
        # Проигрыш
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["slots_lose"].format(cost=stake, new_balance=new_balance)

    menu_text = LEXICON["slots_menu"].format(balance=new_balance)
    final_text = f"{result_text}\n\n{menu_text}"

    await bot.send_message(user_id, final_text, reply_markup=slots_stake_keyboard())