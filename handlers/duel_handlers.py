# handlers/duel_handlers.py
import asyncio
import logging
import random
from dataclasses import dataclass, field
from typing import List, Optional

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import settings
from database import db
from handlers.utils import clean_junk_message
from keyboards.inline import (
    back_to_duels_keyboard,
    duel_boost_choice_keyboard,
    duel_finish_keyboard,
    duel_round_keyboard,
    duel_searching_keyboard,
    duel_stake_keyboard,
    duel_stuck_keyboard,
    duel_surrender_confirm_keyboard,
)
from lexicon.texts import LEXICON

router = Router()
logger = logging.getLogger(__name__)

# --- Константы и Глобальные Хранилища ---
HAND_SIZE = 5
CARD_POOL = range(1, 11)
ROUND_TIMEOUT_SEC = 30
REVEAL_DELAY_SEC = 3
TIMEOUT_CHOICE = -1  # Специальное значение для таймаута

# Глобальные хранилища состояния
duel_queue: dict[int, dict] = {}
active_duels: dict[int, "DuelMatch"] = {}
rematch_offers: dict[int, dict] = {}

# --- НОВОЕ: Глобальный лок для предотвращения гонок состояний ---
MATCHMAKING_LOCK = asyncio.Lock()


@dataclass
class DuelMatch:
    match_id: int
    p1_id: int
    p2_id: int
    stake: int
    p1_message_id: Optional[int] = None
    p2_message_id: Optional[int] = None
    p1_hand: List[int] = field(
        default_factory=lambda: random.sample(CARD_POOL, HAND_SIZE)
    )
    p2_hand: List[int] = field(
        default_factory=lambda: random.sample(CARD_POOL, HAND_SIZE)
    )
    p1_wins: int = 0
    p2_wins: int = 0
    current_round: int = 1
    p1_choice: Optional[int] = None
    p2_choice: Optional[int] = None
    p1_boosts_left: int = 1
    p2_boosts_left: int = 1
    p1_replace_left: int = 1
    p2_replace_left: int = 1
    bonus_pool: int = 0
    current_round_special: Optional[str] = None
    # --- ИЗМЕНЕНО: Храним задачи таймеров для их отмены ---
    p1_timer_task: Optional[asyncio.Task] = None
    p2_timer_task: Optional[asyncio.Task] = None
    is_resolving: bool = False  # Флаг, чтобы избежать двойного разрешения раунда
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def cancel_timers(self) -> None:
        """Безопасно отменяет все активные таймеры для этого матча."""
        for task in (self.p1_timer_task, self.p2_timer_task):
            if task and not task.done():
                task.cancel()
        self.p1_timer_task = None
        self.p2_timer_task = None


# --- Вспомогательные функции (Сервисы) ---


async def cleanup_match(match_id: int, reason: str):
    """Централизованная функция для очистки состояния матча."""
    async with MATCHMAKING_LOCK:
        if match_id in active_duels:
            match = active_duels.pop(match_id)
            match.cancel_timers()
            logger.info(f"Дуэль {match_id} завершена и очищена. Причина: {reason}.")
        if match_id in rematch_offers:
            del rematch_offers[match_id]


def parse_cb_data(data: str, prefix: str, expected_parts: int) -> Optional[list]:
    if not data.startswith(prefix):
        return None
    parts = data.split(":")
    if len(parts) != expected_parts:
        return None
    return parts


async def edit_caption_safe(
    bot: Bot, chat_id: int, message_id: Optional[int], caption: str, kb=None
) -> bool:
    if message_id is None:
        return False
    try:
        await bot.edit_message_caption(
            chat_id=chat_id, message_id=message_id, caption=caption, reply_markup=kb
        )
        return True
    except TelegramBadRequest:
        logger.warning("Сообщение %s не найдено или не изменено.", message_id)
        return False
    except Exception as e:
        logger.exception("Необработанная ошибка в edit_caption_safe: %s", e)
        return False


def roll_special_card() -> Optional[str]:
    roll = random.randint(1, 100)
    if roll <= 8:
        return "black_hole"
    if roll <= 18:
        return "comet"
    return None


def show_card(x: int) -> str:
    return str(x) if x != TIMEOUT_CHOICE else "Таймаут"


