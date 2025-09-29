# plyusovp/maniacstarsbot/ManiacStarsBot-67d43495a3d8b0b5689fd3311461f2c73499ed96/handlers/basketball_handlers.py

import asyncio
import uuid
from typing import Dict

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import BasketballCallback, GameCallback
from keyboards.inline import basketball_stake_keyboard
from lexicon.texts import LEXICON

router = Router()

# Новая экономика: ставка -> выигрыш (x2)
BASKETBALL_PRIZES: Dict[int, int] = {
    1: 2,
    3: 6,
    5: 10,
    10: 20,
}


@router.callback_query(
    GameCallback.filter((F.name == "basketball") & (F.action == "start"))
)
async def basketball_menu_handler(callback: CallbackQuery, bot: Bot):
    """Отображает главное меню игры 'Баскетбол' с выбором ставки."""
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["basketball_menu"].format(balance=balance)

    # Меняем старое сообщение на меню с кнопками выбора ставок
    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=basketball_stake_keyboard(),
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
    if stake_from_callback is None or int(stake_from_callback) not in BASKETBALL_PRIZES:
        await callback.answer("Неверная ставка.", show_alert=True)
        return

    stake = int(stake_from_callback)
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < stake:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    # Отвечаем на колбэк
    await callback.answer()

    # Удаляем старое сообщение
    await safe_delete(bot, callback.message.chat.id, callback.message.message_id)

    # Списываем деньги за попытку
    idem_key = f"basketball-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, stake, "basketball_throw_cost", idem_key=idem_key
    )
    if not spent:
        # Если списание не удалось, отправляем новое меню
        new_balance = await db.get_user_balance(user_id)
        error_text = "Не удалось списать ставку, попробуйте снова."
        menu_text = LEXICON["basketball_menu"].format(balance=new_balance)
        await bot.send_message(
            user_id, f"{error_text}\n\n{menu_text}", reply_markup=basketball_stake_keyboard()
        )
        return

    # Отправляем эмодзи баскетбола
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🏀")

    # Значения 4 и 5 означают попадание в корзину (40% шанс)
    winning_values = {4, 5}
    is_win = msg.dice and msg.dice.value in winning_values
    win_amount = BASKETBALL_PRIZES[stake]

    # Ждем завершения анимации
    await asyncio.sleep(4)

    # Рассчитываем результат
    if is_win:
        # Начисляем выигрыш
        await db.add_balance_unrestricted(
            user_id, win_amount, "basketball_win"
        )
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["basketball_win"].format(
            prize=win_amount, new_balance=new_balance
        )
    else:
        # Проигрыш
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["basketball_lose"].format(
            cost=stake, new_balance=new_balance
        )
        
    # Формируем текст для нового меню
    menu_text = LEXICON["basketball_menu"].format(balance=new_balance)
    final_text = f"{result_text}\n\n{menu_text}"

    # Отправляем одно новое сообщение с результатом и клавиатурой для новой игры
    await bot.send_message(user_id, final_text, reply_markup=basketball_stake_keyboard())