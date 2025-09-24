# handlers/bowling_handlers.py

import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_edit_caption, safe_send_message
from keyboards.factories import BowlingCallback, GameCallback
from keyboards.inline import bowling_play_again_keyboard
from lexicon.texts import LEXICON

router = Router()

# Стоимость и выигрыш
BOWLING_COST = 10
BOWLING_WIN_AMOUNT = 12


@router.callback_query(GameCallback.filter((F.name == "bowling") & (F.action == "start")))
async def bowling_menu_handler(callback: CallbackQuery, bot: Bot):
    """Отображает главное меню игры 'Боулинг'."""
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["bowling_menu"].format(
        balance=balance, cost=BOWLING_COST, prize=BOWLING_WIN_AMOUNT
    )

    # Меняем старое сообщение на меню с кнопкой "Играть"
    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=bowling_play_again_keyboard(), # Используем новую клавиатуру
    )
    await callback.answer()


@router.callback_query(BowlingCallback.filter(F.action == "throw"))
async def throw_bowling_handler(callback: CallbackQuery, bot: Bot):
    """Обрабатывает бросок шара."""
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < BOWLING_COST:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    # Отвечаем на старый колбэк, чтобы кнопка не "зависала"
    await callback.answer()

    # Списываем деньги за попытку
    idem_key = f"bowling-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, BOWLING_COST, "bowling_throw_cost", idem_key=idem_key
    )
    if not spent:
        # Если списать не удалось, отправляем сообщение
        await safe_send_message(user_id, "Не удалось списать ставку, попробуйте снова.")
        return

    # Отправляем эмодзи боулинга
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎳")

    # Значение 6 означает страйк (все кегли сбиты)
    is_win = msg.dice and msg.dice.value == 6

    # Ждем завершения анимации
    await asyncio.sleep(4)

    if is_win:
        # Начисляем выигрыш
        await db.add_balance_unrestricted(user_id, BOWLING_WIN_AMOUNT, "bowling_win")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["bowling_win"].format(
            prize=BOWLING_WIN_AMOUNT, new_balance=new_balance
        )
    else:
        # Проигрыш
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["bowling_lose"].format(
            cost=BOWLING_COST, new_balance=new_balance
        )

    # *** ГЛАВНОЕ ИЗМЕНЕНИЕ: ***
    # Отправляем новое сообщение с результатом и кнопкой "Играть снова"
    await bot.send_message(
        user_id, result_text, reply_markup=bowling_play_again_keyboard()
    )