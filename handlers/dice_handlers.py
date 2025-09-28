# handlers/dice_handlers.py

import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from database import db
from handlers.utils import safe_edit_caption, safe_send_message
from keyboards.factories import DiceCallback, GameCallback
from keyboards.inline import dice_choice_keyboard
from lexicon.texts import LEXICON

router = Router()

# Стоимость и выигрыш
DICE_COST = 10
DICE_WIN_AMOUNT = 12


@router.callback_query(GameCallback.filter((F.name == "dice") & (F.action == "start")))
async def dice_menu_handler(callback: CallbackQuery, bot: Bot):
    """Отображает главное меню игры 'Кости' с выбором ставки."""
    if not callback.message:
        return

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["dice_menu"].format(
        balance=balance, cost=DICE_COST, prize=DICE_WIN_AMOUNT
    )

    # Меняем старое сообщение на меню с кнопками выбора
    await safe_edit_caption(
        bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=dice_choice_keyboard(),
    )
    await callback.answer()


@router.callback_query(DiceCallback.filter(F.action == "choice"))
async def throw_dice_handler(
    callback: CallbackQuery, callback_data: DiceCallback, bot: Bot
):
    """Обрабатывает бросок костей после выбора игрока."""
    user_id = callback.from_user.id
    user_choice = callback_data.choice  # "low" or "high"

    if not user_choice:
        await callback.answer("Произошла ошибка, попробуйте снова.", show_alert=True)
        return

    balance = await db.get_user_balance(user_id)

    if balance < DICE_COST:
        await callback.answer("Недостаточно средств для игры.", show_alert=True)
        return

    # Отвечаем на старый колбэк
    await callback.answer()

    # Списываем деньги
    idem_key = f"dice-spend-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(
        user_id, DICE_COST, "dice_throw_cost", idem_key=idem_key
    )
    if not spent:
        await safe_send_message(
            bot, user_id, "Не удалось списать ставку, попробуйте снова."
        )
        return

    # Отправляем эмодзи костей
    msg: Message = await bot.send_dice(chat_id=user_id, emoji="🎲")
    dice_value = msg.dice.value

    # Определяем, выиграл ли пользователь
    is_win = False
    if user_choice == "low" and dice_value in [1, 2, 3]:
        is_win = True
    elif user_choice == "high" and dice_value in [4, 5, 6]:
        is_win = True

    # Текст для пользователя о его выборе
    choice_text = "1-3" if user_choice == "low" else "4-6"

    await asyncio.sleep(4)

    if is_win:
        await db.add_balance_unrestricted(user_id, DICE_WIN_AMOUNT, "dice_win")
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["dice_win"].format(
            choice=choice_text,
            value=dice_value,
            prize=DICE_WIN_AMOUNT,
            new_balance=new_balance,
        )
    else:
        new_balance = await db.get_user_balance(user_id)
        result_text = LEXICON["dice_lose"].format(
            choice=choice_text,
            value=dice_value,
            cost=DICE_COST,
            new_balance=new_balance,
        )

    # Отправляем новое сообщение с результатом и клавиатурой для новой игры
    await bot.send_message(user_id, result_text, reply_markup=dice_choice_keyboard())
