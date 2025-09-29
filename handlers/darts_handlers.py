# plyusovp/maniacstarsbot/ManiacStarsBot-67d43495a3d8b0b5689fd3311461f2c73499ed96/handlers/darts_handlers.py

import asyncio
import uuid
from typing import Dict

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import DartsCallback, GameCallback
from keyboards.inline import darts_stake_keyboard
from lexicon.texts import LEXICON

router = Router()

# Новая экономика: ставка -> выигрыш (x5)
# Шанс на победу 1/6 (16.7%), так что x5 дает небольшой перевес казино
DARTS_PRIZES: Dict[int, int] = {
    1: 5,
    3: 15,
    5: 25,
    10: 50,
}


@router.callback_query(GameCallback.filter((F.name == "darts") & (F.action == "start")))
async def darts_menu_handler(callback: CallbackQuery, bot: Bot):
    """Отображает главное меню игры 'Дартс' с выбором ставки."""
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["darts_menu"].format(balance=balance)

    # Меняем старое сообщение на меню с кнопками выбора ставок
    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=darts_stake_keyboard(),
    )
    await callback.answer()


@router.callback_query(DartsCallback.filter(F.action == "throw"))
async def throw_darts_handler(
    callback: CallbackQuery, callback_data: DartsCallback, bot: Bot
):
    """Обрабатывает бросок дротика по выбранной ставке."""
    if not callback.from_user or not callback.message:
        return

    stake_from_callback = callback_data.value
    if stake_from_callback is None or int(stake_from_callback) not in DARTS_PRIZES:
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
    idem_key = f"darts-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, stake, "darts_throw_cost", idem_key=idem_key
    )
    if not spent:
        # Если списание не удалось, отправляем новое меню
        new_balance = await db.get_user_balance(user_id)
        error_text = "Не удалось списать ставку, попробуйте снова."
        menu_text = LEXICON["darts_menu"].format(balance=new_balance)
        await bot.send_message(
            user_id, f"{error_text}\n\n{menu_text}", reply_markup=darts_stake_keyboard()
        )
        return

    # Отправляем эмодзи дартса
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎯")

    # Значение 6 означает попадание в яблочко (шанс 1/6)
    is_win = msg.dice and msg.dice.value == 6
    win_amount = DARTS_PRIZES[stake]

    # Ждем завершения анимации
    await asyncio.sleep(4)

    # Рассчитываем результат
    if is_win:
        await db.add_balance_unrestricted(user_id, win_amount, "darts_win")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["darts_win"].format(
            prize=win_amount, new_balance=new_balance
        )
    else:
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["darts_lose"].format(
            cost=stake, new_balance=new_balance
        )

    # Формируем текст для нового меню
    menu_text = LEXICON["darts_menu"].format(balance=new_balance)
    final_text = f"{result_text}\n\n{menu_text}"

    # Отправляем одно новое сообщение с результатом и клавиатурой для новой игры
    await bot.send_message(user_id, final_text, reply_markup=darts_stake_keyboard())