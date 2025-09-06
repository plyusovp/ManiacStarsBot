# handlers/timer_handlers.py
import asyncio
import logging
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import settings
from database import db
from handlers.utils import clean_junk_message, safe_edit_caption
from keyboards.factories import GameCallback, TimerCallback
from keyboards.inline import (
    timer_finish_keyboard,
    timer_game_keyboard,
    timer_searching_keyboard,
    timer_stake_keyboard,
)
from lexicon.texts import LEXICON

router = Router()
logger = logging.getLogger(__name__)

# --- Global Storage ---
timer_queue: dict[int, dict[int, int]] = defaultdict(dict)
active_timers: dict[int, "TimerMatch"] = {}
TIMER_MATCHMAKING_LOCK = asyncio.Lock()


# --- Game State Class ---
@dataclass
class TimerMatch:
    """State of a single 'Star Timer' match."""

    match_id: int
    p1_id: int
    p2_id: int
    stake: int
    target_time: float
    p1_msg_id: Optional[int] = None
    p2_msg_id: Optional[int] = None
    start_time: float = 0.0
    p1_stopped_time: float = 0.0
    p2_stopped_time: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


# --- Core Game Functions ---


async def start_timer_game(
    bot: Bot, p1_id: int, p2_id: int, stake: int, p1_msg_id: int, p2_msg_id: int
):
    """Starts the game: creates a DB entry, sends messages, and starts the timer."""
    result, stop_second = await db.create_timer_match(p1_id, p2_id, stake)
    if not result:
        logger.error(f"Failed to create timer match in DB for {p1_id} and {p2_id}")
        await db.add_balance_unrestricted(p1_id, stake, "timer_refund")
        await db.add_balance_unrestricted(p2_id, stake, "timer_refund")
        await bot.send_message(
            p1_id, "Произошла ошибка при создании игры. Средства возвращены."
        )
        await bot.send_message(
            p2_id, "Произошла ошибка при создании игры. Средства возвращены."
        )
        return

    match_id = result
    target_time = stop_second
    if not match_id or not target_time:
        # Handle case where result might not unpack correctly
        return

    match = TimerMatch(
        match_id, p1_id, p2_id, stake, float(target_time), p1_msg_id, p2_msg_id
    )
    active_timers[match_id] = match

    try:
        p1_chat, p2_chat = await asyncio.gather(
            bot.get_chat(p1_id), bot.get_chat(p2_id)
        )
        p1_username = (
            f"@{p1_chat.username}"
            if p1_chat.username
            else (p1_chat.full_name or "Player 1")
        )
        p2_username = (
            f"@{p2_chat.username}"
            if p2_chat.username
            else (p2_chat.full_name or "Player 2")
        )

    except Exception as e:
        logger.error(f"Could not get timer player info for match {match_id}: {e}")
        if match_id in active_timers:
            del active_timers[match_id]
        return

    text = LEXICON["timer_match_found"].format(
        p1_username=p1_username, p2_username=p2_username, stake=stake
    )
    if p1_msg_id and p2_msg_id:
        await asyncio.gather(
            safe_edit_caption(bot, text + "\n\nПриготовьтесь...", p1_id, p1_msg_id),
            safe_edit_caption(bot, text + "\n\nПриготовьтесь...", p2_id, p2_msg_id),
        )

    await asyncio.sleep(secrets.SystemRandom().uniform(2.5, 4.0))
    if match_id not in active_timers:
        return  # Match was cancelled

    match.start_time = time.time()
    if p1_msg_id and p2_msg_id:
        await asyncio.gather(
            safe_edit_caption(
                bot,
                "🔴 НАЖИМАЙТЕ СТОП!",
                p1_id,
                p1_msg_id,
                reply_markup=timer_game_keyboard(match_id),
            ),
            safe_edit_caption(
                bot,
                "🔴 НАЖИМАЙТЕ СТОП!",
                p2_id,
                p2_msg_id,
                reply_markup=timer_game_keyboard(match_id),
            ),
        )


