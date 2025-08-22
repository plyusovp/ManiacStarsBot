# handlers/game_handlers.py
import random

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from config import PHOTO_ACHIEVEMENTS, PHOTO_MAIN_MENU
from database import db
from handlers.utils import clean_junk_message
from keyboards.inline import (achievements_menu_keyboard,
                              coinflip_bet_keyboard, coinflip_choice_keyboard,
                              coinflip_continue_keyboard,
                              entertainment_menu_keyboard)

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
    6: {"chance": 5, "prize_mult": 3},
}


# --- Вспомогательные функции ---
async def safe_edit_media(message: Message, media: InputMediaPhoto, reply_markup):
    """Безопасно редактирует сообщение с медиа, игнорируя ошибку 'not modified'."""
    try:
        await message.edit_media(media=media, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            print(f"Unhandled TelegramBadRequest in safe_edit_media: {e}")
    except Exception as e:
        print(f"Unexpected error in safe_edit_media: {e}")


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


# --- Основные обработчики ---
@router.message(Command("bonus"))
async def bonus_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id
    try:
        result = await db.get_daily_bonus(user_id)

        response_text = ""
        if result["status"] == "success":
            response_text = f"🎉 Поздравляю! Вы получили ежедневный бонус в размере <b>{result['reward']} ⭐</b>!"
            await db.grant_achievement(user_id, "bonus_hunter", bot)
        elif result["status"] == "wait":
            time_left = format_time(result["seconds_left"])
            response_text = f"Вы уже получали бонус сегодня. Попробуйте снова через <b>{time_left}</b>."
        else:
            response_text = "Произошла ошибка. Попробуйте позже."

        reply = await message.answer(response_text)
        await state.update_data(junk_message_id=reply.message_id)
    except Exception as e:
        print(f"Error in bonus_handler: {e}")
        await message.answer("Что-то пошло не так при получении бонуса.")


@router.callback_query(F.data == "entertainment_menu")
async def entertainment_menu_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await clean_junk_message(callback, state)
    text = "👾 <b>Развлечения</b> 👾\n\nЗдесь собраны все наши игры и другие активности. Выбирай, во что хочешь сыграть!"
    await safe_edit_media(
        callback.message,
        media=InputMediaPhoto(media=PHOTO_MAIN_MENU, caption=text, parse_mode="HTML"),
        reply_markup=entertainment_menu_keyboard(),
    )


# --- ИГРА "ОРЁЛ И РЕШКА" ---
@router.callback_query(F.data == "game_coinflip")
async def start_coinflip_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await clean_junk_message(callback, state)
    balance = await db.get_user_balance(callback.from_user.id)
    text = f"🪙 <b>Орёл и Решка: Рискни и Удвой!</b> 🦅\n\nДелай ставку, угадывай сторону и решай: забрать выигрыш или рискнуть ради большего приза?\n\nВаш баланс: {balance} ⭐\n<b>Выберите начальную ставку:</b>"

    await safe_edit_media(
        callback.message,
        media=InputMediaPhoto(media=PHOTO_MAIN_MENU, caption=text, parse_mode="HTML"),
        reply_markup=coinflip_bet_keyboard(),
    )


@router.callback_query(F.data.startswith("coinflip_bet:"))
async def bet_coinflip_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await clean_junk_message(callback, state)
    bet = int(callback.data.split(":")[1])

    ok = await db.update_user_balance(callback.from_user.id, -bet)
    if not ok:
        await callback.answer("Недостаточно звёзд для такой ставки!", show_alert=True)
        return

    await state.set_state(CoinflipGame.in_game)
    await state.update_data(initial_bet=bet, current_pot=bet, level=1)

    text = f"Вы поставили <b>{bet} ⭐</b>.\n\nКуда упадёт монета?"
    await callback.message.edit_caption(
        caption=text, reply_markup=coinflip_choice_keyboard()
    )


@router.callback_query(CoinflipGame.in_game, F.data.startswith("coinflip_play:"))
async def play_coinflip_handler(callback: CallbackQuery, state: FSMContext) -> None:
    user_choice = callback.data.split(":")[1]

    game_data = await state.get_data()
    level = game_data.get("level", 1)
    current_pot = game_data.get("current_pot")

    level_config = COINFLIP_LEVELS.get(level)
    if not level_config:
        await callback.answer(
            "Вы достигли максимального уровня! Забирайте выигрыш.", show_alert=True
        )
        await cashout_coinflip_handler(callback, state)
        return

    win_chance = level_config["chance"]
    prize_mult = level_config["prize_mult"]

    is_win = random.randint(1, 100) <= win_chance
    result = user_choice if is_win else ("tails" if user_choice == "heads" else "heads")
    result_emoji = "🦅" if result == "heads" else "🪙"

    if is_win:
        new_pot = int(current_pot * prize_mult)
        await state.update_data(current_pot=new_pot, level=level + 1)
        next_level_chance = COINFLIP_LEVELS.get(level + 1, {}).get("chance", 0)

        text = f"Выпал {result_emoji}! **Вы угадали!**\n\nВаш выигрыш составляет уже <b>{new_pot} ⭐</b>.\n\nХотите рискнуть ещё раз? Шанс на победу в следующем раунде: <b>{next_level_chance}%</b>"
        await callback.message.edit_caption(
            caption=text, reply_markup=coinflip_continue_keyboard(new_pot)
        )
    else:
        initial_bet = game_data.get("initial_bet", 0)
        text = f"Выпал {result_emoji}! **Вы проиграли...**\n\nВаша ставка в <b>{initial_bet} ⭐</b> сгорела."
        await state.clear()
        await callback.message.edit_caption(
            caption=text, reply_markup=coinflip_bet_keyboard()
        )
        await callback.answer("Не повезло!", show_alert=True)


@router.callback_query(CoinflipGame.in_game, F.data == "coinflip_continue")
async def continue_coinflip_handler(callback: CallbackQuery, state: FSMContext) -> None:
    game_data = await state.get_data()
    level = game_data.get("level", 1)
    await callback.message.edit_caption(
        caption=f"Риск — благородное дело! Шанс угадать: {COINFLIP_LEVELS.get(level, {}).get('chance', 0)}%\nКуда упадёт монета?",
        reply_markup=coinflip_choice_keyboard(),
    )


@router.callback_query(CoinflipGame.in_game, F.data == "coinflip_cashout")
async def cashout_coinflip_handler(callback: CallbackQuery, state: FSMContext) -> None:
    game_data = await state.get_data()
    prize = game_data.get("current_pot", 0)

    await db.update_user_balance(callback.from_user.id, prize)

    await callback.answer(f"Отличный выбор! Вы забираете {prize} ⭐.", show_alert=True)
    await state.clear()
    await start_coinflip_handler(callback, state)


@router.callback_query(F.data == "game_coinflip_cancel")
async def cancel_coinflip_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if (await state.get_state()) == CoinflipGame.in_game.state:
        # Ставка уже была списана, поэтому она сгорает
        await callback.answer(
            "Вы отменили игру, ваша начальная ставка потеряна.", show_alert=True
        )

    await state.clear()
    await start_coinflip_handler(callback, state)


# --- СИСТЕМА ДОСТИЖЕНИЙ ---
@router.callback_query(F.data == "achievements_menu")
async def achievements_menu_handler(
    callback: CallbackQuery, state: FSMContext, bot: Bot
) -> None:
    await clean_junk_message(callback, state)
    user_id = callback.from_user.id
    try:
        all_ach = await db.get_all_achievements()
        user_ach = await db.get_user_achievements(user_id)
    except Exception as e:
        print(f"Error loading achievements: {e}")
        await callback.answer("Ошибка загрузки достижений.", show_alert=True)
        return

    text = "Выполняй <b>Достижения</b> и получай жирные награды! 🏆"
    await safe_edit_media(
        callback.message,
        media=InputMediaPhoto(
            media=PHOTO_ACHIEVEMENTS, caption=text, parse_mode="HTML"
        ),
        reply_markup=achievements_menu_keyboard(all_ach, user_ach, page=1),
    )


@router.callback_query(F.data.startswith("achievements_page:"))
async def achievements_page_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await clean_junk_message(callback, state)
    try:
        page = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Страница недоступна.", show_alert=True)
        return

    user_id = callback.from_user.id
    try:
        all_ach = await db.get_all_achievements()
        user_ach = await db.get_user_achievements(user_id)
    except Exception as e:
        print(f"Error loading achievements page: {e}")
        await callback.answer("Ошибка загрузки достижений.", show_alert=True)
        return

    try:
        await callback.message.edit_reply_markup(
            reply_markup=achievements_menu_keyboard(all_ach, user_ach, page=page)
        )
    except TelegramBadRequest:
        pass


# --- ЗАГЛУШКИ ---
@router.callback_query(F.data == "game_casino")
async def game_stubs_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await clean_junk_message(callback, state)
    await callback.answer("Скоро... 🤫", show_alert=True)


@router.callback_query(F.data == "ignore_click")
async def ignore_click_handler(callback: CallbackQuery) -> None:
    await callback.answer("Это достижение. Выполняй цели, чтобы его открыть!")
