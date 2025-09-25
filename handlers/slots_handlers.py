# handlers/slots_handlers.py

import asyncio
import uuid
from typing import Dict

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_edit_caption, safe_send_message, safe_delete
from keyboards.factories import GameCallback, SlotsCallback
from keyboards.inline import slots_stake_keyboard
from lexicon.texts import LEXICON

router = Router()

# Экономика по твоей схеме: ставка -> выигрыш
SLOTS_PRIZES: Dict[int, int] = {
    1: 12,
    3: 36,
    5: 60,
    10: 120,
}


@router.callback_query(GameCallback.filter((F.name == "slots") & (F.action == "start")))
async def slots_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает или обновляет главное меню слотов с выбором ставки."""
    await state.clear()
    if not callback.message or not callback.from_user:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["slots_menu"].format(balance=balance)

    # Меняем старое сообщение на меню с кнопками выбора ставок
    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=slots_stake_keyboard(),
    )
    await callback.answer()


@router.callback_query(SlotsCallback.filter(F.action == "spin"))
async def spin_slots_handler(
    callback: CallbackQuery, callback_data: SlotsCallback, bot: Bot
):
    """Обрабатывает вращение и присылает новое сообщение с результатом и кнопками."""
    if not callback.from_user or not callback.message:
        return

    stake = callback_data.value
    if stake is None or stake not in SLOTS_PRIZES:
        await callback.answer("Неверная ставка.", show_alert=True)
        return

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < stake:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    # Отвечаем на колбэк, чтобы кнопка не "висела"
    await callback.answer()

    # Удаляем старое сообщение с кнопками, чтобы не было мусора
    await safe_delete(bot, callback.message.chat.id, callback.message.message_id)

    # Списываем деньги за попытку
    idem_key = f"slots-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, stake, "slots_spin_cost", idem_key=idem_key
    )
    if not spent:
        # Если списание не удалось, нужно отправить новое меню, так как старое мы удалили
        new_balance = await db.get_user_balance(user_id)
        error_text = "Не удалось списать ставку, попробуйте снова."
        menu_text = LEXICON["slots_menu"].format(balance=new_balance)
        await bot.send_message(user_id, f"{error_text}\n\n{menu_text}", reply_markup=slots_stake_keyboard())
        return

    # Отправляем эмодзи казино
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎰")

    # Ждем завершения анимации
    await asyncio.sleep(2)

    winning_values = {1, 22, 43, 64}
    is_win = msg.dice and msg.dice.value in winning_values
    win_amount = SLOTS_PRIZES[stake]
    result_text = ""
    
    # Рассчитываем результат и новый баланс
    if is_win:
        await db.add_balance_unrestricted(user_id, win_amount, "slots_win")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["slots_win"].format(
            prize=win_amount, new_balance=new_balance
        )
    else:
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["slots_lose"].format(
            cost=stake, new_balance=new_balance
        )
        
    # Формируем текст для нового меню
    menu_text = LEXICON["slots_menu"].format(balance=new_balance)
    
    # Объединяем результат и новое меню в одно сообщение
    final_text = f"{result_text}\n\n{menu_text}"

    # Отправляем одно новое сообщение с результатом и кнопками для новой игры
    await bot.send_message(
        user_id, final_text, reply_markup=slots_stake_keyboard()
    )