async def on_player_timeout(bot: Bot, match: DuelMatch, player_role: str) -> None:
    """Обработчик таймаута игрока."""
    async with match.lock:
        if match.is_resolving:
            return

        # Устанавливаем выбор по таймауту только если игрок еще не сделал ход
        if player_role == "p1" and match.p1_choice is None:
            match.p1_choice = TIMEOUT_CHOICE
            timed_out_id, other_id = match.p1_id, match.p2_id
        elif player_role == "p2" and match.p2_choice is None:
            match.p2_choice = TIMEOUT_CHOICE
            timed_out_id, other_id = match.p2_id, match.p1_id
        else:
            return  # Игрок уже сделал ход, таймаут неактуален

    try:
        await bot.send_message(timed_out_id, LEXICON["duel_timeout_you"])
        await bot.send_message(other_id, LEXICON["duel_timeout_opponent"])
    except Exception:
        logger.warning("Не удалось уведомить о таймауте")

    # Если оба игрока сделали ход (один из них по таймауту), разрешаем раунд
    if match.p1_choice is not None and match.p2_choice is not None:
        await resolve_round(bot, match)


def start_turn_timer(bot: Bot, match: DuelMatch, role: str) -> None:
    """Создает и сохраняет задачу таймаута для игрока."""

    async def _timer_task():
        try:
            await asyncio.sleep(ROUND_TIMEOUT_SEC)
            await on_player_timeout(bot, match, role)
        except asyncio.CancelledError:
            pass  # Это нормальное завершение при отмене таймера
        except Exception as e:
            logger.exception(
                f"Ошибка в таймере для match={match.match_id}, role={role}: {e}"
            )

    task = asyncio.create_task(_timer_task())
    if role == "p1":
        match.p1_timer_task = task
    else:
        match.p2_timer_task = task


async def refresh_round_ui(bot: Bot, match: DuelMatch) -> None:
    """Обновляет интерфейс для обоих игроков."""
    async with match.lock:
        special_text = (
            LEXICON.get(f"duel_{match.current_round_special}_active", "")
            if match.current_round_special
            else ""
        )
        score_text = f"Счёт: <b>{match.p1_wins} - {match.p2_wins}</b> (до 2 побед)"
        text = LEXICON.get("duel_round_interface", "Раунд {round}\n{score}\n{special}")
        p1_text = text.format(
            round=match.current_round, score=score_text, special=special_text
        )
        p2_text = text.format(
            round=match.current_round, score=score_text, special=special_text
        )
        p1_kb = duel_round_keyboard(
            match.p1_hand, match.match_id, match.p1_boosts_left, match.p1_replace_left
        )
        p2_kb = duel_round_keyboard(
            match.p2_hand, match.match_id, match.p2_boosts_left, match.p2_replace_left
        )
        p1_id, p2_id = match.p1_id, match.p2_id
        p1_msg, p2_msg = match.p1_message_id, match.p2_message_id

    await asyncio.gather(
        edit_caption_safe(bot, p1_id, p1_msg, p1_text, p1_kb),
        edit_caption_safe(bot, p2_id, p2_msg, p2_text, p2_kb),
    )


async def send_round_interface(bot: Bot, match: DuelMatch) -> None:
    """Начинает новый раунд, сбрасывает состояния и запускает таймеры."""
    async with match.lock:
        match.cancel_timers()
        match.p1_choice, match.p2_choice = None, None
        match.p1_boosts_left, match.p2_boosts_left = 1, 1
        match.p1_replace_left, match.p2_replace_left = 1, 1
        match.current_round_special = roll_special_card()
        match.is_resolving = False
        round_no = match.current_round

    try:
        await db.create_duel_round(match.match_id, round_no)
    except Exception:
        logger.exception("DB: create_duel_round failed")

    await refresh_round_ui(bot, match)
    start_turn_timer(bot, match, "p1")
    start_turn_timer(bot, match, "p2")


