# handlers/basketball_handlers.py

import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from config import settings
from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import BasketballCallback, GameCallback
from keyboards.inline import basketball_stake_keyboard
from lexicon.texts import LEXICON

router = Router()
WIN_MULTIPLIER = 2.5


@router.callback_query(
    GameCallback.filter((F.name == "basketball") & (F.action == "start"))
)
async def basketball_menu_handler(callback: CallbackQuery, bot: Bot):
    """Отображает главное меню игры 'Баскетбол' с выбором ставки."""
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    user_language = await db.get_user_language(callback.from_user.id)
    text = LEXICON["basketball_menu"].format(balance=balance)

    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=basketball_stake_keyboard(user_language),
        photo=settings.PHOTO_BASKETBALL,
    )
    await callback.answer()


@router.callback_query(BasketballCallback.filter(F.action == "throw"))
async def throw_basketball_handler(
    callback: CallbackQuery, callback_data: BasketballCallback, bot: Bot
):
    """Обрабатывает бросок мяча по выбранной ставке."""
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

    idem_key = f"basketball-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, stake, "basketball_throw_cost", idem_key=idem_key
    )
    if not spent:
        new_balance = await db.get_user_balance(user_id)
        error_text = "Не удалось списать ставку, попробуйте снова."
        menu_text = LEXICON["basketball_menu"].format(balance=new_balance)
        await bot.send_photo(
            user_id,
            settings.PHOTO_BASKETBALL,
            caption=f"{error_text}\n\n{menu_text}",
            reply_markup=basketball_stake_keyboard(user_language),
        )
        return

    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🏀")
    await asyncio.sleep(4)

    # Попадание при значениях 4 и 5
    winning_values = {4, 5}
    is_win = msg.dice and msg.dice.value in winning_values

    new_balance = await db.get_user_balance(user_id)

    if is_win:
        win_amount = int(stake * WIN_MULTIPLIER)
        await db.add_balance_unrestricted(user_id, win_amount, "basketball_win")
        new_balance += win_amount
        result_text = LEXICON["basketball_win"].format(
            prize=win_amount, new_balance=new_balance
        )
    else:
        result_text = LEXICON["basketball_lose"].format(
            cost=stake, new_balance=new_balance
        )
    
    # Записываем, что пользователь играл в баскетбол
    await db.record_game_play(user_id, "basketball")

    menu_text = LEXICON["basketball_menu"].format(balance=new_balance)
    final_text = f"{result_text}\n\n{menu_text}"
    await bot.send_photo(
        user_id,
        settings.PHOTO_BASKETBALL,
        caption=final_text,
        reply_markup=basketball_stake_keyboard(user_language),
    )
