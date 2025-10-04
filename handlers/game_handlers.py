# handlers/game_handlers.py
import asyncio
import logging
import secrets
import uuid

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto

from config import settings
from database import db  # <--- ВОТ ЭТА ХУЙНЯ ПРОПАЛА
from economy import COINFLIP_RAKE_PERCENT, COINFLIP_STAGES
from handlers.utils import clean_junk_message, safe_edit_caption, safe_edit_media
from keyboards.factories import CoinflipCallback, GameCallback
from keyboards.inline import (
    coinflip_choice_keyboard,
    coinflip_continue_keyboard,
    coinflip_play_again_keyboard,
    coinflip_stake_keyboard,
)
from lexicon.texts import LEXICON

router = Router()
logger = logging.getLogger(__name__)


class CoinflipState(StatesGroup):
    game_in_progress = State()


@router.callback_query(
    GameCallback.filter((F.name == "coinflip") & (F.action == "start"))
)
async def coinflip_menu_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
) -> None:
    """Отображает меню выбора ставки для Coinflip."""
    await clean_junk_message(state, bot)
    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["coinflip_menu"].format(
        balance=balance, rake_percent=settings.COINFLIP_RAKE_PERCENT
    )
    if callback.message:
        await safe_edit_caption(
            bot,
            caption=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=coinflip_stake_keyboard(),
        )
    await callback.answer()


@router.callback_query(CoinflipCallback.filter(F.action == "stake"))
async def coinflip_stake_selected_handler(
    callback: CallbackQuery,
    callback_data: CoinflipCallback,
    bot: Bot,
    state: FSMContext,
) -> None:
    """Обрабатывает выбор ставки."""
    user_id = callback.from_user.id
    try:
        if not isinstance(callback_data.value, int) or not callback.message:
            return

        stake = int(callback_data.value)
        balance = await db.get_user_balance(user_id)
        if balance < stake:
            await callback.answer("Недостаточно средств.", show_alert=True)
            return

        idem_key = f"cf-start-{user_id}-{uuid.uuid4()}"
        spent = await db.spend_balance(
            user_id, stake, "coinflip_stake", idem_key=idem_key
        )
        if not spent:
            await callback.answer(
                "Не удалось списать ставку. Попробуйте еще раз.", show_alert=True
            )
            return

        await state.set_state(CoinflipState.game_in_progress)
        await state.update_data(stake=stake, stage=0, idem_key=idem_key)

        text = LEXICON["coinflip_choice_prompt"].format(stake=stake)
        await safe_edit_caption(
            bot,
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=coinflip_choice_keyboard(),
        )
        await callback.answer()

    except TelegramBadRequest as e:
        logger.warning(
            f"Failed to edit message for user {user_id} during stake selection: {e}"
        )
        await callback.answer(
            "Произошла небольшая ошибка, попробуй еще раз.", show_alert=True
        )
        await state.clear()


@router.callback_query(
    CoinflipCallback.filter(F.action == "choice"),
    CoinflipState.game_in_progress,
)
async def coinflip_choice_handler(
    callback: CallbackQuery,
    callback_data: CoinflipCallback,
    bot: Bot,
    state: FSMContext,
):
    """Обрабатывает выбор 'Орла' или 'Решки'."""
    try:
        if not callback.data or not callback.message:
            await callback.answer()
            return

        await callback.answer()

        media = InputMediaPhoto(
            media=settings.PHOTO_COINFLIP_PROCESS, caption=LEXICON["coinflip_process"]
        )
        await safe_edit_media(
            bot,
            media,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=None,
        )

        await asyncio.sleep(1.5)

        fsm_data = await state.get_data()
        if not fsm_data:
            await safe_edit_caption(
                bot,
                "Произошла ошибка, данные игры потеряны. Начните заново.",
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=coinflip_play_again_keyboard(),
            )
            await state.clear()
            return

        stage_index = fsm_data.get("stage", 0)
        current_stage = COINFLIP_STAGES[stage_index]
        is_win = secrets.randbelow(100) < current_stage["chance"]

        await process_coinflip_result(callback, bot, state, is_win)
    except Exception:
        await state.clear()
        raise


