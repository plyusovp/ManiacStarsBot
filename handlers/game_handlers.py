# handlers/game_handlers.py
import asyncio
import secrets
import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from database import db
from economy import COINFLIP_RAKE_PERCENT, COINFLIP_STAGES
from handlers.utils import clean_junk_message, safe_edit_caption
from keyboards.factories import CoinflipCallback, GameCallback
from keyboards.inline import (
    coinflip_continue_keyboard,
    coinflip_play_again_keyboard,
    coinflip_stake_keyboard,
)
from lexicon.texts import LEXICON

router = Router()


class CoinflipState(StatesGroup):
    game_in_progress = State()


@router.callback_query(
    GameCallback.filter((F.name == "coinflip") & (F.action == "start"))
)
async def coinflip_menu_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
) -> None:
    """Отображает меню выбора ставки для Coinflip."""
    await state.clear()
    await clean_junk_message(state, bot)
    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["coinflip_menu"].format(balance=balance)
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
    """Обрабатывает первый бросок после выбора ставки."""
    if not isinstance(callback_data.value, int) or not callback.message:
        return
    stake = callback_data.value
    user_id = callback.from_user.id

    balance = await db.get_user_balance(user_id)
    if balance < stake:
        await callback.answer("Недостаточно средств.", show_alert=True)
        return

    idem_key = f"cf-start-{user_id}-{uuid.uuid4()}"
    spent = await db.spend_balance(user_id, stake, "coinflip_stake", idem_key=idem_key)
    if not spent:
        await callback.answer("Не удалось списать ставку.", show_alert=True)
        return

    await state.set_state(CoinflipState.game_in_progress)
    await state.update_data(stake=stake, stage=0, idem_key=idem_key)

    await safe_edit_caption(
        bot,
        LEXICON["coinflip_process"],
        callback.message.chat.id,
        callback.message.message_id,
    )
    await asyncio.sleep(1.5)

    await process_coinflip_stage(callback, bot, state)


async def process_coinflip_stage(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Обрабатывает текущий этап игры."""
    if not callback.message:
        return
    user_id = callback.from_user.id
    fsm_data = await state.get_data()
    stage_index = fsm_data.get("stage", 0)
    stake = fsm_data.get("stake", 0)

    if stage_index >= len(COINFLIP_STAGES):
        return await cash_out(callback, bot, state)

    current_stage = COINFLIP_STAGES[stage_index]
    is_win = secrets.randbelow(100) < current_stage["chance"]

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
            await safe_edit_caption(
                bot,
                text,
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=coinflip_continue_keyboard(),
            )
        else:
            # Это был последний возможный выигрыш
            await cash_out(callback, bot, state)
    else:
        # Проигрыш
        await state.clear()
        new_balance = await db.get_user_balance(user_id)
        text = LEXICON["coinflip_loss"].format(stake=stake, new_balance=new_balance)
        await safe_edit_caption(
            bot,
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=coinflip_play_again_keyboard(),
        )


@router.callback_query(CoinflipState.game_in_progress, F.data == "cf:continue")
async def continue_game_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Обрабатывает нажатие кнопки 'Рискнуть'."""
    await callback.answer()
    if callback.message:
        await safe_edit_caption(
            bot,
            LEXICON["coinflip_process"],
            callback.message.chat.id,
            callback.message.message_id,
        )
    await asyncio.sleep(1.5)
    await process_coinflip_stage(callback, bot, state)


@router.callback_query(CoinflipState.game_in_progress, F.data == "cf:cashout")
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

    # Индекс этапа указывает на следующий этап, поэтому для выигрыша берем предыдущий
    win_stage_index = stage_index - 1
    if win_stage_index < 0:
        # Это может случиться, если что-то пошло не так
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
    await safe_edit_caption(
        bot,
        text,
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=coinflip_play_again_keyboard(),
    )
