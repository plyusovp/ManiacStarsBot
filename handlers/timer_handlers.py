# handlers/timer_handlers.py
import asyncio
import random
import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import database.db as db
from keyboards.inline import (
    timer_stake_keyboard, timer_game_keyboard, 
    entertainment_menu_keyboard, timer_finish_keyboard,
    timer_stuck_keyboard
)
from config import PHOTO_MAIN_MENU
from .utils import clean_junk_message

router = Router()

timer_queue = {}
active_timers = {}
rematch_timer_offers = {}

class TimerMatch:
    """Класс для хранения состояния игры 'Звёздный таймер'."""
    def __init__(self, match_id, p1_id, p2_id, stake, bank, stop_second):
        self.match_id = match_id
        self.p1_id = p1_id
        self.p2_id = p2_id
        self.stake = stake
        self.bank = bank
        self.p1_msg_id = None
        self.p2_msg_id = None
        self.stop_second = stop_second
        self.start_time = None
        self.p1_clicked_at = None
        self.p2_clicked_at = None
        self.timer_task: asyncio.Task = None
        self.lock = asyncio.Lock()

async def resolve_timer_match(bot: Bot, match_id: int):
    """Завершает игру, определяет победителя и распределяет банк."""
    match = active_timers.get(match_id)
    if not match: return

    async with match.lock:
        if match_id not in active_timers: return

        p1_time = match.p1_clicked_at
        p2_time = match.p2_clicked_at
        stop_time = match.start_time + (10 - match.stop_second)
        
        p1_diff = stop_time - p1_time if p1_time and p1_time <= stop_time else float('inf')
        p2_diff = stop_time - p2_time if p2_time and p2_time <= stop_time else float('inf')

        winner_id, loser_id = None, None
        is_draw = False

        if p1_diff < p2_diff:
            winner_id, loser_id = match.p1_id, match.p2_id
        elif p2_diff < p1_diff:
            winner_id, loser_id = match.p2_id, match.p1_id
        else:
            is_draw = True

        bank = match.bank
        commission = int(bank * 0.07)
        
        try:
            p1_user = await bot.get_chat(match.p1_id)
            p2_user = await bot.get_chat(match.p2_id)
            p1_username = f"@{p1_user.username}" if p1_user.username else p1_user.full_name
            p2_username = f"@{p2_user.username}" if p2_user.username else p2_user.full_name
        except Exception:
            p1_username, p2_username = "Игрок 1", "Игрок 2"

        result_text = f"⌛ Таймер остановлен на <b>{match.stop_second}</b> секунде!\n\n"
        result_text += f"{p1_username} нажал на {10 - (p1_time - match.start_time):.2f}\n" if p1_time else f"{p1_username} не нажал\n"
        result_text += f"{p2_username} нажал на {10 - (p2_time - match.start_time):.2f}\n" if p2_time else f"{p2_username} не нажал\n\n"

        if winner_id:
            prize = bank - commission
            winner_username = p1_username if winner_id == match.p1_id else p2_username
            result_text += f"🏆 Победитель: {winner_username}!\nОн забирает банк в <b>{prize} ⭐</b>."
            await db.update_user_balance(winner_id, prize)
            await db.finish_timer_match(match_id, winner_id=winner_id)
        else:
            rematch_pot = bank - commission
            result_text += f"🤝 Ничья! Банк в размере {rematch_pot}⭐ становится джекпотом для реванша!"
            await db.finish_timer_match(match_id, is_draw=True, new_bank=rematch_pot)

        await asyncio.gather(
            bot.edit_message_caption(chat_id=match.p1_id, message_id=match.p1_msg_id, caption=result_text, reply_markup=timer_finish_keyboard(match_id)),
            bot.edit_message_caption(chat_id=match.p2_id, message_id=match.p2_msg_id, caption=result_text, reply_markup=timer_finish_keyboard(match_id))
        )
        
        if match_id in active_timers:
            del active_timers[match_id]

async def timer_task(bot: Bot, match_id: int):
    """Асинхронная задача-таймер для игры."""
    match = active_timers.get(match_id)
    if not match: return
    
    match.start_time = time.time()
    
    for i in range(10, -1, -1):
        text = f"⏳ <b>{i}</b>..."
        try:
            await asyncio.gather(
                bot.edit_message_caption(chat_id=match.p1_id, message_id=match.p1_msg_id, caption=text, reply_markup=timer_game_keyboard(match_id)),
                bot.edit_message_caption(chat_id=match.p2_id, message_id=match.p2_msg_id, caption=text, reply_markup=timer_game_keyboard(match_id))
            )
        except TelegramBadRequest:
            if match_id in active_timers: del active_timers[match_id]
            return
        await asyncio.sleep(1)
        
    await resolve_timer_match(bot, match_id)

