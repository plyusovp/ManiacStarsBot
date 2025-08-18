# handlers/game_handlers.py
import random
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

import database.db as db
from keyboards.inline import (
    achievements_menu_keyboard, entertainment_menu_keyboard, 
    coinflip_bet_keyboard, coinflip_choice_keyboard, coinflip_continue_keyboard
)
from config import PHOTO_ACHIEVEMENTS, PHOTO_MAIN_MENU
from handlers.menu_handler import show_main_menu
from .utils import clean_junk_message # 🔥 Импортируем из нового файла

router = Router()

# --- FSM для Игры "Орёл и Решка" ---
class CoinflipGame(StatesGroup):
    in_game = State()

# --- Конфигурация уровней игры ---
COINFLIP_LEVELS = {
    1: {"chance": 50, "prize_mult": 2},
    2: {"chance": 43, "prize_mult": 1.7},
    3: {"chance": 35, "prize_mult": 1.5},
    4: {"chance": 25, "prize_mult": 1.8},
    5: {"chance": 15, "prize_mult": 2},
    6: {"chance": 5,  "prize_mult": 3},
}

def format_time(seconds: int) -> str:
    """Форматирует секунды в строку 'Чч Мм Сс'."""
    if seconds < 0:
        return "0с"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}ч {minutes}м"
    elif minutes > 0:
        return f"{minutes}м {secs}с"
    else:
        return f"{secs}с"

