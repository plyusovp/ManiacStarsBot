# handlers/duel_handlers.py
import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import settings
from database import db
from handlers.utils import safe_delete, safe_edit_caption
from keyboards.factories import DuelCallback, GameCallback
from keyboards.inline import (
    back_to_duels_keyboard,
    duel_boost_choice_keyboard,
    duel_game_keyboard,
    duel_searching_keyboard,
    duel_stake_keyboard,
)
from lexicon.texts import LEXICON

router = Router()


# --- Dataclasses for Game State ---
@dataclass
class Player:
    """Represents a player's state in a duel."""

    id: int
    message_id: int
    hand: list[int] = field(default_factory=list)
    played_card: Optional[int] = None
    has_boosted: bool = False
    has_rerolled: bool = False


@dataclass
class DuelMatch:
    """Represents the state of a single duel match."""

    match_id: int
    p1: Player
    p2: Player
    stake: int
    round: int = 1
    p1_wins: int = 0
    p2_wins: int = 0
    turn_started_at: float = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    current_event: Optional[str] = None
    trace_id: Optional[str] = None


# --- Global Storages ---
duel_queue: dict[
    int, tuple[int, int, Optional[str]]
] = {}  # {stake: (user_id, message_id, trace_id)}
active_duels: dict[int, DuelMatch] = {}
DUEL_MATCHMAKING_LOCK = asyncio.Lock()
rand = secrets.SystemRandom()


# --- Core Game Logic ---
def deal_hand() -> list[int]:
    """Deals a new hand of 5 unique cards."""
    return rand.sample(range(1, 11), 5)


async def update_game_interface(
    bot: Bot, match: DuelMatch, text_override: Optional[str] = None
):
    """Updates the game message for both players."""
    event_text = LEXICON.get(match.current_event, "") if match.current_event else ""
    p1_text = text_override or LEXICON["duel_turn"].format(
        round=match.round,
        p1_wins=match.p1_wins,
        p2_wins=match.p2_wins,
        opponent_card="?" if not match.p2.played_card else str(match.p2.played_card),
        event_text=event_text,
    )
    p2_text = text_override or LEXICON["duel_turn"].format(
        round=match.round,
        p1_wins=match.p2_wins,  # Swapped for p2's perspective
        p2_wins=match.p1_wins,
        opponent_card="?" if not match.p1.played_card else str(match.p1.played_card),
        event_text=event_text,
    )

    p1_keyboard = (
        back_to_duels_keyboard()
        if text_override
        else duel_game_keyboard(
            match.match_id,
            match.p1.hand,
            match.p2.id,
            not match.p1.has_boosted,
            not match.p1.has_rerolled,
        )
    )
    p2_keyboard = (
        back_to_duels_keyboard()
        if text_override
        else duel_game_keyboard(
            match.match_id,
            match.p2.hand,
            match.p1.id,
            not match.p2.has_boosted,
            not match.p2.has_rerolled,
        )
    )

    await asyncio.gather(
        safe_edit_caption(
            bot,
            p1_text,
            match.p1.id,
            match.p1.message_id,
            reply_markup=p1_keyboard,
        ),
        safe_edit_caption(
            bot,
            p2_text,
            match.p2.id,
            match.p2.message_id,
            reply_markup=p2_keyboard,
        ),
    )


async def start_new_round(bot: Bot, match: DuelMatch):
    """Starts a new round or ends the game if a winner is decided."""
    if match.p1_wins >= 2 or match.p2_wins >= 2:
        return await resolve_game_end(bot, match)

    match.round += 1
    match.p1.played_card = None
    match.p2.played_card = None
    match.current_event = None

    if rand.random() < 0.1:
        match.current_event = rand.choice(["event_comet", "event_black_hole"])

    await update_game_interface(bot, match)


