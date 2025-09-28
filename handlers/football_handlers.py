# handlers/football_handlers.py

import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_edit_caption
from keyboards.factories import FootballCallback, GameCallback
from keyboards.inline import football_keyboard
from lexicon.texts import LEXICON

router = Router()

# Стоимость и выигрыш
FOOTBALL_COST = 10
FOOTBALL_WIN_AMOUNT = 12


@router.callback_query(
    GameCallback.filter((F.name == "football") & (F.action == "start"))
)
async def football_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает главное меню игры 'Футбол'."""
    await state.clear()
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["football_menu"].format(
        balance=balance, cost=FOOTBALL_COST, prize=FOOTBALL_WIN_AMOUNT
    )

    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=football_keyboard(),
    )
    await callback.answer()


@router.callback_query(FootballCallback.filter(F.action == "kick"))
async def kick_football_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обрабатывает удар по мячу."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)

    if balance < FOOTBALL_COST:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    # Списываем деньги за попытку
    idem_key = f"football-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, FOOTBALL_COST, "football_kick_cost", idem_key=idem_key
    )
    if not spent:
        await callback.answer(
            "Не удалось списать ставку, попробуйте снова.", show_alert=True
        )
        return

    # Отправляем эмодзи футбола
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="⚽")

    # Значения, которые означают гол
    winning_values = {3, 4, 5}
    is_win = msg.dice and msg.dice.value in winning_values

    # Ждем завершения анимации
    await asyncio.sleep(4)

    if is_win:
        # Начисляем выигрыш
        await db.add_balance_unrestricted(user_id, FOOTBALL_WIN_AMOUNT, "football_win")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["football_win"].format(
            prize=FOOTBALL_WIN_AMOUNT, new_balance=new_balance
        )
    else:
        # Проигрыш
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["football_lose"].format(
            cost=FOOTBALL_COST, new_balance=new_balance
        )

    # Отправляем результат отдельным сообщением
    await bot.send_message(user_id, result_text)

    # Обновляем меню, чтобы показать актуальный баланс
    await football_menu_handler(callback, state, bot)