# --- ЕЖЕДНЕВНЫЙ БОНУС ---
@router.message(Command("bonus"))
async def bonus_handler(message: Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    result = await db.get_daily_bonus(user_id)
    
    response_text = ""
    if result['status'] == 'success':
        response_text = f"🎉 Поздравляю! Вы получили ежедневный бонус в размере <b>{result['reward']} ⭐</b>!"
        await db.grant_achievement(user_id, 'bonus_hunter', bot)
    elif result['status'] == 'wait':
        time_left = format_time(result['seconds_left'])
        response_text = f"Вы уже получали бонус сегодня. Попробуйте снова через <b>{time_left}</b>."
    else:
        response_text = "Произошла ошибка. Попробуйте позже."
    
    reply = await message.answer(response_text)
    await state.update_data(junk_message_id=reply.message_id)

# --- РАЗДЕЛ "РАЗВЛЕЧЕНИЯ" ---
@router.callback_query(F.data == "entertainment_menu")
async def entertainment_menu_handler(callback: CallbackQuery, state: FSMContext):
    await clean_junk_message(callback, state)
    text = "👾 <b>Развлечения</b> 👾\n\nЗдесь собраны все наши игры и другие активности. Выбирай, во что хочешь сыграть!"
    await callback.message.edit_media(
        media=InputMediaPhoto(media=PHOTO_MAIN_MENU, caption=text), 
        reply_markup=entertainment_menu_keyboard()
    )

# --- ИГРА "ОРЁЛ И РЕШКА" ---
@router.callback_query(F.data == "game_coinflip")
async def start_coinflip_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await clean_junk_message(callback, state)
    balance = await db.get_user_balance(callback.from_user.id)
    text = f"🪙 <b>Орёл и Решка: Рискни и Удвой!</b> 🦅\n\nДелай ставку, угадывай сторону и решай: забрать выигрыш или рискнуть ради большего приза?\n\nВаш баланс: {balance} ⭐\n<b>Выберите начальную ставку:</b>"
    
    await callback.message.edit_caption(caption=text, reply_markup=coinflip_bet_keyboard())

@router.callback_query(F.data.startswith("coinflip_bet:"))
async def bet_coinflip_handler(callback: CallbackQuery, state: FSMContext):
    await clean_junk_message(callback, state)
    bet = int(callback.data.split(":")[1])
    balance = await db.get_user_balance(callback.from_user.id)

    if balance < bet:
        await callback.answer("Недостаточно звёзд для такой ставки!", show_alert=True)
        return

    await state.set_state(CoinflipGame.in_game)
    await state.update_data(
        initial_bet=bet,
        current_pot=bet,
        level=1
    )
    
    text = f"Вы поставили <b>{bet} ⭐</b>.\n\nКуда упадёт монета?"
    await callback.message.edit_caption(caption=text, reply_markup=coinflip_choice_keyboard())

@router.callback_query(CoinflipGame.in_game, F.data.startswith("coinflip_play:"))
async def play_coinflip_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_choice = callback.data.split(":")[1]
    
    game_data = await state.get_data()
    level = game_data.get('level', 1)
    current_pot = game_data.get('current_pot')
    initial_bet = game_data.get('initial_bet')
    
    level_config = COINFLIP_LEVELS.get(level)
    if not level_config:
        await callback.answer("Вы достигли максимального уровня! Забирайте выигрыш.", show_alert=True)
        await cashout_coinflip_handler(callback, state)
        return

    win_chance = level_config['chance']
    prize_mult = level_config['prize_mult']
    
    is_win = random.randint(1, 100) <= win_chance
    result = user_choice if is_win else ('tails' if user_choice == 'heads' else 'heads')
    result_emoji = '🦅' if result == 'heads' else '🪙'
    
    if is_win:
        new_pot = int(current_pot * prize_mult)
        await state.update_data(current_pot=new_pot, level=level + 1)
        
        next_level_chance = COINFLIP_LEVELS.get(level + 1, {}).get('chance', 0)
        
        text = f"Выпал {result_emoji}! **Вы угадали!**\n\nВаш выигрыш составляет уже <b>{new_pot} ⭐</b>.\n\nХотите рискнуть ещё раз? Шанс на победу в следующем раунде: <b>{next_level_chance}%</b>"
        await callback.message.edit_caption(caption=text, reply_markup=coinflip_continue_keyboard(new_pot))
    else:
        await db.update_user_balance(callback.from_user.id, -initial_bet)
        text = f"Выпал {result_emoji}! **Вы проиграли...**\n\nВаша ставка в <b>{initial_bet} ⭐</b> сгорела."
        await state.clear()
        await callback.message.edit_caption(caption=text, reply_markup=coinflip_bet_keyboard())
        await callback.answer("Не повезло!", show_alert=True)

@router.callback_query(CoinflipGame.in_game, F.data == "coinflip_continue")
async def continue_coinflip_handler(callback: CallbackQuery, state: FSMContext):
    game_data = await state.get_data()
    level = game_data.get('level', 1)
    await callback.message.edit_caption(caption=f"Риск — благородное дело! Шанс угадать: {COINFLIP_LEVELS[level]['chance']}%\nКуда упадёт монета?", reply_markup=coinflip_choice_keyboard())

@router.callback_query(CoinflipGame.in_game, F.data == "coinflip_cashout")
async def cashout_coinflip_handler(callback: CallbackQuery, state: FSMContext):
    game_data = await state.get_data()
    prize = game_data.get('current_pot', 0)
    initial_bet = game_data.get('initial_bet', 0)
    
    profit = prize - initial_bet
    await db.update_user_balance(callback.from_user.id, profit)
    
    await callback.answer(f"Отличный выбор! Вы забираете {prize} ⭐.", show_alert=True)
    await state.clear()
    await start_coinflip_handler(callback, state)

@router.callback_query(F.data == "game_coinflip_cancel")
async def cancel_coinflip_handler(callback: CallbackQuery, state: FSMContext):
    if await state.get_state() == CoinflipGame.in_game:
        game_data = await state.get_data()
        initial_bet = game_data.get('initial_bet', 0)
        await db.update_user_balance(callback.from_user.id, -initial_bet)
        await callback.answer(f"Вы отменили игру и потеряли начальную ставку в {initial_bet} ⭐.", show_alert=True)
    
    await state.clear()
    await start_coinflip_handler(callback, state)


# --- СИСТЕМА ДОСТИЖЕНИЙ ---
@router.callback_query(F.data == "achievements_menu")
async def achievements_menu_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await clean_junk_message(callback, state)
    user_id = callback.from_user.id
    all_ach = await db.get_all_achievements()
    user_ach = await db.get_user_achievements(user_id)
    text = "Выполняй <b>Достижения</b> и получай жирные награды! 🏆"
    await callback.message.edit_media(
        media=InputMediaPhoto(media=PHOTO_ACHIEVEMENTS, caption=text),
        reply_markup=achievements_menu_keyboard(all_ach, user_ach, page=1)
    )

@router.callback_query(F.data.startswith("achievements_page:"))
async def achievements_page_handler(callback: CallbackQuery, state: FSMContext):
    await clean_junk_message(callback, state)
    page = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    all_ach = await db.get_all_achievements()
    user_ach = await db.get_user_achievements(user_id)
    await callback.message.edit_reply_markup(
        reply_markup=achievements_menu_keyboard(all_ach, user_ach, page=page)
    )

# --- ЗАГЛУШКИ ДЛЯ БУДУЩИХ ИГР ---
@router.callback_query(F.data == "game_casino")
async def game_stubs_handler(callback: CallbackQuery, state: FSMContext):
    await clean_junk_message(callback, state)
    await callback.answer("Скоро... 🤫", show_alert=True)


@router.callback_query(F.data == "ignore_click")
async def ignore_click_handler(callback: CallbackQuery):
    """Обрабатывает нажатия на неинтерактивные кнопки достижений."""
    await callback.answer("Это достижение. Выполняй цели, чтобы его открыть!")