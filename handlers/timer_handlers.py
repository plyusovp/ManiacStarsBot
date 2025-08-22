# handlers/timer_handlers.py
import asyncio
import random
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import database.db as db
from keyboards.inline import (
    timer_stake_keyboard, timer_game_keyboard, 
    entertainment_menu_keyboard, timer_finish_keyboard,
    timer_stuck_keyboard, timer_rematch_offer_keyboard
)
from config import PHOTO_MAIN_MENU
from .utils import clean_junk_message
from .duel_handlers import edit_caption_safe, parse_cb_data

router = Router()
logger = logging.getLogger(__name__)

# --- Константы и Хранилища ---
TIMER_QUEUE_TIMEOUT_SEC = 45
TIMER_COUNTDOWN_SEC = 5

timer_queue: dict[int, dict] = {}
active_timers: dict[int, "TimerMatch"] = {}
rematch_timer_offers: dict[int, dict] = {}

@dataclass
class TimerMatch:
    """Класс для хранения состояния игры 'Звёздный таймер'."""
    match_id: int
    p1_id: int
    p2_id: int
    stake: int
    bank: int
    stop_second: int
    p1_message_id: Optional[int] = None
    p2_message_id: Optional[int] = None
    start_time: Optional[float] = None
    p1_clicked_at: Optional[float] = None
    p2_clicked_at: Optional[float] = None
    timer_task: Optional[asyncio.Task] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

# --- Сервисы (Логика игры) ---
async def resolve_timer_match(bot: Bot, match: TimerMatch):
    """Завершает игру, определяет победителя и распределяет банк."""
    # Эта функция вызывается уже под замком, повторный не нужен
    if match.match_id not in active_timers: return

    p1_time = match.p1_clicked_at
    p2_time = match.p2_clicked_at
    stop_time = match.start_time + (10 - match.stop_second)
    
    p1_diff = stop_time - p1_time if p1_time and p1_time <= stop_time else float('inf')
    p2_diff = stop_time - p2_time if p2_time and p2_time <= stop_time else float('inf')

    winner_id, loser_id = None, None
    if p1_diff < p2_diff:
        winner_id, loser_id = match.p1_id, match.p2_id
    elif p2_diff < p1_diff:
        winner_id, loser_id = match.p2_id, match.p1_id

    bank = match.bank
    commission = int(bank * 0.07)
    
    try:
        p1_user = await bot.get_chat(match.p1_id)
        p2_user = await bot.get_chat(match.p2_id)
        p1_username = f"@{p1_user.username}" if p1_user.username else p1_user.full_name
        p2_username = f"@{p2_user.username}" if p2_user.username else p2_user.full_name
    except Exception:
        p1_username, p2_username = "Игрок 1", "Игрок 2"

    p1_time_str = f"{10 - (p1_time - match.start_time):.2f}" if p1_time else "не нажал"
    p2_time_str = f"{10 - (p2_time - match.start_time):.2f}" if p2_time else "не нажал"
    
    result_text = f"⌛ Таймер остановлен на <b>{match.stop_second}</b> секунде!\n\n{p1_username} нажал(а) на {p1_time_str}\n{p2_username} нажал(а) на {p2_time_str}\n\n"

    p1_opponent_id = match.p2_id
    p2_opponent_id = match.p1_id

    if winner_id and loser_id:
        prize = bank - commission
        winner_username = p1_username if winner_id == match.p1_id else p2_username
        result_text += f"🏆 Победитель: {winner_username}!\nОн(а) забирает банк в <b>{prize} ⭐</b>."
        await db.update_user_balance(winner_id, prize + match.stake) # Возврат ставки + приз
        await db.finish_timer_match(match.match_id, winner_id=winner_id)
    else: # Ничья
        rematch_pot = bank - commission
        result_text += f"🤝 Ничья! Банк в размере {rematch_pot}⭐ становится джекпотом для реванша!"
        await db.update_user_balance(match.p1_id, match.stake)
        await db.update_user_balance(match.p2_id, match.stake)
        await db.finish_timer_match(match.match_id, is_draw=True, new_bank=rematch_pot)

    await asyncio.gather(
        edit_caption_safe(bot, match.p1_id, match.p1_message_id, result_text, timer_finish_keyboard(match.match_id, p1_opponent_id)),
        edit_caption_safe(bot, match.p2_id, match.p2_message_id, result_text, timer_finish_keyboard(match.match_id, p2_opponent_id))
    )
    
    if match.match_id in active_timers:
        del active_timers[match.match_id]


async def timer_task(bot: Bot, match: TimerMatch):
    """Асинхронная задача-таймер для игры."""
    match.start_time = time.time()
    
    for i in range(10, -1, -1):
        text = f"⏳ <b>{i}</b>..."
        try:
            await asyncio.gather(
                edit_caption_safe(bot, match.p1_id, match.p1_message_id, text, timer_game_keyboard(match.match_id)),
                edit_caption_safe(bot, match.p2_id, match.p2_message_id, text, timer_game_keyboard(match.match_id))
            )
        except TelegramBadRequest:
            if match.match_id in active_timers: del active_timers[match.match_id]
            return
            
        await asyncio.sleep(1)
        
    await resolve_timer_match(bot, match)