async def resolve_round(bot: Bot, match: DuelMatch) -> None:
    """Разрешает исход раунда, когда оба игрока сделали ход."""
    async with match.lock:
        if match.is_resolving:
            return
        if not (match.p1_choice is not None and match.p2_choice is not None):
            return
        match.is_resolving = True
        match.cancel_timers()

        special = match.current_round_special
        p1_card, p2_card = match.p1_choice, match.p2_choice
        round_no = match.current_round
        p1_id, p2_id = match.p1_id, match.p2_id
        p1_msg, p2_msg = match.p1_message_id, match.p2_message_id

        if special == "black_hole":
            round_winner = "void"
        else:
            if p1_card == TIMEOUT_CHOICE and p2_card == TIMEOUT_CHOICE:
                round_winner = "draw"
            elif p1_card == TIMEOUT_CHOICE:
                round_winner = "p2"
            elif p2_card == TIMEOUT_CHOICE:
                round_winner = "p1"
            elif p1_card > p2_card:
                round_winner = "p1"
            elif p2_card > p1_card:
                round_winner = "p2"
            else:
                round_winner = "draw"

        comet_bonus = 0
        if special == "comet" and round_winner not in ["draw", "void"]:
            match.bonus_pool += match.stake
            comet_bonus = match.stake

        if round_winner == "p1":
            match.p1_wins += 1
        elif round_winner == "p2":
            match.p2_wins += 1

        is_over = match.p1_wins >= 2 or match.p2_wins >= 2 or len(match.p1_hand) == 0

    # --- Логика отображения и сохранения вынесена из-под лока ---

    if round_winner == "void":
        await db.save_duel_round(
            match.match_id, round_no, p1_card, p2_card, "void", "black_hole"
        )
        await asyncio.gather(
            edit_caption_safe(bot, p1_id, p1_msg, LEXICON["duel_blackhole_triggered"]),
            edit_caption_safe(bot, p2_id, p2_msg, LEXICON["duel_blackhole_triggered"]),
        )
    else:
        p1_result_text = (
            LEXICON["duel_round_win"]
            if round_winner == "p1"
            else (
                LEXICON["duel_round_loss"]
                if round_winner == "p2"
                else LEXICON["duel_round_draw"]
            )
        )
        p2_result_text = (
            LEXICON["duel_round_win"]
            if round_winner == "p2"
            else (
                LEXICON["duel_round_loss"]
                if round_winner == "p1"
                else LEXICON["duel_round_draw"]
            )
        )
        p1_reveal = LEXICON["duel_reveal"].format(
            p1_card=show_card(p1_card),
            p2_card=show_card(p2_card),
            result=p1_result_text,
            comet_text=(
                LEXICON["duel_comet_triggered"].format(bonus=comet_bonus)
                if comet_bonus
                else ""
            ),
        )
        p2_reveal = LEXICON["duel_reveal"].format(
            p1_card=show_card(p2_card),
            p2_card=show_card(p1_card),
            result=p2_result_text,
            comet_text=(
                LEXICON["duel_comet_triggered"].format(bonus=comet_bonus)
                if comet_bonus
                else ""
            ),
        )

        await db.save_duel_round(
            match.match_id, round_no, p1_card, p2_card, round_winner, special
        )
        await asyncio.gather(
            edit_caption_safe(bot, p1_id, p1_msg, p1_reveal),
            edit_caption_safe(bot, p2_id, p2_msg, p2_reveal),
        )

    await asyncio.sleep(REVEAL_DELAY_SEC)

    if is_over:
        await resolve_match(bot, match)
    else:
        async with match.lock:
            match.current_round += 1
        await send_round_interface(bot, match)