async def resolve_round(bot: Bot, match: DuelMatch):
    """Resolves the current round after both players have played."""
    p1_card, p2_card = match.p1.played_card, match.p2.played_card
    if p1_card is None or p2_card is None:
        return
    round_winner = None
    round_text = ""

    if match.current_event == "event_black_hole":
        round_text = LEXICON["event_black_hole_triggered"]
    elif p1_card > p2_card:
        match.p1_wins += 1
        round_winner = match.p1
        round_text = f"Игрок {match.p1.id} победил в раунде!"
    elif p2_card > p1_card:
        match.p2_wins += 1
        round_winner = match.p2
        round_text = f"Игрок {match.p2.id} победил в раунде!"
    else:
        round_text = "Ничья в этом раунде!"

    if match.current_event == "event_comet" and round_winner:
        if round_winner.id == match.p1.id:
            match.p1_wins += 1
        else:
            match.p2_wins += 1
        round_text += "\n" + LEXICON["event_comet_triggered"]

    final_text = LEXICON["duel_round_end"].format(
        p1_card=p1_card, p2_card=p2_card, round_result=round_text
    )
    await update_game_interface(bot, match, text_override=final_text)

    await asyncio.sleep(4)
    await start_new_round(bot, match)


async def resolve_game_end(bot: Bot, match: DuelMatch):
    """Ends the game, calculates rewards, and cleans up."""
    if match.match_id not in active_duels:
        return

    extra = {"trace_id": match.trace_id, "match_id": match.match_id}
    winner_id, loser_id = (
        (match.p1.id, match.p2.id)
        if match.p1_wins > match.p2_wins
        else (match.p2.id, match.p1.id)
    )
    rake = int(match.stake * 2 * (settings.DUEL_RAKE_PERCENT / 100))
    prize = match.stake * 2 - rake

    logging.info(f"Duel finished. Winner: {winner_id}, Prize: {prize}", extra=extra)

    await db.finish_duel_atomic(match.match_id, winner_id, loser_id, prize)

    final_text = LEXICON["duel_game_over"].format(
        winner_id=winner_id,
        p1_wins=match.p1_wins,
        p2_wins=match.p2_wins,
        prize=prize,
    )
    await update_game_interface(bot, match, text_override=final_text)

    if match.match_id in active_duels:
        del active_duels[match.match_id]


async def start_duel_game(
    bot: Bot,
    p1_id: int,
    p2_id: int,
    stake: int,
    p1_msg_id: int,
    p2_msg_id: int,
    trace_id: str,
):
    """Initializes and starts a new duel match."""
    match_id = await db.create_duel(p1_id, p2_id, stake)
    if not match_id:
        logging.error(
            f"Failed to create duel in DB for {p1_id} vs {p2_id}",
            extra={"trace_id": trace_id},
        )
        return

    p1 = Player(id=p1_id, message_id=p1_msg_id, hand=deal_hand())
    p2 = Player(id=p2_id, message_id=p2_msg_id, hand=deal_hand())
    match = DuelMatch(match_id=match_id, p1=p1, p2=p2, stake=stake, trace_id=trace_id)
    active_duels[match_id] = match

    logging.info(
        f"Duel game starting. Match ID: {match_id}",
        extra={"trace_id": trace_id, "p1_id": p1_id, "p2_id": p2_id, "stake": stake},
    )
    await update_game_interface(bot, match)