async def start_timer_match(bot: Bot, p1_id: int, p2_id: int, stake: int, bank: int, p1_msg_id: int, p2_msg_id: int):
    """Запускает игру 'Звёздный таймер'."""
    match_id, stop_second = await db.create_timer_match(p1_id, p2_id, stake, bank)
    if not match_id:
        logger.error("Не удалось создать матч в БД для таймера.")
        # Тут нужно вернуть ставки, если они были списаны до этого
        return

    match = TimerMatch(match_id, p1_id, p2_id, stake, bank, stop_second)
    match.p1_msg_id = p1_msg_id
    match.p2_msg_id = p2_msg_id
    active_timers[match_id] = match
    
    match.timer_task = asyncio.create_task(timer_task(bot, match))


@router.callback_query(F.data == "game_timer")
async def timer_menu_handler(callback: CallbackQuery, state: FSMContext):
    """Отображает главное меню 'Звёздного таймера'."""
    await clean_junk_message(callback, state)
    user_id = callback.from_user.id
    
    if await db.get_active_timer_id(user_id):
        text = "Вы уже находитесь в активной игре. Вы можете покинуть её (ставка будет потеряна)."
        return await edit_caption_safe(callback.bot, callback.message.chat.id, callback.message.message_id, text, timer_stuck_keyboard())

    balance = await db.get_user_balance(user_id)
    text = (
        f"⏳ <b>Звёздный таймер</b> ⏳\n\n"
        f"Испытай свою реакцию! Нажми кнопку как можно ближе к моменту остановки таймера, но не позже.\n\n"
        f"<b>Ваш баланс:</b> {balance} ⭐\n"
        f"<b>Выберите ставку:</b>"
    )
    await edit_caption_safe(callback.bot, callback.message.chat.id, callback.message.message_id, text, timer_stake_keyboard())


@router.callback_query(F.data.startswith("timer_stake:"))
async def find_timer_handler(callback: CallbackQuery, bot: Bot):
    """Обрабатывает выбор ставки и ищет соперника."""
    parts = parse_cb_data(callback.data, "timer_stake:", 2)
    if not parts: return await callback.answer("Ошибка данных.")
    stake = int(parts[1])
    user_id = callback.from_user.id
    
    if not await db.update_user_balance(user_id, -stake):
        return await callback.answer("У вас недостаточно звёзд для этой ставки!", show_alert=True)
    
    opponent_data = timer_queue.get(stake)
    if opponent_data and opponent_data['user_id'] != user_id:
        del timer_queue[stake]
        opponent_id, opponent_msg_id = opponent_data['user_id'], opponent_data['msg_id']
        
        await edit_caption_safe(bot, callback.message.chat.id, callback.message.message_id, "✅ Соперник найден! Запуск...")
        await edit_caption_safe(bot, opponent_id, opponent_msg_id, "✅ Соперник найден! Запуск...")
        await asyncio.sleep(1)
        await start_timer_match(bot, opponent_id, user_id, stake, stake * 2, opponent_msg_id, callback.message.message_id)
    else:
        timer_queue[stake] = {'user_id': user_id, 'msg_id': callback.message.message_id}
        await edit_caption_safe(bot, callback.message.chat.id, callback.message.message_id, f"🔎 Ищем соперника для игры на {stake} ⭐...")

@router.callback_query(F.data.startswith("timer_play:"))
async def play_timer_handler(callback: CallbackQuery):
    """Обрабатывает нажатие на кнопку 'Забрать банк'."""
    parts = parse_cb_data(callback.data, "timer_play:", 2)
    if not parts: return await callback.answer("Ошибка данных.")
    match_id = int(parts[1])
    
    user_id = callback.from_user.id
    match = active_timers.get(match_id)

    if not match:
        return await callback.answer("Игра уже закончилась.", show_alert=True)
    
    async with match.lock:
        player_clicked_attr = 'p1_clicked_at' if user_id == match.p1_id else 'p2_clicked_at'
        
        if getattr(match, player_clicked_attr) is not None:
            return await callback.answer("Вы уже сделали свой ход в этой игре.", show_alert=True)
            
        setattr(match, player_clicked_attr, time.time())
        await db.update_timer_player_click(match_id, user_id, time.time())
        
        opponent_clicked_attr = 'p2_clicked_at' if user_id == match.p1_id else 'p1_clicked_at'
        
        if getattr(match, opponent_clicked_attr) is not None:
            if match.timer_task and not match.timer_task.done():
                match.timer_task.cancel()
            await resolve_timer_match(callback.bot, match)
        else:
            await callback.answer("Ваш ход принят! Ожидаем соперника...")

@router.callback_query(F.data == "timer_leave_active")
async def timer_leave_active_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id
    match_id = await db.get_active_timer_id(user_id)
    
    if not match_id:
        await callback.answer("Не найдено активных игр.", show_alert=True)
        return await timer_menu_handler(callback, state)

    await db.interrupt_timer_match(match_id)
    
    details = await db.get_timer_match_details(match_id)
    if details:
        stake, _, p1_id, p2_id = details
        opponent_id = p2_id if user_id == p1_id else p1_id
        await db.update_user_balance(opponent_id, stake)
        await callback.answer("Вы покинули игру. Ваша ставка была потеряна.", show_alert=True)
    else:
        await callback.answer("Вы покинули зависшую игру.", show_alert=True)
        
    await timer_menu_handler(callback, state)

