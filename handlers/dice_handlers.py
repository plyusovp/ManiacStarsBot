# plyusovp/maniacstarsbot/ManiacStarsBot-67d43495a3d8b0b5689fd3311461f2c73499ed96/handlers/dice_handlers.py

import asyncio
import uuid
from typing import Dict

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import DiceCallback, GameCallback
from keyboards.inline import dice_range_choice_keyboard, dice_stake_keyboard
from lexicon.texts import LEXICON

router = Router()

# Новая экономика: ставка -> выигрыш (почти x2)
# Шанс 50/50, поэтому даем небольшой рейк в 10% на крупных ставках
DICE_PRIZES: Dict[int, int] = {
    1: 2,
    3: 5,
    5: 9,
    10: 18,
}

# Создаем состояния (FSM) для хранения ставки
class DiceState(StatesGroup):
    waiting_for_choice = State()


@router.callback_query(GameCallback.filter((F.name == "dice") & (F.action == "start")))
async def dice_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает главное меню игры 'Кости' с выбором ставки."""
    await state.clear()
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["dice_menu"].format(balance=balance)

    # Меняем старое сообщение на меню с кнопками выбора ставок
    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=dice_stake_keyboard(),
    )
    await callback.answer()


@router.callback_query(DiceCallback.filter(F.action == "stake"))
async def dice_stake_selected_handler(
    callback: CallbackQuery, callback_data: DiceCallback, bot: Bot, state: FSMContext
):
    """Обрабатывает выбор ставки и предлагает выбрать диапазон."""
    if not callback.message:
        return

    stake_from_callback = callback_data.value
    if stake_from_callback is None or int(stake_from_callback) not in DICE_PRIZES:
        await callback.answer("Неверная ставка.", show_alert=True)
        return

    stake = int(stake_from_callback)
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < stake:
        await callback.answer("Недостаточно средств.", show_alert=True)
        return

    # Сохраняем ставку в состояние
    await state.set_state(DiceState.waiting_for_choice)
    await state.update_data(stake=stake)

    text = f"Ставка {stake} ⭐ принята! Теперь выбери, на что ставишь:"
    await safe_edit_caption(
        bot,
        text,
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=dice_range_choice_keyboard(),
    )
    await callback.answer()


@router.callback_query(DiceState.waiting_for_choice, DiceCallback.filter(F.action == "choice"))
async def throw_dice_handler(
    callback: CallbackQuery, callback_data: DiceCallback, bot: Bot, state: FSMContext
):
    """Обрабатывает бросок костей после выбора диапазона."""
    if not callback.from_user or not callback.message:
        return

    fsm_data = await state.get_data()
    stake = fsm_data.get("stake")
    user_choice = callback_data.choice  # "low" or "high"

    if not stake or not user_choice:
        await state.clear()
        await callback.answer("Произошла ошибка, попробуйте снова.", show_alert=True)
        return

    await state.clear()
    user_id = callback.from_user.id
    
    # Сразу удаляем сообщение, чтобы не было мусора
    await safe_delete(bot, callback.message.chat.id, callback.message.message_id)

    # Списываем деньги
    idem_key = f"dice-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, stake, "dice_throw_cost", idem_key=idem_key
    )
    if not spent:
        new_balance = await db.get_user_balance(user_id)
        error_text = "Не удалось списать ставку, попробуйте снова."
        menu_text = LEXICON["dice_menu"].format(balance=new_balance)
        await bot.send_message(
            user_id, f"{error_text}\n\n{menu_text}", reply_markup=dice_stake_keyboard()
        )
        return

    # Отправляем эмодзи костей
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎲")
    dice_value = msg.dice.value

    # Определяем, выиграл ли пользователь
    is_win = (user_choice == "low" and dice_value in [1, 2, 3]) or \
             (user_choice == "high" and dice_value in [4, 5, 6])
    
    win_amount = DICE_PRIZES[stake]
    choice_text = "1-3" if user_choice == "low" else "4-6"

    await asyncio.sleep(4)

    if is_win:
        await db.add_balance_unrestricted(user_id, win_amount, "dice_win")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["dice_win"].format(
            choice=choice_text, value=dice_value, prize=win_amount, new_balance=new_balance
        )
    else:
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["dice_lose"].format(
            choice=choice_text, value=dice_value, cost=stake, new_balance=new_balance
        )

    # Формируем новое меню и отправляем одним сообщением
    menu_text = LEXICON["dice_menu"].format(balance=new_balance)
    final_text = f"{result_text}\n\n{menu_text}"

    await bot.send_message(user_id, final_text, reply_markup=dice_stake_keyboard())