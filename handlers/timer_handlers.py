# handlers/timer_handlers.py
import asyncio
import logging
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import settings
from database import db
from handlers.utils import clean_junk_message
from keyboards.inline import (
    timer_finish_keyboard,
    timer_game_keyboard,
    timer_searching_keyboard,
    timer_stake_keyboard,
)
from lexicon.texts import LEXICON

router = Router()
logger = logging.getLogger(__name__)

timer_queue = defaultdict(dict)
active_timers = {}


@dataclass
class TimerMatch:
    """Класс для хранения состояния игры в 'Таймер'."""

    match_id: int
    p1_id: int
    p2_id: int
    stake: int
    target_time: float  # Загаданное время
    start_time: float = 0.0  # Время начала раунда
    p1_stopped_time: float = 0.0
    p2_stopped_time: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


async def start_timer_game(bot: Bot, match_id: int, p1_id: int, p2_id: int, stake: int):
    """Запускает игру: обратный отсчет и основной раунд."""
    target_time = random.uniform(2.5, 7.0)  # Загадываем время от 2.5 до 7 секунд
    match = TimerMatch(match_id, p1_id, p2_id, stake, target_time)
    active_timers[match_id] = match

    try:
        p1 = await bot.get_chat(p1_id)
        p2 = await bot.get_chat(p2_id)
    except Exception as e:
        logger.error(f"Не удалось получить информацию об игроках в таймере: {e}")
        del active_timers[match_id]
        return

    p1_username = f"@{p1.username}" if p1.username else p1.full_name
    p2_username = f"@{p2.username}" if p2.username else p2.full_name

    text = LEXICON["timer_match_found"].format(
        p1_username=p1_username, p2_username=p2_username, stake=stake
    )

    # Отправляем начальные сообщения
    p1_msg, p2_msg = await asyncio.gather(
        bot.send_message(p1_id, text + "\n\nПриготовьтесь..."),
        bot.send_message(p2_id, text + "\n\nПриготовьтесь..."),
    )

    await asyncio.sleep(random.uniform(2.5, 4.0))  # Случайная задержка перед стартом

    # Редактируем сообщения, чтобы начать игру
    match.start_time = time.time()
    await asyncio.gather(
        bot.edit_message_text(
            "🔴 НАЖИМАЙТЕ СТОП!",
            chat_id=p1_id,
            message_id=p1_msg.message_id,
            reply_markup=timer_game_keyboard(match_id),
        ),
        bot.edit_message_text(
            "🔴 НАЖИМАЙТЕ СТОП!",
            chat_id=p2_id,
            message_id=p2_msg.message_id,
            reply_markup=timer_game_keyboard(match_id),
        ),
    )


async def resolve_timer_game(bot: Bot, match_id: int):
    """Определяет победителя и отправляет результаты."""
    match = active_timers.get(match_id)
    if not match:
        return

    async with match.lock:
        # Проверяем, что оба игрока сделали ход
        if not (match.p1_stopped_time > 0 and match.p2_stopped_time > 0):
            return

        p1_elapsed = match.p1_stopped_time - match.start_time
        p2_elapsed = match.p2_stopped_time - match.start_time

        p1_diff = abs(p1_elapsed - match.target_time)
        p2_diff = abs(p2_elapsed - match.target_time)

        winner_id, loser_id, is_draw = None, None, False
        if p1_diff < p2_diff:
            winner_id, loser_id = match.p1_id, match.p2_id
        elif p2_diff < p1_diff:
            winner_id, loser_id = match.p2_id, match.p1_id
        else:
            is_draw = True

    bank = match.stake * 2
    rake = int(bank * (settings.DUEL_RAKE_PERCENT / 100))
    prize = bank - rake

    p1_result_text = f"{p1_elapsed:.3f} сек. (отличие: {p1_diff:.3f})"
    p2_result_text = f"{p2_elapsed:.3f} сек. (отличие: {p2_diff:.3f})"
    target_text = f"Загаданное время было: {match.target_time:.3f} сек."

    if is_draw:
        await db.finish_timer_match(match_id, is_draw=True, new_bank=0)
        text = (
            LEXICON["timer_draw"].format(
                p1_result=p1_result_text, p2_result=p2_result_text
            )
            + f"\n\n{target_text}"
        )
        await asyncio.gather(
            bot.send_message(match.p1_id, text, reply_markup=timer_finish_keyboard()),
            bot.send_message(match.p2_id, text, reply_markup=timer_finish_keyboard()),
        )
    else:
        await db.finish_timer_match(match_id, winner_id=winner_id)
        winner_text = (
            LEXICON["timer_win_result"].format(
                p1_result=p1_result_text, p2_result=p2_result_text, prize=prize
            )
            + f"\n\n{target_text}"
        )
        loser_text = (
            LEXICON["timer_loss_result"].format(
                p1_result=p1_result_text, p2_result=p2_result_text
            )
            + f"\n\n{target_text}"
        )
        await bot.send_message(
            winner_id, winner_text, reply_markup=timer_finish_keyboard()
        )
        await bot.send_message(
            loser_id, loser_text, reply_markup=timer_finish_keyboard()
        )

    if match_id in active_timers:
        del active_timers[match_id]