async def process_coinflip_result(
    callback: CallbackQuery, bot: Bot, state: FSMContext, is_win: bool
):
    """Обрабатывает результат текущего этапа игры."""
    if not callback.message:
        return
    user_id = callback.from_user.id
    fsm_data = await state.get_data()
    stage_index = fsm_data.get("stage", 0)
    stake = fsm_data.get("stake", 0)

    if stage_index >= len(COINFLIP_STAGES):
        return await cash_out(callback, bot, state)

    current_stage = COINFLIP_STAGES[stage_index]

    if is_win:
        next_stage_index = stage_index + 1
        await state.update_data(stage=next_stage_index)

        gross_prize = int(stake * current_stage["multiplier"])
        rake = int(gross_prize * (COINFLIP_RAKE_PERCENT / 100))
        current_prize = gross_prize - rake

        if next_stage_index < len(COINFLIP_STAGES):
            next_stage = COINFLIP_STAGES[next_stage_index]
            next_gross = int(stake * next_stage["multiplier"])
            next_prize = next_gross - int(next_gross * (COINFLIP_RAKE_PERCENT / 100))
            text = LEXICON["coinflip_continue"].format(
                current_prize=current_prize,
                next_prize=next_prize,
                next_chance=next_stage["chance"],
            )
            media = InputMediaPhoto(media=settings.PHOTO_GAMES_MENU, caption=text)
            await safe_edit_media(
                bot,
                media,
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=coinflip_continue_keyboard(),
            )
        else:
            await cash_out(callback, bot, state)
    else:
        await state.clear()
        new_balance = await db.get_user_balance(user_id)
        text = LEXICON["coinflip_loss"].format(stake=stake, new_balance=new_balance)
        media = InputMediaPhoto(media=settings.PHOTO_GAMES_MENU, caption=text)
        await safe_edit_media(
            bot,
            media,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=coinflip_play_again_keyboard(),
        )


@router.callback_query(
    CoinflipState.game_in_progress, CoinflipCallback.filter(F.action == "continue")
)
async def continue_game_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Обрабатывает нажатие кнопки 'Рискнуть'."""
    await callback.answer()
    if callback.message:
        fsm_data = await state.get_data()
        stake = fsm_data.get("stake", 0)
        text = LEXICON["coinflip_choice_prompt"].format(stake=stake)
        await safe_edit_caption(
            bot,
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=coinflip_choice_keyboard(),
        )


@router.callback_query(
    CoinflipState.game_in_progress, CoinflipCallback.filter(F.action == "cashout")
)
async def cash_out_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Обрабатывает нажатие кнопки 'Забрать выигрыш'."""
    await callback.answer()
    await cash_out(callback, bot, state)


async def cash_out(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Функция для начисления выигрыша и завершения игры."""
    if not callback.message:
        return
    fsm_data = await state.get_data()
    stage_index = fsm_data.get("stage", 0)
    stake = fsm_data.get("stake", 0)
    user_id = callback.from_user.id

    win_stage_index = stage_index - 1
    if win_stage_index < 0:
        await state.clear()
        return

    win_stage = COINFLIP_STAGES[win_stage_index]
    gross_prize = int(stake * win_stage["multiplier"])
    rake = int(gross_prize * (COINFLIP_RAKE_PERCENT / 100))
    prize = gross_prize - rake

    await db.add_balance_with_checks(user_id, prize, "coinflip_win")
    new_balance = await db.get_user_balance(user_id)
    await state.clear()

    text = LEXICON["coinflip_win_final"].format(prize=prize, new_balance=new_balance)
    media = InputMediaPhoto(media=settings.PHOTO_GAMES_MENU, caption=text)

    await safe_edit_media(
        bot,
        media,
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=coinflip_play_again_keyboard(),
    )
