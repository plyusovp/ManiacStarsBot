# handlers/basketball_handlers.py

import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_edit_caption, safe_send_message
from keyboards.factories import BasketballCallback, GameCallback
from keyboards.inline import basketball_play_again_keyboard
from lexicon.texts import LEXICON

router = Router()

# Стоимость и выигрыш
BASKETBALL_COST = 10
BASKETBALL_WIN_AMOUNT = 12


@router.callback_query(
    GameCallback.filter((F.name == "basketball") & (F.action == "start"))
)
async def basketball_menu_handler(callback: CallbackQuery, bot: Bot):
    """Отображает главное меню игры 'Баскетбол'."""
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["basketball_menu"].format(
        balance=balance, cost=BASKETBALL_COST, prize=BASKETBALL_WIN_AMOUNT
    )

    # Меняем старое сообщение на меню с кнопкой "Играть"
    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=basketball_play_again_keyboard(),
    )
    await callback.answer()


@router.callback_query(BasketballCallback.filter(F.action == "throw"))
async def throw_basketball_handler(callback: CallbackQuery, bot: Bot):
    """Обрабатывает бросок мяча."""
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < BASKETBALL_COST:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    # Отвечаем на старый колбэк, чтобы кнопка не "зависала"
    await callback.answer()

    # Списываем деньги за попытку
    idem_key = f"basketball-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, BASKETBALL_COST, "basketball_throw_cost", idem_key=idem_key
    )
    if not spent:
        await safe_send_message(
            bot, user_id, "Не удалось списать ставку, попробуйте снова."
        )
        return

    # Отправляем эмодзи баскетбола
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🏀")

    # Значения 4 и 5 означают попадание в корзину
    winning_values = {4, 5}
    is_win = msg.dice and msg.dice.value in winning_values

    # Ждем завершения анимации
    await asyncio.sleep(4)

    if is_win:
        # Начисляем выигрыш
        await db.add_balance_unrestricted(
            user_id, BASKETBALL_WIN_AMOUNT, "basketball_win"
        )
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["basketball_win"].format(
            prize=BASKETBALL_WIN_AMOUNT, new_balance=new_balance
        )
    else:
        # Проигрыш
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["basketball_lose"].format(
            cost=BASKETBALL_COST, new_balance=new_balance
        )

    # Отправляем новое сообщение с результатом и кнопкой "Играть снова"
    await bot.send_message(
        user_id, result_text, reply_markup=basketball_play_again_keyboard()
    )