@router.callback_query(F.data.startswith("timer_rematch:"))
async def timer_rematch_handler(callback: CallbackQuery, bot: Bot):
    parts = parse_cb_data(callback.data, "timer_rematch:", 3)
    if not parts: return await callback.answer("Ошибка данных.")
    _, match_id, opponent_id = map(int, parts)
    
    user_id = callback.from_user.id

    details = await db.get_timer_match_details(match_id)
    if not details:
        return await callback.answer("Не удалось найти детали прошлой игры.", show_alert=True)
        
    stake, old_bank, p1_id, p2_id = details
    
    if match_id in rematch_timer_offers:
        if rematch_timer_offers[match_id]['user_id'] == user_id:
            return await callback.answer("Ожидаем ответа соперника...", show_alert=True)
        
        offer = rematch_timer_offers.pop(match_id)
        
        if not await db.update_user_balance(user_id, -stake):
            await db.update_user_balance(offer['user_id'], stake) # Возвращаем ставку тому, кто ждал
            return await callback.answer("Недостаточно средств для реванша.", show_alert=True)

        await edit_caption_safe(bot, offer['user_id'], offer['msg_id'], f"Соперник принял реванш! Играем на джекпот {old_bank} ⭐. Запуск...")
        await edit_caption_safe(bot, user_id, callback.message.message_id, f"Вы приняли реванш! Играем на джекпот {old_bank} ⭐. Запуск...")
        await asyncio.sleep(1)
        await start_timer_match(bot, offer['user_id'], user_id, stake, old_bank, offer['msg_id'], callback.message.message_id)
    else:
        if not await db.update_user_balance(user_id, -stake):
             return await callback.answer("Недостаточно средств для предложения реванша.", show_alert=True)
        
        rematch_timer_offers[match_id] = {'user_id': user_id, 'msg_id': callback.message.message_id}
        await edit_caption_safe(bot, user_id, callback.message.message_id, "✅ Запрос на реванш отправлен. Ожидаем ответа соперника...")
        
        rematch_keyboard = timer_rematch_offer_keyboard(match_id=match_id, opponent_id=user_id, bank=old_bank)
        try:
            await bot.send_message(
                opponent_id, 
                f"Игрок @{callback.from_user.username or user_id} предлагает реванш, чтобы разыграть банк в {old_bank} ⭐!",
                reply_markup=rematch_keyboard
            )
        except Exception as e:
            logger.exception(f"Не удалось отправить предложение о реванше: {e}")

@router.callback_query(F.data.startswith("timer_rematch_accept:"))
async def timer_rematch_accept_handler(callback: CallbackQuery, bot: Bot):
    parts = parse_cb_data(callback.data, "timer_rematch_accept:", 3)
    if not parts: return await callback.answer("Ошибка данных.")
    _, match_id, opponent_id = map(int, parts)
    
    user_id = callback.from_user.id
    details = await db.get_timer_match_details(match_id)
    if not details: return await callback.answer("Не удалось найти детали прошлой игры.", show_alert=True)
    stake, old_bank, _, _ = details

    if not await db.update_user_balance(user_id, -stake):
        await db.update_user_balance(opponent_id, stake) # Возвращаем ставку тому, кто предложил
        await callback.answer("У вас недостаточно средств для реванша.", show_alert=True)
        return

    await edit_caption_safe(bot, callback.message.chat.id, callback.message.message_id, f"Вы приняли реванш! Играем на джекпот {old_bank} ⭐. Запуск...")
    
    msg1 = await bot.send_photo(user_id, PHOTO_MAIN_MENU, caption="Реванш! Запуск...")
    msg2 = await bot.send_photo(opponent_id, PHOTO_MAIN_MENU, caption="Соперник принял реванш! Запуск...")
    
    await start_timer_match(bot, user_id, opponent_id, stake, old_bank, msg1.message_id, msg2.message_id)

@router.callback_query(F.data.startswith("timer_rematch_decline:"))
async def timer_rematch_decline_handler(callback: CallbackQuery, bot: Bot):
    parts = parse_cb_data(callback.data, "timer_rematch_decline:", 2)
    if not parts: return await callback.answer("Ошибка данных.")
    match_id = int(parts[1])
    
    if match_id in rematch_timer_offers:
        offer = rematch_timer_offers.pop(match_id)
        opponent_id = offer['user_id']
        await db.update_user_balance(opponent_id, offer.get('stake', 0)) # Возвращаем ставку
        try:
            await bot.send_message(opponent_id, "Соперник отклонил предложение о реванше.")
        except Exception as e:
            logger.exception(f"Не удалось уведомить об отклонении реванша: {e}")

    await edit_caption_safe(bot, callback.message.chat.id, callback.message.message_id, "Вы отклонили реванш.")
    await asyncio.sleep(2)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
