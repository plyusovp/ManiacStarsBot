# handlers/bowling_handlers.py

import asyncio
import uuid
from typing import Dict

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_edit_caption, safe_send_message
from keyboards.factories import BowlingCallback, GameCallback
from keyboards.inline import bowling_play_again_keyboard, bowling_stake_keyboard
from lexicon.texts import LEXICON

router = Router()

# Новая экономика: ставка -> выигрыш
BOWLING_PRIZES: Dict[int, int] = {
    1: 5,
    3: 15,
    5: 25,
    10: 50,
}


@router.callback_query(GameCallback.filter((F.name == "bowling") & (F.action == "start")))
async def bowling_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает главное меню игры 'Боулинг' с выбором ставки."""
    await state.clear()
    if not callback.message or not callback.from_user:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    # Используем правильный текст из lexicon, который не требует 'cost'
    text = LEXICON["bowling_menu"].format(balance=balance)

    # Меняем старое сообщение на меню с кнопками выбора ставок
    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=bowling_stake_keyboard(),
    )
    await callback.answer()


@router.callback_query(BowlingCallback.filter(F.action == "throw"))
async def throw_bowling_handler(callback: CallbackQuery, callback_data: BowlingCallback, bot: Bot):
    """Обрабатывает бросок шара по выбранной ставке."""
    if not callback.from_user or not callback.message:
        return

    stake = callback_data.value
    if stake is None or stake not in BOWLING_PRIZES:
        await callback.answer("Неверная ставка.", show_alert=True)
        return

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < stake:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    # Отвечаем на колбэк, чтобы кнопка не "висела"
    await callback.answer()

    # Списываем деньги за попытку
    idem_key = f"bowling-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, stake, "bowling_throw_cost", idem_key=idem_key
    )
    if not spent:
        await safe_send_message(user_id, "Не удалось списать ставку, попробуйте снова.")
        return

    # Отправляем эмодзи боулинга
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎳")

    # Ждем завершения анимации
    await asyncio.sleep(4)

    # Значение 6 означает страйк
    is_win = msg.dice and msg.dice.value == 6
    win_amount = BOWLING_PRIZES[stake]

    if is_win:
        await db.add_balance_unrestricted(user_id, win_amount, "bowling_win")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["bowling_win"].format(
            prize=win_amount, new_balance=new_balance
        )
    else:
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["bowling_lose"].format(
            cost=stake, new_balance=new_balance
        )

    # Отправляем новое сообщение с результатом и кнопкой "Играть снова"
    await bot.send_message(
        user_id, result_text, reply_markup=bowling_play_again_keyboard()
    )
    