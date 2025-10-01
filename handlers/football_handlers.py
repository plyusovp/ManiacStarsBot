# handlers/football_handlers.py

import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import FootballCallback, GameCallback
from keyboards.inline import football_stake_keyboard
from lexicon.texts import LEXICON

router = Router()
WIN_MULTIPLIER = 2.5


@router.callback_query(
    GameCallback.filter((F.name == "football") & (F.action == "start"))
)
async def football_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает главное меню игры 'Футбол' с выбором ставки."""
    await state.clear()
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["football_menu"].format(balance=balance)

    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=football_stake_keyboard(),
    )
    await callback.answer()


@router.callback_query(FootballCallback.filter(F.action == "kick"))
async def kick_football_handler(
    callback: CallbackQuery,
    callback_data: FootballCallback,
    bot: Bot,
    state: FSMContext,
):
    """Обрабатывает удар по мячу по выбранной ставке."""
    if not callback.from_user or not callback.message:
        return

    stake_from_callback = callback_data.value
    if stake_from_callback is None:
        await callback.answer("Неверная ставка.", show_alert=True)
        return

    stake = int(stake_from_callback)
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < stake:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    await callback.answer()
    await safe_delete(bot, callback.message.chat.id, callback.message.message_id)

    idem_key = f"football-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, stake, "football_kick_cost", idem_key=idem_key
    )
    if not spent:
        new_balance = await db.get_user_balance(user_id)
        error_text = "Не удалось списать ставку, попробуйте снова."
        menu_text = LEXICON["football_menu"].format(balance=new_balance)
        await bot.send_message(
            user_id,
            f"{error_text}\n\n{menu_text}",
            reply_markup=football_stake_keyboard(),
        )
        return

    msg: Message = await bot.send_dice(chat_id=user_id, emoji="⚽️")
    await asyncio.sleep(4)

    # Гол при значениях 4 и 5
    winning_values = {4, 5}
    is_win = msg.dice and msg.dice.value in winning_values

    new_balance = await db.get_user_balance(user_id)

    if is_win:
        win_amount = int(stake * WIN_MULTIPLIER)
        await db.add_balance_unrestricted(user_id, win_amount, "football_win")
        new_balance += win_amount
        result_text = LEXICON["football_win"].format(
            prize=win_amount, new_balance=new_balance
        )
    else:
        result_text = LEXICON["football_lose"].format(
            cost=stake, new_balance=new_balance
        )

    menu_text = LEXICON["football_menu"].format(balance=new_balance)
    final_text = f"{result_text}\n\n{menu_text}"
    await bot.send_message(user_id, final_text, reply_markup=football_stake_keyboard())