async def resolve_timer_game(bot: Bot, match_id: int):
    """Resolves the game when both players have pressed 'Stop'."""
    if match_id not in active_timers:
        return
    match = active_timers[match_id]

    async with match.lock:
        if not (match.p1_stopped_time > 0 and match.p2_stopped_time > 0):
            return

        p1_result = match.p1_stopped_time - match.start_time
        p2_result = match.p2_stopped_time - match.start_time
        p1_diff = abs(p1_result - match.target_time)
        p2_diff = abs(p2_result - match.target_time)

        rake = int(match.stake * 2 * (settings.DUEL_RAKE_PERCENT / 100))
        prize = match.stake * 2 - rake
        is_draw = p1_diff == p2_diff

        if is_draw:
            await db.finish_timer_match(match_id=match_id, is_draw=True)
            text = LEXICON["timer_draw"].format(
                target_time=f"{match.target_time:.3f}",
                p1_res=f"{p1_result:.3f}",
                p2_res=f"{p2_result:.3f}",
                stake=match.stake,
            )
        else:
            winner_id, _ = (
                (match.p1_id, match.p2_id)
                if p1_diff < p2_diff
                else (match.p2_id, match.p1_id)
            )
            await db.finish_timer_match(match_id, winner_id=winner_id, new_bank=prize)
            winner_chat = await bot.get_chat(winner_id)
            winner_username = (
                f"@{winner_chat.username}"
                if winner_chat.username
                else winner_chat.full_name or f"Player {winner_id}"
            )
            text = LEXICON["timer_win"].format(
                winner=winner_username,
                target_time=f"{match.target_time:.3f}",
                p1_res=f"{p1_result:.3f}",
                p2_res=f"{p2_result:.3f}",
                prize=prize,
            )

        if match.p1_msg_id:
            await safe_edit_caption(
                bot,
                text,
                match.p1_id,
                match.p1_msg_id,
                reply_markup=timer_finish_keyboard(),
            )
        if match.p2_msg_id:
            await safe_edit_caption(
                bot,
                text,
                match.p2_id,
                match.p2_msg_id,
                reply_markup=timer_finish_keyboard(),
            )

        if match_id in active_timers:
            del active_timers[match_id]


# --- Callback Handlers ---


@router.callback_query(
    GameCallback.filter((F.name == "timer") & (F.action == "start"))
)
async def timer_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Displays the 'Star Timer' game menu."""
    await clean_junk_message(state, bot)
    if not callback.message:
        return
    balance = await db.get_user_balance(callback.from_user.id)
    await safe_edit_caption(
        bot,
        caption=LEXICON["timer_menu"].format(balance=balance),
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=timer_stake_keyboard(),
    )
    await callback.answer()


@router.callback_query(TimerCallback.filter(F.action == "stake"))
async def find_timer_handler(
    callback: CallbackQuery, callback_data: TimerCallback, bot: Bot
):
    """Handles stake selection and starts searching for an opponent."""
    stake = callback_data.value
    if stake is None or not callback.message:
        return await callback.answer("Ошибка: неверная ставка.", show_alert=True)

    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    if balance < stake:
        return await callback.answer("Недостаточно средств.", show_alert=True)

    async with TIMER_MATCHMAKING_LOCK:
        if stake in timer_queue and timer_queue[stake]:
            opponent_id, opponent_msg_id = timer_queue[stake].popitem()
            if opponent_id == user_id:  # Can't play against yourself
                timer_queue[stake][opponent_id] = opponent_msg_id
                return await callback.answer("Вы уже в поиске.", show_alert=True)

            logger.info(
                f"Timer match found! {user_id} vs {opponent_id} with stake {stake}"
            )

            asyncio.create_task(
                start_timer_game(
                    bot,
                    user_id,
                    opponent_id,
                    stake,
                    callback.message.message_id,
                    opponent_msg_id,
                )
            )
        else:
            timer_queue[stake][user_id] = callback.message.message_id
            await safe_edit_caption(
                bot,
                caption=f"🔎 Ищем соперника для игры в таймер со ставкой {stake} ⭐...",
                chat_id=user_id,
                message_id=callback.message.message_id,
                reply_markup=timer_searching_keyboard(),
            )
    await callback.answer()


@router.callback_query(TimerCallback.filter(F.action == "cancel_search"))
async def timer_cancel_search_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
):
    """Cancels the game search."""
    user_id = callback.from_user.id
    async with TIMER_MATCHMAKING_LOCK:
        for stake, players in list(timer_queue.items()):
            if user_id in players:
                del players[user_id]
                if not players:
                    del timer_queue[stake]
                break
    await callback.answer("Поиск отменен.", show_alert=True)
    await timer_menu_handler(callback, state, bot)


@router.callback_query(
    TimerCallback.filter(F.action == "stop"), flags={"throttling_key": "timer_stop"}
)
async def stop_timer_handler(
    callback: CallbackQuery, callback_data: TimerCallback, bot: Bot
):
    """Handles the 'Stop' button press during the game."""
    match_id = callback_data.match_id
    if match_id is None or not callback.message:
        return await callback.answer("Ошибка: игра не найдена.", show_alert=True)
    user_id = callback.from_user.id

    if match_id not in active_timers:
        return await callback.answer("Игра уже завершена.", show_alert=True)
    match = active_timers[match_id]

    async with match.lock:
        is_p1 = user_id == match.p1_id
        if is_p1 and match.p1_stopped_time > 0:
            return await callback.answer("Вы уже остановили таймер.", show_alert=True)
        if not is_p1 and match.p2_stopped_time > 0:
            return await callback.answer("Вы уже остановили таймер.", show_alert=True)

        stopped_time = time.time()
        if is_p1:
            match.p1_stopped_time = stopped_time
        else:
            match.p2_stopped_time = stopped_time

        should_resolve = match.p1_stopped_time > 0 and match.p2_stopped_time > 0

    await callback.message.edit_text("✅ Ваше время принято! Ожидаем соперника...")
    await callback.answer()

    if should_resolve:
        asyncio.create_task(resolve_timer_game(bot, match_id))