# --- Handlers ---
@router.callback_query(GameCallback.filter(F.name == "duel" and F.action == "start"))
async def duel_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Shows the duel menu with stake options."""
    if not callback.message:
        return
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    stats = await db.get_user_duel_stats(user_id)
    caption = LEXICON["duel_menu"].format(
        balance=balance,
        rake_percent=settings.DUEL_RAKE_PERCENT,
        wins=stats.get("wins", 0),
        losses=stats.get("losses", 0),
    )
    await safe_edit_caption(
        bot,
        caption,
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=duel_stake_keyboard(),
    )


@router.callback_query(DuelCallback.filter(F.action == "stake"))
async def find_duel_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot, data: dict
):
    """Handles stake selection and matchmaking."""
    stake = callback_data.value
    if stake is None or not callback.message:
        return
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    trace_id = data.get("trace_id", "unknown")
    extra = {"trace_id": trace_id, "user_id": user_id, "stake": stake}

    if balance < stake:
        return await callback.answer("Недостаточно средств!", show_alert=True)

    async with DUEL_MATCHMAKING_LOCK:
        if stake in duel_queue:
            opponent_id, opponent_msg_id, opponent_trace_id = duel_queue.pop(stake)
            if opponent_id == user_id:  # Prevent playing against oneself
                duel_queue[stake] = (opponent_id, opponent_msg_id, opponent_trace_id)
                return await callback.answer("Вы уже в поиске.", show_alert=True)

            logging.info(f"Duel match found for stake {stake}", extra=extra)

            await db.spend_balance(
                user_id, stake, "duel_stake_hold", ref_id=str(opponent_id)
            )
            await db.spend_balance(
                opponent_id, stake, "duel_stake_hold", ref_id=str(user_id)
            )

            asyncio.create_task(
                start_duel_game(
                    bot,
                    opponent_id,
                    user_id,
                    stake,
                    opponent_msg_id,
                    callback.message.message_id,
                    trace_id,
                )
            )
        else:
            logging.info("User started duel search", extra=extra)
            if callback.message:
                duel_queue[stake] = (user_id, callback.message.message_id, trace_id)
                await safe_edit_caption(
                    bot,
                    f"🔎 Ищем соперника со ставкой {stake} ⭐...",
                    user_id,
                    callback.message.message_id,
                    reply_markup=duel_searching_keyboard(stake),
                )
    await callback.answer()


@router.callback_query(DuelCallback.filter(F.action == "cancel_search"))
async def cancel_duel_search_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot, data: dict
):
    """Cancels the duel search."""
    stake = callback_data.value
    if stake is None or not callback.message:
        return
    user_id = callback.from_user.id
    extra = {"trace_id": data.get("trace_id"), "user_id": user_id, "stake": stake}

    async with DUEL_MATCHMAKING_LOCK:
        if stake in duel_queue and duel_queue[stake][0] == user_id:
            del duel_queue[stake]
            logging.info("User cancelled duel search", extra=extra)
            await callback.answer("Поиск отменен.", show_alert=True)
            balance = await db.get_user_balance(user_id)
            stats = await db.get_user_duel_stats(user_id)
            caption = LEXICON["duel_menu"].format(
                balance=balance,
                rake_percent=settings.DUEL_RAKE_PERCENT,
                wins=stats.get("wins", 0),
                losses=stats.get("losses", 0),
            )
            await safe_edit_caption(
                bot,
                caption,
                user_id,
                callback.message.message_id,
                reply_markup=duel_stake_keyboard(),
            )
        else:
            logging.warning("Failed to cancel duel search (not in queue?)", extra=extra)
            await callback.answer(
                "Не удалось отменить поиск. Возможно, соперник уже найден.",
                show_alert=True,
            )


@router.callback_query(
    DuelCallback.filter(F.action == "play"), flags={"throttling_key": "spin"}
)
async def play_card_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot
):
    """Handles a player playing a card."""
    match_id = callback_data.match_id
    card_value = callback_data.value
    if match_id is None or card_value is None:
        return

    user_id = callback.from_user.id

    if match_id not in active_duels:
        return await callback.answer(
            "Игра не найдена или уже завершена.", show_alert=True
        )

    match = active_duels[match_id]
    async with match.lock:
        player = match.p1 if user_id == match.p1.id else match.p2
        if player.played_card:
            return await callback.answer(
                "Вы уже сделали ход в этом раунде.", show_alert=True
            )

        if card_value not in player.hand:
            return await callback.answer("У вас нет такой карты!", show_alert=True)

        player.hand.remove(card_value)
        player.played_card = card_value
        await callback.answer(f"Вы сыграли карту {card_value}")

        if match.p1.played_card and match.p2.played_card:
            await resolve_round(bot, match)
        else:
            await update_game_interface(bot, match)


@router.callback_query(DuelCallback.filter(F.action == "boost"))
async def boost_card_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot
):
    """Shows options for which card to boost."""
    match_id = callback_data.match_id
    if match_id is None:
        return
    user_id = callback.from_user.id
    if match_id not in active_duels:
        return await callback.answer("Игра не найдена.", show_alert=True)

    match = active_duels[match_id]
    player = match.p1 if user_id == match.p1.id else match.p2

    if player.has_boosted:
        return await callback.answer("Вы уже использовали усиление.", show_alert=True)

    balance = await db.get_user_balance(user_id)
    if balance < settings.DUEL_BOOST_COST:
        return await callback.answer(
            f"Недостаточно средств. Нужно {settings.DUEL_BOOST_COST} ⭐.",
            show_alert=True,
        )

    await safe_edit_caption(
        bot,
        "Какую карту усилить?",
        user_id,
        player.message_id,
        reply_markup=duel_boost_choice_keyboard(match_id, player.hand),
    )
    await callback.answer()


@router.callback_query(DuelCallback.filter(F.action == "boost_confirm"))
async def boost_confirm_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot
):
    """Confirms and applies the card boost."""
    match_id = callback_data.match_id
    card_to_boost = callback_data.value
    if match_id is None or card_to_boost is None:
        return

    user_id = callback.from_user.id
    if match_id not in active_duels:
        return await callback.answer("Игра не найдена.", show_alert=True)

    match = active_duels[match_id]
    async with match.lock:
        player = match.p1 if user_id == match.p1.id else match.p2
        if player.has_boosted or card_to_boost not in player.hand:
            # Silently update interface to prevent exploit
            return await update_game_interface(bot, match)

        await db.spend_balance(
            user_id, settings.DUEL_BOOST_COST, "duel_boost", ref_id=str(match_id)
        )

        card_index = player.hand.index(card_to_boost)
        player.hand[card_index] += 2
        player.has_boosted = True

        await callback.answer(
            f"Карта {card_to_boost} усилена до {player.hand[card_index]}!",
            show_alert=True,
        )
        await update_game_interface(bot, match)


@router.callback_query(DuelCallback.filter(F.action == "boost_cancel"))
async def boost_cancel_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot
):
    """Cancels the boost selection."""
    match_id = callback_data.match_id
    if not match_id or match_id not in active_duels:
        return await callback.answer("Игра не найдена.", show_alert=True)
    await callback.answer()
    await update_game_interface(bot, active_duels[match_id])


@router.callback_query(DuelCallback.filter(F.action == "reroll"))
async def reroll_hand_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot
):
    """Rerolls the player's hand."""
    match_id = callback_data.match_id
    if match_id is None:
        return
    user_id = callback.from_user.id
    if match_id not in active_duels:
        return await callback.answer("Игра не найдена.", show_alert=True)

    match = active_duels[match_id]
    async with match.lock:
        player = match.p1 if user_id == match.p1.id else match.p2
        if player.has_rerolled:
            return await callback.answer("Вы уже меняли руку.", show_alert=True)

        balance = await db.get_user_balance(user_id)
        if balance < settings.DUEL_REROLL_COST:
            return await callback.answer(
                f"Недостаточно средств. Нужно {settings.DUEL_REROLL_COST} ⭐.",
                show_alert=True,
            )

        await db.spend_balance(
            user_id, settings.DUEL_REROLL_COST, "duel_reroll", ref_id=str(match_id)
        )
        player.hand = deal_hand()
        player.has_rerolled = True

        await callback.answer("Ваша рука была обновлена!", show_alert=True)
        await update_game_interface(bot, match)


