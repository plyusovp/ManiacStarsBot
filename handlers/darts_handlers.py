# handlers/darts_handlers.py

import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from config import settings
from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import DartsCallback, GameCallback
from keyboards.inline import darts_stake_keyboard
from lexicon.texts import LEXICON

router = Router()


@router.callback_query(GameCallback.filter((F.name == "darts") & (F.action == "start")))
async def darts_menu_handler(callback: CallbackQuery, bot: Bot):
    """Отображает главное меню игры 'Дартс' с выбором ставки."""
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    user_language = await db.get_user_language(callback.from_user.id)
    text = LEXICON["darts_menu"].format(balance=balance)

    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=darts_stake_keyboard(user_language),
        photo=settings.PHOTO_DARTS,
    )
    await callback.answer()


@router.callback_query(GameCallback.filter((F.name == "darts") & (F.action == "rules")))
async def darts_rules_handler(callback: CallbackQuery, bot: Bot):
    """Отображает правила игры 'Дартс'."""
    if not callback.message:
        return

    user_language = await db.get_user_language(callback.from_user.id)
    text = LEXICON["darts_rules"]

    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=darts_stake_keyboard(user_language),
        photo=settings.PHOTO_DARTS,
    )
    await callback.answer("📖 Правила игры")


@router.callback_query(DartsCallback.filter(F.action == "throw"))
async def throw_darts_handler(
    callback: CallbackQuery, callback_data: DartsCallback, bot: Bot
):
    """Обрабатывает бросок дротика по выбранной ставке."""
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

    idem_key = f"darts-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, stake, "darts_throw_cost", idem_key=idem_key
    )
    if not spent:
        new_balance = await db.get_user_balance(user_id)
        error_text = "Не удалось списать ставку, попробуйте снова."
        menu_text = LEXICON["darts_menu"].format(balance=new_balance)
        await bot.send_photo(
            user_id,
            settings.PHOTO_DARTS,
            caption=f"{error_text}\n\n{menu_text}",
            reply_markup=darts_stake_keyboard(user_language),
        )
        return

    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎯")
    await asyncio.sleep(4)

    dice_value = msg.dice.value if msg.dice else 0
    win_amount: int = 0  # Инициализируем как int

    if dice_value == 6:  # Bullseye
        win_amount = stake * 4
    elif dice_value == 5:  # Inner ring
        win_amount = stake * 2
    elif dice_value == 4:  # Outer ring
        # ИСПРАВЛЕНИЕ: Преобразуем float в int
        win_amount = int(stake * 1.5)

    new_balance = await db.get_user_balance(user_id)

    if win_amount > 0:
        await db.add_balance_unrestricted(user_id, win_amount, "darts_win")
        new_balance += win_amount
        result_text = LEXICON["darts_win"].format(
            prize=win_amount, new_balance=new_balance
        )
    else:
        result_text = LEXICON["darts_lose"].format(cost=stake, new_balance=new_balance)

    # Записываем, что пользователь играл в дартс
    await db.record_game_play(user_id, "darts")

    menu_text = LEXICON["darts_menu"].format(balance=new_balance)
    final_text = f"{result_text}\n\n{menu_text}"
    await bot.send_photo(
        user_id,
        settings.PHOTO_DARTS,
        caption=final_text,
        reply_markup=darts_stake_keyboard(user_language),
    )
