# plyusovp/maniacstarsbot/ManiacStarsBot-67d43495a3d8b0b5689fd3311461f2c73499ed96/handlers/football_handlers.py

import asyncio
import uuid
from typing import Dict

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import FootballCallback, GameCallback
from keyboards.inline import football_stake_keyboard
from lexicon.texts import LEXICON

router = Router()

# Новая экономика: ставка -> выигрыш (x2)
# Дает нам преимущество в 20% из-за 40% шанса на победу
FOOTBALL_PRIZES: Dict[int, int] = {
    1: 2,
    3: 6,
    5: 10,
    10: 20,
}


@router.callback_query(
    GameCallback.filter((F.name == "football") & (F.action == "start"))
)
async def football_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Отображает главное меню игры 'Футбол' с выбором ставки."""
    await state.clear()
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    # Убираем из текста упоминание фиксированной ставки, т.к. теперь есть выбор
    text = LEXICON["football_menu"].format(balance=balance)

    # Используем новую клавиатуру с выбором ставок
    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=football_stake_keyboard(),
    )
    await callback.answer()


@router.callback_query(FootballCallback.filter(F.action == "kick"))
async def kick_football_handler(
    callback: CallbackQuery, callback_data: FootballCallback, bot: Bot, state: FSMContext
):
    """Обрабатывает удар по мячу по выбранной ставке."""
    if not callback.from_user or not callback.message:
        return

    stake_from_callback = callback_data.value
    if stake_from_callback is None or int(stake_from_callback) not in FOOTBALL_PRIZES:
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

    # Удаляем старое сообщение с кнопками, чтобы чат был чистым
    await safe_delete(bot, callback.message.chat.id, callback.message.message_id)

    # Списываем деньги за попытку
    idem_key = f"football-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, stake, "football_kick_cost", idem_key=idem_key
    )
    if not spent:
        # Если списание не удалось, отправляем новое меню, так как старое удалили
        new_balance = await db.get_user_balance(user_id)
        error_text = "Не удалось списать ставку, попробуйте снова."
        menu_text = LEXICON["football_menu"].format(balance=new_balance)
        await bot.send_message(
            user_id, f"{error_text}\n\n{menu_text}", reply_markup=football_stake_keyboard()
        )
        return

    # Отправляем эмодзи футбола
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="⚽️")

    # ВАЖНО: Правильные выигрышные значения для "⚽️" - 4 и 5 (гол).
    # Это дает 40% шанс на победу (2 из 5).
    winning_values = {4, 5}
    is_win = msg.dice and msg.dice.value in winning_values
    win_amount = FOOTBALL_PRIZES[stake]

    # Ждем завершения анимации
    await asyncio.sleep(4)

    # Рассчитываем результат
    if is_win:
        # Начисляем выигрыш
        await db.add_balance_unrestricted(user_id, win_amount, "football_win")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["football_win"].format(
            prize=win_amount, new_balance=new_balance
        )
    else:
        # Проигрыш
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["football_lose"].format(
            cost=stake, new_balance=new_balance
        )

    # Формируем текст для нового меню
    menu_text = LEXICON["football_menu"].format(balance=new_balance)
    # Объединяем результат и новое меню в одно сообщение
    final_text = f"{result_text}\n\n{menu_text}"

    # Отправляем ОДНО новое сообщение с результатом и клавиатурой для новой игры
    await bot.send_message(user_id, final_text, reply_markup=football_stake_keyboard())