async def resolve_match(
    bot: Bot, match: DuelMatch, surrendered_player_id: Optional[int] = None
) -> None:
    """Завершает матч, распределяет награды и вызывает очистку."""
    async with match.lock:
        if match.is_resolving:  # Предотвращаем двойное завершение
            return
        match.is_resolving = True

        winner_id, loser_id, is_draw = None, None, False

        if surrendered_player_id:
            winner_id = (
                match.p2_id if surrendered_player_id == match.p1_id else match.p1_id
            )
            loser_id = surrendered_player_id
        elif match.p1_wins > match.p2_wins:
            winner_id, loser_id = match.p1_id, match.p2_id
        elif match.p2_wins > match.p1_wins:
            winner_id, loser_id = match.p2_id, match.p1_id
        else:
            is_draw = True
            winner_id, loser_id = match.p1_id, match.p2_id

        p1_id, p2_id, p1_msg, p2_msg = (
            match.p1_id,
            match.p2_id,
            match.p1_message_id,
            match.p2_message_id,
        )
        score_text = f"{match.p1_wins}:{match.p2_wins}"
        bank = match.stake * 2
        rake = int(bank * (settings.DUEL_RAKE_PERCENT / 100))
        prize = bank - rake + match.bonus_pool

    # --- Взаимодействие с БД и Telegram API вне лока ---

    await db.finish_duel_atomic(
        match.match_id, winner_id, loser_id, prize, is_draw, match.stake
    )

    if not is_draw:
        winner_text = LEXICON["duel_win"].format(
            score=score_text, prize=prize, bank=bank, rake=rake, bonus=match.bonus_pool
        )
        loser_text = LEXICON["duel_loss"].format(score=score_text)
        if surrendered_player_id:
            winner_text = LEXICON["duel_win_surrender"].format(prize=prize)
            loser_text = LEXICON["duel_loss_surrender"].format(stake=match.stake)

        await asyncio.gather(
            edit_caption_safe(
                bot,
                winner_id,
                p1_msg if winner_id == p1_id else p2_msg,
                winner_text,
                duel_finish_keyboard(match.match_id, loser_id),
            ),
            edit_caption_safe(
                bot,
                loser_id,
                p1_msg if loser_id == p1_id else p2_msg,
                loser_text,
                duel_finish_keyboard(match.match_id, winner_id),
            ),
        )
    else:
        draw_text = LEXICON["duel_draw"].format(score=score_text)
        await asyncio.gather(
            edit_caption_safe(
                bot,
                p1_id,
                p1_msg,
                draw_text,
                duel_finish_keyboard(match.match_id, p2_id),
            ),
            edit_caption_safe(
                bot,
                p2_id,
                p2_msg,
                draw_text,
                duel_finish_keyboard(match.match_id, p1_id),
            ),
        )

    await cleanup_match(match.match_id, "match_resolved")


async def start_match(
    bot: Bot,
    match_id: int,
    p1_id: int,
    p2_id: int,
    stake: int,
    p1_msg_id: int,
    p2_msg_id: int,
) -> None:
    """Создает объект матча и запускает обратный отсчет."""
    match = DuelMatch(
        match_id, p1_id, p2_id, stake, p1_message_id=p1_msg_id, p2_message_id=p2_msg_id
    )

    async with MATCHMAKING_LOCK:
        active_duels[match_id] = match

    try:
        p1 = await bot.get_chat(p1_id)
        p2 = await bot.get_chat(p2_id)
        p1_username = f"@{p1.username}" if p1.username else p1.full_name
        p2_username = f"@{p2.username}" if p2.username else p2.full_name
    except Exception:
        logger.exception(
            "Не удалось получить информацию об игроках для матча %s", match_id
        )
        await cleanup_match(match_id, "get_chat_failed")
        return

    base_text = LEXICON["duel_match_found"].format(
        p1_username=p1_username, p2_username=p2_username, stake=stake
    )

    for i in range(5, 0, -1):
        if match_id not in active_duels:  # Проверяем, не был ли матч отменен
            return
        countdown_text = base_text + LEXICON["duel_countdown"].format(seconds=i)
        await asyncio.gather(
            edit_caption_safe(bot, p1_id, p1_msg_id, countdown_text),
            edit_caption_safe(bot, p2_id, p2_msg_id, countdown_text),
        )
        if i > 1:
            await asyncio.sleep(1)

    if match_id in active_duels:
        await send_round_interface(bot, match)


# --- Хендлеры ---


@router.callback_query(F.data == "game_duel")
async def duel_menu_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await clean_junk_message(callback, state)
    if await db.is_user_in_active_duel(callback.from_user.id):
        text = "Вы уже находитесь в активной дуэли."
        await edit_caption_safe(
            callback.bot,
            callback.message.chat.id,
            callback.message.message_id,
            text,
            duel_stuck_keyboard(),
        )
        return

    balance = await db.get_user_balance(callback.from_user.id)
    stats = await db.get_user_duel_stats(callback.from_user.id)
    text = LEXICON["duel_menu"].format(
        balance=balance, wins=stats["wins"], losses=stats["losses"]
    )
    await edit_caption_safe(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        duel_stake_keyboard(),
    )