async def start_timer_match(bot: Bot, p1_id: int, p2_id: int, stake: int, bank: int, p1_msg_id: int, p2_msg_id: int):
    """Запускает игру 'Звёздный таймер'."""
    match_id, stop_second = await db.create_timer_match(p1_id, p2_id, stake, bank)
    match = TimerMatch(match_id, p1_id, p2_id, stake, bank, stop_second)
    match.p1_msg_id = p1_msg_id
    match.p2_msg_id = p2_msg_id
    active_timers[match_id] = match
    
    match.timer_task = asyncio.create_task(timer_task(bot, match_id))

@router.callback_query(F.data == "game_timer")
async def timer_menu_handler(callback: CallbackQuery, state: FSMContext):
    """Отображает главное меню 'Звёздного таймера'."""
    await clean_junk_message(callback, state)
    user_id = callback.from_user.id
    
    if await db.get_active_timer_id(user_id):
        text = "Вы уже находитесь в активной игре. Вы можете покинуть её (ставка будет потеряна)."
        return await callback.message.edit_media(
            media=InputMediaPhoto(media=PHOTO_MAIN_MENU, caption=text),
            reply_markup=timer_stuck_keyboard()
        )
    
    balance = await db.get_user_balance(user_id)
    text = (
        f"⏳ <b>Звёздный таймер</b> ⏳\n\n"
        f"Испытай свою реакцию! Нажми кнопку как можно ближе к моменту остановки таймера, но не позже.\n\n"
        f"<b>Ваш баланс:</b> {balance} ⭐\n"
        f"<b>Выберите ставку:</b>"
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(media=PHOTO_MAIN_MENU, caption=text),
        reply_markup=timer_stake_keyboard()
    )

@router.callback_query(F.data.startswith("timer_stake:"))
async def find_timer_handler(callback: CallbackQuery, bot: Bot):
    """Обрабатывает выбор ставки и ищет соперника."""
    stake = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    balance = await db.get_user_balance(user_id)
    if balance < stake:
        return await callback.answer("У вас недостаточно звёзд для этой ставки!", show_alert=True)
        
    await db.update_user_balance(user_id, -stake)
    
    opponent_data = timer_queue.get(stake)
    if opponent_data and opponent_data['user_id'] != user_id:
        del timer_queue[stake]
        opponent_id = opponent_data['user_id']
        opponent_msg_id = opponent_data['msg_id']
        
        await callback.message.edit_caption(caption="✅ Соперник найден! Запускаю таймер...")
        await bot.edit_message_caption(chat_id=opponent_id, message_id=opponent_msg_id, caption="✅ Соперник найден! Запускаю таймер...")
        await asyncio.sleep(1)
        await start_timer_match(bot, opponent_id, user_id, stake, stake * 2, opponent_msg_id, callback.message.message_id)
    else:
        timer_queue[stake] = {'user_id': user_id, 'msg_id': callback.message.message_id}
        await callback.message.edit_caption(caption=f"🔎 Ищем соперника для игры на {stake} ⭐...")

@router.callback_query(F.data.startswith("timer_play:"))
async def play_timer_handler(callback: CallbackQuery):
    """Обрабатывает нажатие на кнопку 'Забрать банк'."""
    match_id = int(callback.data.split(":")[1])
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
            await resolve_timer_match(callback.bot, match_id)
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
    await callback.answer("Вы покинули зависшую игру. Ваша ставка была возвращена.", show_alert=True)
    
    # Возвращаем ставку
    match_details = await db.get_timer_match_details(match_id)
    if match_details:
        stake, _ = match_details
        await db.update_user_balance(user_id, stake)

    await timer_menu_handler(callback, state)


@router.callback_query(F.data.startswith("timer_rematch:"))
async def timer_rematch_handler(callback: CallbackQuery, bot: Bot):
    match_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    details = await db.get_timer_match_details(match_id)
    if not details:
        return await callback.answer("Не удалось найти детали прошлой игры.", show_alert=True)
        
    stake, old_bank = details

    # Если уже есть предложение о реванше
    if match_id in rematch_timer_offers:
        opponent_id = rematch_timer_offers.pop(match_id)
        if opponent_id == user_id:
            rematch_timer_offers[match_id] = user_id
            return await callback.answer("Ожидаем ответа соперника...", show_alert=True)
        
        # Реванш!
        await callback.message.edit_caption(caption=f"Соперник принял реванш! Играем на джекпот {old_bank} ⭐. Запуск...")
        p1, p2 = await db.get_timer_players(match_id)
        # Находим message_id старых сообщений (этот момент может быть сложным, пока упростим)
        # Для простоты отправим новые сообщения
        msg1 = await bot.send_photo(p1, PHOTO_MAIN_MENU, caption="Реванш! Запуск...")
        msg2 = await bot.send_photo(p2, PHOTO_MAIN_MENU, caption="Реванш! Запуск...")
        
        await start_timer_match(bot, p1, p2, stake, old_bank, msg1.message_id, msg2.message_id)

    # Если предложения ещё нет
    else:
        rematch_timer_offers[match_id] = user_id
        await callback.message.edit_caption(caption="✅ Запрос на реванш отправлен. Ожидаем ответа соперника...")