@router.callback_query(DuelCallback.filter(F.action == "surrender"))
async def surrender_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot
):
    """Handles a player surrendering."""
    match_id = callback_data.match_id
    if not match_id or match_id not in active_duels:
        return await callback.answer("Игра уже завершена.", show_alert=True)

    match = active_duels[match_id]

    extra = {
        "trace_id": match.trace_id,
        "user_id": callback.from_user.id,
        "match_id": match_id,
    }
    logging.info("Player surrendered", extra=extra)

    # Force win for the opponent
    if match.p1.id == callback.from_user.id:
        match.p2_wins = 2
        match.p1_wins = 0
    else:
        match.p1_wins = 2
        match.p2_wins = 0

    await resolve_game_end(bot, match)
    await callback.answer("Вы сдались.", show_alert=True)


# --- Cleanup and Maintenance ---
@router.callback_query(DuelCallback.filter(F.action == "stuck"))
async def duel_stuck_handler(callback: CallbackQuery, bot: Bot):
    """Handles the 'stuck game' button, cleaning up old games."""
    # This is a simple cleanup, more advanced logic could be added
    cleaned_count = 0
    for match_id in list(active_duels.keys()):
        # Simple heuristic: if a game is older than 5 mins, it's stuck
        if (
            asyncio.get_event_loop().time() - active_duels[match_id].turn_started_at
        ) > 300:
            del active_duels[match_id]
            cleaned_count += 1
    await callback.answer(
        f"Очищено {cleaned_count} зависших игр. Попробуйте найти игру снова.",
        show_alert=True,
    )
    if callback.message:
        await safe_delete(bot, callback.message.chat.id, callback.message.message_id)
