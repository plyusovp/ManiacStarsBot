# handlers/game_handlers.py
import asyncio
import logging
import secrets
import uuid
from typing import Any

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database import db
from economy import COINFLIP_LEVELS, COINFLIP_RAKE_PERCENT
from handlers.utils import clean_junk_message, safe_edit_caption
from keyboards.factories import CoinflipCallback, GameCallback
from keyboards.inline import coinflip_level_keyboard, coinflip_stake_keyboard
from lexicon.texts import LEXICON

router = Router()


async def process_coinflip_round(
    user_id: int, stake: int, level: str, idem_key: str, trace_id: str
) -> dict[str, Any]:
    """
    Обрабатывает один раунд игры Coinflip.
    Возвращает словарь с результатом.
    """
    extra = {"user_id": user_id, "trace_id": trace_id, "idem_key": idem_key}
    game_rules = COINFLIP_LEVELS.get(level)
    if not game_rules:
        logging.error(f"Invalid coinflip level provided: {level}", extra=extra)
        return {"success": False, "reason": "invalid_level"}

    spent_successfully = await db.spend_balance(
        user_id, stake, "coinflip_stake", ref_id=f"cf:{level}", idem_key=idem_key
    )
    if not spent_successfully:
        return {"success": False, "reason": "insufficient_funds"}

    is_win = secrets.randbelow(100) + 1 <= game_rules["win_chance"]

    prize = 0
    if is_win:
        gross_prize = int(stake * game_rules["multiplier"])
        rake = int(gross_prize * (COINFLIP_RAKE_PERCENT / 100))
        prize = gross_prize - rake
        result = await db.add_balance_with_checks(
            user_id, prize, "coinflip_win", ref_id=f"cf:{level}"
        )
        if not result.get("success"):
            logging.error(
                f"Failed to credit coinflip win. Reason: {result.get('reason')}",
                extra=extra,
            )
            await db.add_balance_unrestricted(
                user_id, stake, "coinflip_win_fail_refund"
            )

    log_extra = {**extra, "stake": stake, "level": level, "win": is_win, "prize": prize}
    logging.info("Coinflip result processed", extra=log_extra)
    return {"success": True, "is_win": is_win, "prize": prize}


@router.callback_query(
    GameCallback.filter((F.name == "coinflip") & (F.action == "start"))
)
async def coinflip_menu_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
) -> None:
    """Отображает меню выбора уровня сложности для Coinflip."""
    await clean_junk_message(state, bot)
    await state.clear()
    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["coinflip_menu"].format(balance=balance)
    if callback.message:
        await safe_edit_caption(
            bot,
            caption=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=coinflip_level_keyboard(),
        )
    await callback.answer()


@router.callback_query(CoinflipCallback.filter(F.action == "select_level"))
async def coinflip_level_selected_handler(
    callback: CallbackQuery,
    callback_data: CoinflipCallback,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Отображает меню выбора ставки после выбора уровня."""
    level = str(callback_data.value)
    level_name = COINFLIP_LEVELS.get(level, {}).get("name", "Неизвестный")
    await state.update_data(coinflip_level=level)
    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["coinflip_stake_select"].format(
        level_name=level_name, balance=balance
    )
    if callback.message:
        await safe_edit_caption(
            bot,
            caption=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=coinflip_stake_keyboard(level),
        )
    await callback.answer()


@router.callback_query(CoinflipCallback.filter(F.action == "select_stake"))
async def coinflip_stake_selected_handler(
    callback: CallbackQuery,
    callback_data: CoinflipCallback,
    bot: Bot,
    state: FSMContext,
    data: dict,
) -> None:
    """Обрабатывает игру после выбора ставки."""
    if not isinstance(callback_data.value, int):
        return
    stake = callback_data.value
    user_data = await state.get_data()
    level = user_data.get("coinflip_level")
    trace_id = data.get("trace_id", "unknown")
    user_id = callback.from_user.id
    extra = {"user_id": user_id, "trace_id": trace_id}

    if not level:
        logging.warning("Coinflip level not found in FSM state", extra=extra)
        await callback.answer("Ошибка: сначала выберите уровень.", show_alert=True)
        await coinflip_menu_handler(callback, state, bot)
        return

    balance = await db.get_user_balance(user_id)
    if balance < stake:
        await callback.answer(
            "У вас недостаточно звёзд для этой ставки.", show_alert=True
        )
        return

    idem_key = f"cf-{user_id}-{uuid.uuid4()}"
    level_name = COINFLIP_LEVELS[level]["name"]
    initial_text = LEXICON["coinflip_process"].format(
        level_name=level_name, stake=stake
    )
    if callback.message:
        await safe_edit_caption(
            bot,
            caption=initial_text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
        )
    await asyncio.sleep(1.5)

    result = await process_coinflip_round(user_id, stake, level, idem_key, trace_id)

    if not result.get("success"):
        error_reason = result.get("reason", "unknown_error")
        logging.error(f"Coinflip round failed. Reason: {error_reason}", extra=extra)
        final_text = f"Произошла ошибка: {error_reason}. Попробуйте еще раз."
        if callback.message:
            await safe_edit_caption(
                bot,
                caption=final_text,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=coinflip_stake_keyboard(level),
            )
        return

    new_balance = await db.get_user_balance(user_id)
    if result["is_win"]:
        final_text = LEXICON["coinflip_win"].format(
            prize=result["prize"], new_balance=new_balance
        )
    else:
        final_text = LEXICON["coinflip_loss"].format(
            stake=stake, new_balance=new_balance
        )
    if callback.message:
        await safe_edit_caption(
            bot,
            caption=final_text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=coinflip_stake_keyboard(level),
        )
    await callback.answer()
