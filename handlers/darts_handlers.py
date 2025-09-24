# handlers/darts_handlers.py

import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_edit_caption, safe_send_message
from keyboards.factories import DartsCallback, GameCallback
from keyboards.inline import darts_play_again_keyboard
from lexicon.texts import LEXICON

router = Router()

# Стоимость и выигрыш
DARTS_COST = 10
DARTS_WIN_AMOUNT = 12


@router.callback_query(GameCallback.filter((F.name == "darts") & (F.action == "start")))
async def darts_menu_handler(callback: CallbackQuery, bot: Bot):
    """Отображает главное меню игры 'Дартс'."""
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["darts_menu"].format(
        balance=balance, cost=DARTS_COST, prize=DARTS_WIN_AMOUNT
    )

    # Меняем старое сообщение на меню с кнопкой "Играть"
    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=darts_play_again_keyboard(),
    )
    await callback.answer()


@router.callback_query(DartsCallback.filter(F.action == "throw"))
async def throw_darts_handler(callback: CallbackQuery, bot: Bot):
    """Обрабатывает бросок дротика."""
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < DARTS_COST:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    # Отвечаем на старый колбэк, чтобы кнопка не "зависала"
    await callback.answer()

    # Списываем деньги за попытку
    idem_key = f"darts-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, DARTS_COST, "darts_throw_cost", idem_key=idem_key
    )
    if not spent:
        await safe_send_message(user_id, "Не удалось списать ставку, попробуйте снова.")
        return

    # Отправляем эмодзи дартса
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎯")

    # Значение 6 означает попадание в яблочко
    is_win = msg.dice and msg.dice.value == 6

    # Ждем завершения анимации
    await asyncio.sleep(4)

    if is_win:
        # Начисляем выигрыш
        await db.add_balance_unrestricted(user_id, DARTS_WIN_AMOUNT, "darts_win")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["darts_win"].format(
            prize=DARTS_WIN_AMOUNT, new_balance=new_balance
        )
    else:
        # Проигрыш
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["darts_lose"].format(
            cost=DARTS_COST, new_balance=new_balance
        )

    # Отправляем новое сообщение с результатом и кнопкой "Играть снова"
    await bot.send_message(
        user_id, result_text, reply_markup=darts_play_again_keyboard()
    )