@router.callback_query(F.data == "game_timer")
async def timer_menu_handler(callback: CallbackQuery, state: FSMContext):
    await clean_junk_message(callback, state)
    balance = await db.get_user_balance(callback.from_user.id)
    text = LEXICON["timer_menu"].format(balance=balance)
    await callback.message.edit_caption(
        caption=text, reply_markup=timer_stake_keyboard()
    )


@router.callback_query(F.data.startswith("timer_stake:"))
async def find_timer_handler(callback: CallbackQuery, bot: Bot):
    stake = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    balance = await db.get_user_balance(user_id)
    if balance < stake:
        return await callback.answer(
            f"Недостаточно средств для ставки в {stake} ⭐.", show_alert=True
        )

    if any(user_id in [m.p1_id, m.p2_id] for m in active_timers.values()):
        return await callback.answer("Вы уже находитесь в игре.", show_alert=True)

    if user_id in timer_queue.get(stake, {}):
        return await callback.answer("Вы уже ищете игру.", show_alert=True)

    # Ищем оппонента в очереди
    if timer_queue.get(stake):
        opponent_id = list(timer_queue[stake].keys())[0]
        del timer_queue[stake][opponent_id]

        match_id = await db.create_timer_match(user_id, opponent_id, stake)
        if not match_id:
            # Если создание матча не удалось (нехватка средств у кого-то)
            await callback.answer(
                "Не удалось создать игру: у одного из игроков недостаточно средств.",
                show_alert=True,
            )
            # Нужно уведомить и второго игрока
            try:
                await bot.send_message(
                    opponent_id,
                    "Поиск отменен: у вашего оппонента недостаточно средств.",
                )
            except Exception:
                pass
            return

        # Запускаем игру для обоих
        await start_timer_game(bot, match_id, user_id, opponent_id, stake)
        # Убираем сообщения о поиске
        try:
            await asyncio.gather(
                bot.delete_message(
                    chat_id=user_id, message_id=callback.message.message_id
                ),
                bot.delete_message(
                    chat_id=opponent_id, message_id=timer_queue[stake].get("msg_id")
                ),
            )
        except (TelegramBadRequest, KeyError):
            pass

    else:
        # Добавляем в очередь
        timer_queue[stake][user_id] = {"msg_id": callback.message.message_id}
        await callback.message.edit_caption(
            caption=f"🔎 Ищем соперника со ставкой {stake} ⭐...",
            reply_markup=timer_searching_keyboard(),
        )


@router.callback_query(F.data == "timer_cancel_search")
async def timer_cancel_search_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    for stake in timer_queue:
        if user_id in timer_queue[stake]:
            del timer_queue[stake][user_id]
            break
    await callback.answer("Поиск отменён.", show_alert=True)
    await timer_menu_handler(callback, state)


@router.callback_query(F.data.startswith("timer_stop:"))
async def stop_timer_handler(callback: CallbackQuery, bot: Bot):
    match_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    match = active_timers.get(match_id)
    if not match:
        return await callback.answer(
            "Игра не найдена или уже завершена.", show_alert=True
        )

    async with match.lock:
        player_role = "p1" if user_id == match.p1_id else "p2"

        if player_role == "p1" and match.p1_stopped_time > 0:
            return await callback.answer("Вы уже сделали свой ход.")
        if player_role == "p2" and match.p2_stopped_time > 0:
            return await callback.answer("Вы уже сделали свой ход.")

        stopped_time = time.time()
        if player_role == "p1":
            match.p1_stopped_time = stopped_time
        else:
            match.p2_stopped_time = stopped_time

    await callback.message.edit_text("✅ Ваше время принято! Ожидаем соперника...")
    await resolve_timer_game(bot, match_id)