@router.callback_query(F.data == "duel_rules")
async def duel_rules_handler(callback: CallbackQuery) -> None:
    await edit_caption_safe(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        LEXICON["duel_rules"],
        back_to_duels_keyboard(),
    )


@router.callback_query(F.data.startswith("duel_stake:"))
async def find_duel_handler(callback: CallbackQuery, bot: Bot) -> None:
    parts = parse_cb_data(callback.data, "duel_stake:", 2)
    if not parts:
        return await callback.answer("Ошибка данных.")
    stake = int(parts[1])
    user_id = callback.from_user.id

    async with MATCHMAKING_LOCK:
        if user_id in [data["user_id"] for data in duel_queue.values()]:
            return await callback.answer(
                "Вы уже находитесь в поиске игры.", show_alert=True
            )

        opponent_data = duel_queue.get(stake)
        if opponent_data and opponent_data["user_id"] != user_id:
            del duel_queue[stake]
            opponent_id, opponent_msg_id = (
                opponent_data["user_id"],
                opponent_data["msg_id"],
            )
            # Выходим из-под лока, чтобы создать матч
        else:
            duel_queue[stake] = {
                "user_id": user_id,
                "msg_id": callback.message.message_id,
            }
            await edit_caption_safe(
                bot,
                callback.message.chat.id,
                callback.message.message_id,
                f"🔎 Ищем соперника со ставкой {stake} ⭐...",
                duel_searching_keyboard(),
            )
            return

    # Если нашли оппонента, создаем матч
    match_id = await db.create_duel_atomic(
        opponent_id, user_id, stake, idem_key=callback.id
    )
    if not match_id:
        await callback.answer(
            "У одного из игроков недостаточно средств! Игра отменена.", show_alert=True
        )
        await edit_caption_safe(
            bot,
            opponent_id,
            opponent_msg_id,
            "У вашего оппонента оказалось недостаточно средств для ставки, игра отменена.",
            duel_stake_keyboard(),
        )
        return

    await edit_caption_safe(
        bot,
        callback.message.chat.id,
        callback.message.message_id,
        "✅ Соперник найден! Загрузка лобби...",
    )
    await start_match(
        bot,
        match_id,
        opponent_id,
        user_id,
        stake,
        opponent_msg_id,
        callback.message.message_id,
    )


@router.callback_query(F.data == "duel_cancel_search")
async def duel_cancel_search_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    user_id = callback.from_user.id
    async with MATCHMAKING_LOCK:
        for stake, data in list(duel_queue.items()):
            if data["user_id"] == user_id:
                del duel_queue[stake]
                break
    await callback.answer("Поиск отменён.", show_alert=True)
    await duel_menu_handler(callback, state)


@router.callback_query(F.data.startswith("duel_play:"))
async def duel_play_handler(callback: CallbackQuery, bot: Bot) -> None:
    parts = parse_cb_data(callback.data, "duel_play:", 4)
    if not parts:
        return await callback.answer("Ошибка данных.")
    _, match_id_str, card_value_str, original_value_str = parts
    match_id, card_value, original_value = (
        int(match_id_str),
        int(card_value_str),
        int(original_value_str),
    )

    user_id = callback.from_user.id
    match = active_duels.get(match_id)
    if not match:
        return await callback.answer("Ошибка: матч не найден.", show_alert=True)
    if user_id not in (match.p1_id, match.p2_id):
        return await callback.answer("Это не ваш матч.", show_alert=True)

    async with match.lock:
        if match.is_resolving:
            return await callback.answer("Раунд уже завершается.")

        player_role = "p1" if user_id == match.p1_id else "p2"
        choice_attr, hand_attr, timer_attr = (
            f"{player_role}_choice",
            f"{player_role}_hand",
            f"{player_role}_timer_task",
        )

        if getattr(match, choice_attr) is not None:
            return await callback.answer("Вы уже сделали ход.")

        player_hand: List = getattr(match, hand_attr)
        card_to_find = next(
            (
                c
                for c in player_hand
                if (isinstance(c, tuple) and c[1] == original_value)
                or c == original_value
            ),
            None,
        )
        if card_to_find is None:
            return await callback.answer("У вас нет такой карты!")

        # Отменяем таймер игрока, т.к. он сделал ход
        timer = getattr(match, timer_attr)
        if timer and not timer.done():
            timer.cancel()

        setattr(match, choice_attr, card_value)
        player_hand.remove(card_to_find)

        need_resolve = match.p1_choice is not None and match.p2_choice is not None

    await edit_caption_safe(
        bot,
        callback.message.chat.id,
        callback.message.message_id,
        "✅ Ваш ход принят. Ожидаем соперника...",
    )
    await callback.answer()

    if need_resolve:
        await resolve_round(bot, match)


