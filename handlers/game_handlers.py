# handlers/game_handlers.py
import asyncio
import logging
import random
import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database import db
from economy import COINFLIP_LEVELS, COINFLIP_RAKE_PERCENT
from handlers.utils import clean_junk_message
from keyboards.inline import coinflip_level_keyboard, coinflip_stake_keyboard
from lexicon.texts import LEXICON

router = Router()
logger = logging.getLogger(__name__)

# --- Вспомогательные функции ---


async def process_coinflip_round(
    user_id: int, stake: int, level: str, idem_key: str
) -> dict:
    """
    Обрабатывает один раунд игры Coinflip.
    Возвращает словарь с результатом.
    """
    game_rules = COINFLIP_LEVELS.get(level)
    if not game_rules:
        return {"success": False, "reason": "invalid_level"}

    # 1. Списываем ставку
    spent_successfully = await db.spend_balance(
        user_id, stake, "coinflip_stake", ref_id=f"cf:{level}", idem_key=idem_key
    )
    if not spent_successfully:
        return {"success": False, "reason": "insufficient_funds"}

    # 2. Генерируем исход (один random на раунд)
    is_win = random.randint(1, 100) <= game_rules["chance"]

    # 3. Рассчитываем выигрыш и начисляем, если победа
    prize = 0
    if is_win:
        gross_prize = int(stake * game_rules["prize_mult"])
        rake = int(gross_prize * (COINFLIP_RAKE_PERCENT / 100))
        prize = gross_prize - rake

        await db.add_balance_with_checks(
            user_id, prize, "coinflip_win", ref_id=f"cf:{level}"
        )

    # 4. Логируем исход
    log_info = {
        "game": "coinflip",
        "user_id": user_id,
        "stake": stake,
        "level": level,
        "chance": game_rules["chance"],
        "is_win": is_win,
        "prize": prize,
        "round_id": idem_key,
    }
    logger.info(f"Coinflip result: {log_info}")

    return {"success": True, "is_win": is_win, "prize": prize}


# --- Хендлеры ---


@router.callback_query(F.data == "game_coinflip")
async def coinflip_menu_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Отображает меню выбора уровня сложности для Coinflip."""
    await clean_junk_message(callback, state)
    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["coinflip_menu"].format(balance=balance)
    await callback.message.edit_caption(
        caption=text, reply_markup=coinflip_level_keyboard()
    )


@router.callback_query(F.data.startswith("cf_level:"))
async def coinflip_level_selected_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Отображает меню выбора ставки после выбора уровня."""
    level = callback.data.split(":")[1]
    level_name = COINFLIP_LEVELS.get(level, {}).get("name", "Неизвестный")

    await state.update_data(coinflip_level=level)

    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["coinflip_stake_select"].format(
        level_name=level_name, balance=balance
    )
    await callback.message.edit_caption(
        caption=text, reply_markup=coinflip_stake_keyboard()
    )


@router.callback_query(F.data.startswith("cf_stake:"))
async def coinflip_stake_selected_handler(
    callback: CallbackQuery, bot: Bot, state: FSMContext
) -> None:
    """Обрабатывает игру после выбора ставки."""
    try:
        stake = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        return await callback.answer("Ошибка: неверный формат ставки.", show_alert=True)

    user_data = await state.get_data()
    level = user_data.get("coinflip_level")
    if not level:
        return await callback.answer(
            "Ошибка: сначала выберите уровень сложности.", show_alert=True
        )

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    if balance < stake:
        return await callback.answer(
            "У вас недостаточно звёзд для этой ставки.", show_alert=True
        )

    # Генерируем уникальный ключ для этой попытки игры
    idem_key = f"cf-{user_id}-{uuid.uuid4()}"

    # Анимация "броска монеты"
    level_name = COINFLIP_LEVELS[level]["name"]
    initial_text = LEXICON["coinflip_process"].format(
        level_name=level_name, stake=stake
    )
    await callback.message.edit_caption(caption=initial_text)
    await asyncio.sleep(1.5)

    # Обработка раунда
    result = await process_coinflip_round(user_id, stake, level, idem_key)

    if not result.get("success"):
        error_reason = result.get("reason", "unknown_error")
        # В случае ошибки, возвращаемся в меню выбора ставки
        # (средства не списались, можно пробовать снова)
        final_text = f"Произошла ошибка: {error_reason}. Попробуйте еще раз."
        await callback.message.edit_caption(
            caption=final_text, reply_markup=coinflip_stake_keyboard()
        )
        return

    # Отображение результата
    new_balance = await db.get_user_balance(user_id)
    if result["is_win"]:
        final_text = LEXICON["coinflip_win"].format(
            prize=result["prize"], new_balance=new_balance
        )
    else:
        final_text = LEXICON["coinflip_loss"].format(
            stake=stake, new_balance=new_balance
        )

    # После игры снова показываем меню выбора ставки
    await callback.message.edit_caption(
        caption=final_text, reply_markup=coinflip_stake_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_games")
async def back_to_games_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает в главное игровое меню (предполагается, что оно в menu_handler)."""
    # Этот импорт здесь, чтобы избежать циклических зависимостей
    from handlers.menu_handler import games_handler

    await games_handler(callback, state)
