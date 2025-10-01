# handlers/bowling_handlers.py

import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import BowlingCallback, GameCallback
from keyboards.inline import bowling_stake_keyboard
from lexicon.texts import LEXICON

router = Router()


@router.callback_query(
    GameCallback.filter((F.name == "bowling") & (F.action == "start"))
)
async def bowling_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает главное меню игры 'Боулинг' с выбором ставки."""
    await state.clear()
    if not callback.message or not callback.from_user:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["bowling_menu"].format(balance=balance)

    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=bowling_stake_keyboard(),
    )
    await callback.answer()


@router.callback_query(BowlingCallback.filter(F.action == "throw"))
async def throw_bowling_handler(
    callback: CallbackQuery, callback_data: BowlingCallback, bot: Bot
):
    """Обрабатывает бросок шара по выбранной ставке."""
    if not callback.from_user or not callback.message:
        return

    stake_value = callback_data.value
    if stake_value is None:
        await callback.answer("Неверная ставка.", show_alert=True)
        return

    stake = int(stake_value)
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < stake:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    await callback.answer()
    await safe_delete(bot, callback.message.chat.id, callback.message.message_id)

    idem_key = f"bowling-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, stake, "bowling_throw_cost", idem_key=idem_key
    )
    if not spent:
        new_balance = await db.get_user_balance(user_id)
        error_text = "Не удалось списать ставку, попробуйте снова."
        menu_text = LEXICON["bowling_menu"].format(balance=new_balance)
        await bot.send_message(
            user_id,
            f"{error_text}\n\n{menu_text}",
            reply_markup=bowling_stake_keyboard(),
        )
        return

    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎳")
    await asyncio.sleep(4)

    dice_value = msg.dice.value if msg.dice else 0
    win_amount: int = 0  # Инициализируем как int

    if dice_value == 6:  # Strike
        win_amount = stake * 3
    elif dice_value == 5:  # 1 pin left
        # ИСПРАВЛЕНИЕ: Преобразуем float в int
        win_amount = int(stake * 1.5)

    new_balance = await db.get_user_balance(user_id)

    if win_amount > 0:
        await db.add_balance_unrestricted(user_id, win_amount, "bowling_win")
        new_balance += win_amount
        result_text = LEXICON["bowling_win"].format(
            prize=win_amount, new_balance=new_balance
        )
    else:
        result_text = LEXICON["bowling_lose"].format(
            cost=stake, new_balance=new_balance
        )

    menu_text = LEXICON["bowling_menu"].format(balance=new_balance)
    final_text = f"{result_text}\n\n{menu_text}"
    await bot.send_message(user_id, final_text, reply_markup=bowling_stake_keyboard())