# ... (остальные хендлеры duel_handlers.py без изменений: duel_replace, duel_boost, surrender и т.д.)
# Важно: в них нужно использовать `active_duels.get(match_id)` для безопасного доступа к матчу.
# Пример для duel_surrender_confirm_handler:
@router.callback_query(F.data.startswith("duel_surrender_confirm:"))
async def duel_surrender_confirm_handler(callback: CallbackQuery, bot: Bot) -> None:
    parts = parse_cb_data(callback.data, "duel_surrender_confirm:", 2)
    if not parts:
        return await callback.answer("Ошибка данных.")
    match_id = int(parts[1])
    user_id = callback.from_user.id

    match = active_duels.get(match_id)
    if not match:
        return await callback.answer("Матч уже завершен.", show_alert=True)

    await resolve_match(bot, match, surrendered_player_id=user_id)


@router.callback_query(F.data.startswith("duel_replace:"))
async def duel_replace_handler(callback: CallbackQuery, bot: Bot) -> None:
    parts = parse_cb_data(callback.data, "duel_replace:", 2)
    if not parts:
        return await callback.answer("Ошибка данных.")
    match_id = int(parts[1])

    user_id = callback.from_user.id
    match = active_duels.get(match_id)
    if not match:
        return

    async with match.lock:
        is_p1 = user_id == match.p1_id
        if not is_p1 and user_id != match.p2_id:
            return await callback.answer("Это не ваш матч.", show_alert=True)

        already_played = (
            (match.p1_choice is not None) if is_p1 else (match.p2_choice is not None)
        )
        if already_played:
            return await callback.answer(
                "Ход уже сделан — заменить карту нельзя.", show_alert=True
            )

        replaces_left = match.p1_replace_left if is_p1 else match.p2_replace_left
        if replaces_left < 1:
            return await callback.answer(
                "Ты уже заменял карту в этом раунде.", show_alert=True
            )

        player_hand = match.p1_hand if is_p1 else match.p2_hand
        if not player_hand:
            return await callback.answer("Не из чего менять.", show_alert=True)

        current_vals = [c[1] if isinstance(c, tuple) else c for c in player_hand]
        available_pool = [c for c in range(1, 11) if c not in current_vals]
        if not available_pool:
            return await callback.answer(
                "Сейчас заменить нельзя — нет доступных чисел.", show_alert=True
            )

    ok = await db.spend_balance(
        user_id, 2, "duel_replace_card", ref_id=f"duel:{match_id}", idem_key=callback.id
    )
    if not ok:
        return await callback.answer(
            "Недостаточно звёзд для замены (нужно 2 ⭐).", show_alert=True
        )

    async with match.lock:
        card_to_replace = random.choice(player_hand)
        player_hand.remove(card_to_replace)

        current_vals_after_removal = [
            c[1] if isinstance(c, tuple) else c for c in player_hand
        ]
        pool = [c for c in range(1, 11) if c not in current_vals_after_removal]

        new_card = random.choice(pool)
        player_hand.append(new_card)

        if is_p1:
            match.p1_replace_left = 0
        else:
            match.p2_replace_left = 0
        old_val = (
            card_to_replace[1]
            if isinstance(card_to_replace, tuple)
            else card_to_replace
        )

    await callback.answer(f"🔄 Карта {old_val} заменена на {new_card}!")
    await refresh_round_ui(bot, match)


