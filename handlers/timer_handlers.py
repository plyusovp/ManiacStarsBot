# handlers/timer_handlers.py
import asyncio
import logging
from collections import defaultdict

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import settings
from database import db
from handlers.utils import clean_junk_message
# --- ИЗМЕНЕНО: Удален несуществующий импорт 'timer_rematch_offer_keyboard' ---
from keyboards.inline import (timer_finish_keyboard, timer_game_keyboard,
                              timer_searching_keyboard, timer_stake_keyboard)
from lexicon.texts import LEXICON

router = Router()
logger = logging.getLogger(__name__)

timer_queue = defaultdict(dict)
active_timers = {}


async def start_timer_game(bot, match_id, p1_id, p2_id, stake, stop_second):
    active_timers[match_id] = {
        "p1_id": p1_id,
        "p2_id": p2_id,
        "stake": stake,
        "stop_second": stop_second,
        "p1_clicked_at": None,
        "p2_clicked_at": None,
    }

    try:
        p1 = await bot.get_chat(p1_id)
        p2 = await bot.get_chat(p2_id)
    except Exception as e:
        logger.error(f"Не удалось получить информацию об игроках: {e}")
        del active_timers[match_id]
        return

    p1_username = f"@{p1.username}" if p1.username else p1.full_name
    p2_username = f"@{p2.username}" if p2.username else p2.full_name

    text = LEXICON["timer_match_found"].format(
        p1_username=p1_username, p2_username=p2_username, stake=stake
    )
    keyboard = timer_game_keyboard(match_id, stop_second)

    await asyncio.gather(
        bot.send_message(p1_id, text, reply_markup=keyboard),
        bot.send_message(p2_id, text, reply_markup=keyboard),
    )


async def resolve_timer_game(bot, match_id):
    game = active_timers.get(match_id)
    if not game or not all([game["p1_clicked_at"], game["p2_clicked_at"]]):
        return

    p1_diff = abs(game["p1_clicked_at"] - game["stop_second"])
    p2_diff = abs(game["p2_clicked_at"] - game["stop_second"])

    winner_id, loser_id, is_draw = None, None, False
    if p1_diff < p2_diff:
        winner_id, loser_id = game["p1_id"], game["p2_id"]
    elif p2_diff < p1_diff:
        winner_id, loser_id = game["p2_id"], game["p1_id"]
    else:
        is_draw = True

    bank = game["stake"] * 2
    rake = int(bank * (settings.DUEL_RAKE_PERCENT / 100))
    prize = bank - rake

    if is_draw:
        await db.finish_timer_match(match_id, is_draw=True, new_bank=0)
        text = LEXICON["timer_draw"].format(
            p1_result=game["p1_clicked_at"], p2_result=game["p2_clicked_at"]
        )
        await asyncio.gather(
            bot.send_message(
                game["p1_id"], text, reply_markup=timer_finish_keyboard()
            ),
            bot.send_message(
                game["p2_id"], text, reply_markup=timer_finish_keyboard()
            ),
        )
    else:
        await db.finish_timer_match(match_id, winner_id=winner_id)
        winner_text = LEXICON["timer_win_result"].format(
            p1_result=game["p1_clicked_at"],
            p2_result=game["p2_clicked_at"],
            prize=prize,
        )
        loser_text = LEXICON["timer_loss_result"].format(
            p1_result=game["p1_clicked_at"], p2_result=game["p2_clicked_at"]
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

    if user_id in timer_queue[stake]:
        return await callback.answer(
            "Вы уже находитесь в поиске игры.", show_alert=True
        )

    if timer_queue[stake]:
        opponent_id = list(timer_queue[stake].keys())[0]
        del timer_queue[stake][opponent_id]

        bank = stake * 2
        match_id, stop_second = await db.create_timer_match(
            user_id, opponent_id, stake, bank
        )
        await start_timer_game(bot, match_id, user_id, opponent_id, stake, stop_second)
    else:
        timer_queue[stake][user_id] = True
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
    _, match_id, stop_at = callback.data.split(":")
    match_id, stop_at = int(match_id), int(stop_at)
    user_id = callback.from_user.id

    game = active_timers.get(match_id)
    if not game:
        return await callback.answer("Игра не найдена или уже завершена.")

    player_role = "p1" if user_id == game["p1_id"] else "p2"
    if game[f"{player_role}_clicked_at"] is not None:
        return await callback.answer("Вы уже сделали свой ход.")

    game[f"{player_role}_clicked_at"] = stop_at
    await db.update_timer_player_click(match_id, user_id, stop_at)

    await callback.message.edit_text("✅ Ваш ход принят. Ожидаем соперника...")
    await resolve_timer_game(bot, match_id)
