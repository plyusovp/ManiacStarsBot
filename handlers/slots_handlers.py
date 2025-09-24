# handlers/slots_handlers.py

import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_edit_caption
from keyboards.factories import GameCallback, SlotsCallback
from keyboards.inline import slots_keyboard
from lexicon.texts import LEXICON

router = Router()

# Стоимость и выигрыш (пока что фиксированные)
SLOT_COST = 10
SLOT_WIN_AMOUNT = 12


@router.callback_query(GameCallback.filter((F.name == "slots") & (F.action == "start")))
async def slots_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает главное меню слотов."""
    print("!!! СЛОТЫ ЗАПУСТИЛИСЬ !!!")
    await state.clear()
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["slots_menu"].format(
        balance=balance, cost=SLOT_COST, prize=SLOT_WIN_AMOUNT
    )

    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=slots_keyboard(),
    )
    await callback.answer()


@router.callback_query(SlotsCallback.filter(F.action == "spin"))
async def spin_slots_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обрабатывает вращение слотов."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < SLOT_COST:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    # Списываем деньги за попытку
    idem_key = f"slots-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, SLOT_COST, "slots_spin_cost", idem_key=idem_key
    )
    if not spent:
        await callback.answer("Не удалось списать ставку, попробуйте снова.", show_alert=True)
        return

    # Отправляем эмодзи казино
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎰")

    # Значения, которые означают выигрыш (три одинаковых символа)
    # 1 - три BAR, 22 - три винограда, 43 - три лимона, 64 - три семерки
    winning_values = {1, 22, 43, 64}
    is_win = msg.dice and msg.dice.value in winning_values

    # Ждем завершения анимации
    await asyncio.sleep(2)

    if is_win:
        # Начисляем выигрыш
        await db.add_balance_unrestricted(user_id, SLOT_WIN_AMOUNT, "slots_win")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["slots_win"].format(
            prize=SLOT_WIN_AMOUNT, new_balance=new_balance
        )
    else:
        # Проигрыш
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["slots_lose"].format(
            cost=SLOT_COST, new_balance=new_balance
        )

    # Отправляем результат отдельным сообщением
    await bot.send_message(user_id, result_text)

    # Обновляем меню, чтобы показать актуальный баланс
    await slots_menu_handler(callback, state, bot)