@router.callback_query(F.data.startswith("duel_boost:"))
async def duel_boost_handler(callback: CallbackQuery, bot: Bot) -> None:
    parts = parse_cb_data(callback.data, "duel_boost:", 2)
    if not parts:
        return await callback.answer("Ошибка данных.")
    match_id = int(parts[1])

    user_id = callback.from_user.id
    match = active_duels.get(match_id)
    if not match:
        return

    async with match.lock:
        is_p1 = user_id == match.p1_id
        if not is_p1 and user_id != match.p2_id:
            return await callback.answer("Это не ваш матч.", show_alert=True)

        already_played = (
            (match.p1_choice is not None) if is_p1 else (match.p2_choice is not None)
        )
        if already_played:
            return await callback.answer(
                "Ход уже сделан — усиливать нельзя.", show_alert=True
            )

        boosts_left = match.p1_boosts_left if is_p1 else match.p2_boosts_left
        if boosts_left < 1:
            return await callback.answer(
                "У тебя не осталось усилений в этом раунде.", show_alert=True
            )

        player_hand = match.p1_hand if is_p1 else match.p2_hand

    await edit_caption_safe(
        bot,
        callback.message.chat.id,
        callback.message.message_id,
        "Какую карту усилить? (+1 к силе за 1 ⭐)",
        duel_boost_choice_keyboard(player_hand, match_id),
    )


@router.callback_query(F.data.startswith("duel_boost_choice:"))
async def duel_boost_choice_handler(callback: CallbackQuery, bot: Bot) -> None:
    parts = parse_cb_data(callback.data, "duel_boost_choice:", 3)
    if not parts:
        return await callback.answer("Ошибка данных.")
    _, match_id_str, card_str = parts
    match_id, card_to_boost_original = int(match_id_str), int(card_str)

    user_id = callback.from_user.id
    match = active_duels.get(match_id)
    if not match:
        return

    async with match.lock:
        is_p1 = user_id == match.p1_id
        if not is_p1 and user_id != match.p2_id:
            return await callback.answer("Это не ваш матч.", show_alert=True)

        already_played = (
            (match.p1_choice is not None) if is_p1 else (match.p2_choice is not None)
        )
        if already_played:
            return await callback.answer(
                "Ход уже сделан — усиливать нельзя.", show_alert=True
            )

        boosts_left = match.p1_boosts_left if is_p1 else match.p2_boosts_left
        if boosts_left < 1:
            return await callback.answer(
                "У тебя не осталось усилений в этом раунде.", show_alert=True
            )

    ok = await db.spend_balance(
        user_id, 1, "duel_boost_card", ref_id=f"duel:{match_id}", idem_key=callback.id
    )
    if not ok:
        return await callback.answer(
            "Недостаточно звёзд для усиления (нужно 1 ⭐).", show_alert=True
        )

    boosted_value = 0
    card_found = False
    async with match.lock:
        player_hand = match.p1_hand if is_p1 else match.p2_hand
        for i, card in enumerate(player_hand):
            original_value = card[1] if isinstance(card, tuple) else card
            if original_value == card_to_boost_original:
                current_value = card[0] if isinstance(card, tuple) else card
                boosted_value = current_value + 1
                player_hand[i] = (boosted_value, original_value)
                card_found = True
                break

        if not card_found:
            await db.add_balance_unrestricted(
                user_id, 1, "duel_boost_refund", ref_id=f"duel:{match_id}"
            )
            return await callback.answer("Ошибка: карта для усиления не найдена.")

        if is_p1:
            match.p1_boosts_left -= 1
        else:
            match.p2_boosts_left -= 1

    await callback.answer(
        f"⚡ Карта {card_to_boost_original} усилена до {boosted_value}!"
    )
    await refresh_round_ui(bot, match)


@router.callback_query(F.data.startswith("duel_cancel_action:"))
async def duel_cancel_action_handler(callback: CallbackQuery, bot: Bot) -> None:
    parts = parse_cb_data(callback.data, "duel_cancel_action:", 2)
    if not parts:
        return await callback.answer("Ошибка данных.")
    match_id = int(parts[1])
    match = active_duels.get(match_id)
    if not match:
        return
    await refresh_round_ui(bot, match)


@router.callback_query(F.data.startswith("duel_surrender:"))
async def duel_surrender_handler(callback: CallbackQuery) -> None:
    parts = parse_cb_data(callback.data, "duel_surrender:", 2)
    if not parts:
        return await callback.answer("Ошибка данных.")
    match_id = int(parts[1])
    await edit_caption_safe(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        "Ты уверен, что хочешь сдаться? Ты проиграешь свою ставку.",
        duel_surrender_confirm_keyboard(match_id),
    )


@router.callback_query(F.data == "duel_leave_active")
async def duel_leave_active_handler(
    callback: CallbackQuery, bot: Bot, state: FSMContext
) -> None:
    user_id = callback.from_user.id
    match_id = await db.get_active_duel_id(user_id)

    if not match_id:
        await callback.answer("Не найдено активных игр.", show_alert=True)
        return await duel_menu_handler(callback, state)

    match = active_duels.get(match_id)
    if match:
        await resolve_match(bot, match, surrendered_player_id=user_id)
    else:
        # Если матча нет в памяти, но есть в БД - это "зависшая" игра
        logger.warning(
            f"Принудительное завершение зависшей дуэли {match_id} для пользователя {user_id}"
        )
        await db.force_surrender_duel(match_id, user_id)
        await cleanup_match(match_id, "stuck_game_cleanup")
        await callback.answer(
            "Ваша 'зависшая' игра была принудительно завершена. Ставка списана.",
            show_alert=True,
        )
    await duel_menu_handler(callback, state)


@router.callback_query(F.data.startswith("duel_rematch:"))
async def duel_rematch_handler(callback: CallbackQuery, bot: Bot) -> None:
    parts = parse_cb_data(callback.data, "duel_rematch:", 3)
    if not parts:
        return await callback.answer("Ошибка данных.")
    _, old_match_id, opponent_id = map(int, parts)
    user_id = callback.from_user.id

    # Проверяем, что реванш не для активной игры
    if old_match_id in active_duels:
        return await callback.answer(
            "Нельзя начать реванш, пока предыдущая игра не завершена.", show_alert=True
        )

    details = await db.get_duel_details_for_rematch(old_match_id)
    if (
        not details
        or user_id not in (details["p1_id"], details["p2_id"])
        or opponent_id not in (details["p1_id"], details["p2_id"])
    ):
        return await callback.answer(
            "Не удалось найти данные для реванша.", show_alert=True
        )

    stake = details["stake"]

    async with MATCHMAKING_LOCK:
        if (
            old_match_id in rematch_offers
            and rematch_offers[old_match_id]["user_id"] != user_id
        ):
            # Оппонент уже предложил реванш, принимаем
            offer = rematch_offers.pop(old_match_id)
            p1_id, p2_id = offer["user_id"], user_id
            opponent_msg_id = offer["msg_id"]
        else:
            # Предлагаем реванш
            rematch_offers[old_match_id] = {
                "user_id": user_id,
                "msg_id": callback.message.message_id,
            }
            await edit_caption_safe(
                bot,
                user_id,
                callback.message.message_id,
                "✅ Запрос на реванш отправлен...",
            )
            try:
                await bot.send_message(
                    opponent_id,
                    f"Игрок @{callback.from_user.username} предлагает реванш!",
                    reply_markup=duel_finish_keyboard(old_match_id, user_id),
                )
            except Exception:
                logger.exception("Не удалось отправить предложение о реванше")
            return

    # Если дошли сюда, значит реванш принят
    new_match_id = await db.create_duel_atomic(
        p1_id, p2_id, stake, idem_key=f"rematch-{old_match_id}-{p1_id}-{p2_id}"
    )
    if not new_match_id:
        await callback.answer(
            "Не удалось начать реванш: недостаточно средств.", show_alert=True
        )
        await bot.send_message(
            p1_id, "Реванш не начался: у одного из игроков недостаточно средств."
        )
        return

    await edit_caption_safe(
        bot, p1_id, opponent_msg_id, "Соперник принял реванш! Начинаем новый бой..."
    )
    await edit_caption_safe(
        bot,
        p2_id,
        callback.message.message_id,
        "Вы приняли реванш! Начинаем новый бой...",
    )
    await start_match(
        bot,
        new_match_id,
        p1_id,
        p2_id,
        stake,
        opponent_msg_id,
        callback.message.message_id,
    )
