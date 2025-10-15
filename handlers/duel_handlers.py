# plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/handlers/duel_handlers.py

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
from handlers.utils import safe_delete, safe_edit_caption, safe_send_message
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


@dataclass
class Player:
    id: int
    message_id: int
    hand: list[int] = field(default_factory=list)
    played_card: Optional[int] = None
    has_boosted: bool = False
    has_rerolled: bool = False


@dataclass
class DuelMatch:
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


duel_queue: dict[int, tuple[int, int, Optional[str]]] = {}
active_duels: dict[int, DuelMatch] = {}
DUEL_MATCHMAKING_LOCK = asyncio.Lock()
rand = secrets.SystemRandom()


def deal_hand() -> list[int]:
    return rand.sample(range(1, 11), 5)


async def update_game_interface(
    bot: Bot, match: DuelMatch, text_override: Optional[str] = None
):
    event_text = LEXICON.get(match.current_event, "") if match.current_event else ""

    # Красивое отображение карт с эмодзи
    card_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    def format_hand(hand):
        formatted_cards = []
        for card in sorted(hand):
            emoji = card_emojis[card - 1] if card <= 10 else f"{card}"
            formatted_cards.append(emoji)
        return " ".join(formatted_cards)

    p1_hand_text = format_hand(match.p1.hand)
    p2_hand_text = format_hand(match.p2.hand)
    p1_text = text_override or LEXICON["duel_turn"].format(
        round=match.round,
        p1_wins=match.p1_wins,
        p2_wins=match.p2_wins,
        opponent_card="?",
        hand_text=p1_hand_text,
        event_text=event_text,
    )
    p2_text = text_override or LEXICON["duel_turn"].format(
        round=match.round,
        p1_wins=match.p2_wins,
        p2_wins=match.p1_wins,
        opponent_card="?",
        hand_text=p2_hand_text,
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
    if match.p1_wins >= 2 or match.p2_wins >= 2:
        return await resolve_game_end(bot, match)
    match.round += 1
    match.p1.played_card = None
    match.p2.played_card = None
    match.current_event = None

    # Увеличиваем шанс магических событий для большей захватывающей игры
    event_chance = 0.15  # 15% вместо 10%
    if rand.random() < event_chance:
        # Добавляем больше разнообразия в события
        events = ["event_comet", "event_black_hole"]

        # В последних раундах больше шансов на комету
        if match.round >= 3:
            events.extend(["event_comet", "event_comet"])  # Удваиваем шанс кометы

        match.current_event = rand.choice(events)
    await update_game_interface(bot, match)


async def resolve_round(bot: Bot, match: DuelMatch):
    p1_card, p2_card = match.p1.played_card, match.p2.played_card
    if p1_card is None or p2_card is None:
        return
    round_winner = None
    p1_round_text = ""
    p2_round_text = ""

    if match.current_event == "event_black_hole":
        p1_round_text = p2_round_text = LEXICON["event_black_hole_triggered"]
    elif p1_card > p2_card:
        match.p1_wins += 1
        round_winner = match.p1
        p1_round_text = "🏆 **ПОБЕДА!** Ваша карта сильнее! 🏆"
        p2_round_text = "😔 **ПОРАЖЕНИЕ...** Карта соперника оказалась сильнее 😔"
    elif p2_card > p1_card:
        match.p2_wins += 1
        round_winner = match.p2
        p1_round_text = "😔 **ПОРАЖЕНИЕ...** Карта соперника оказалась сильнее 😔"
        p2_round_text = "🏆 **ПОБЕДА!** Ваша карта сильнее! 🏆"
    else:
        p1_round_text = p2_round_text = "🤝 **НИЧЬЯ!** Одинаковые карты! 🤝"
    if match.current_event == "event_comet" and round_winner:
        if round_winner.id == match.p1.id:
            match.p1_wins = min(match.p1_wins + 1, 2)
        else:
            match.p2_wins = min(match.p2_wins + 1, 2)
        # Добавляем эффект кометы к персональным сообщениям
        comet_text = "\n" + LEXICON["event_comet_triggered"]
        p1_round_text += comet_text
        p2_round_text += comet_text

    # Создаем персональные сообщения для каждого игрока
    p1_final_text = LEXICON["duel_round_end"].format(
        p1_card=p1_card, p2_card=p2_card, round_result=p1_round_text
    )
    p2_final_text = LEXICON["duel_round_end"].format(
        p1_card=p2_card, p2_card=p1_card, round_result=p2_round_text
    )

    # Отправляем персональные сообщения каждому игроку
    await asyncio.gather(
        safe_edit_caption(
            bot,
            p1_final_text,
            match.p1.id,
            match.p1.message_id,
            reply_markup=back_to_duels_keyboard(),
        ),
        safe_edit_caption(
            bot,
            p2_final_text,
            match.p2.id,
            match.p2.message_id,
            reply_markup=back_to_duels_keyboard(),
        ),
    )
    await asyncio.sleep(4)
    await start_new_round(bot, match)


async def resolve_game_end(bot: Bot, match: DuelMatch):
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

    # Проверяем достижения для победителя
    try:
        from aiogram import Bot as BotType

        if isinstance(bot, BotType):
            # Проверяем достижения по количеству побед
            winner_stats = await db.get_user_duel_stats(winner_id)
            wins = winner_stats.get("wins", 0)

            # Достижения за победы в дуэлях
            if wins == 1:
                await db.grant_achievement(winner_id, "first_duel_win", bot)
            elif wins == 5:
                await db.grant_achievement(winner_id, "duel_warrior", bot)
            elif wins == 10:
                await db.grant_achievement(winner_id, "duel_master", bot)
            elif wins == 25:
                await db.grant_achievement(winner_id, "duel_legend", bot)
    except Exception as e:
        logging.warning(f"Failed to check duel achievements: {e}")
    # Создаем персональные сообщения об окончании игры
    if winner_id == match.p1.id:
        # P1 победил
        p1_final_text = (
            f"🎉 **ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ!** 🎉\n\n"
            f"🏆 Счёт: {match.p1_wins}:{match.p2_wins}\n"
            f"💰 Выигрыш: **{prize} ⭐**\n\n"
            f"Отличная игра! Ваши звёзды уже начислены на баланс."
        )
        p2_final_text = (
            f"😔 **Поражение...** 😔\n\n"
            f"📊 Счёт: {match.p2_wins}:{match.p1_wins}\n"
            f"💸 Потеря: **{match.stake} ⭐**\n\n"
            f"Не расстраивайтесь! В следующий раз повезёт больше!"
        )
    else:
        # P2 победил
        p1_final_text = (
            f"😔 **Поражение...** 😔\n\n"
            f"📊 Счёт: {match.p1_wins}:{match.p2_wins}\n"
            f"💸 Потеря: **{match.stake} ⭐**\n\n"
            f"Не расстраивайтесь! В следующий раз повезёт больше!"
        )
        p2_final_text = (
            f"🎉 **ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ!** 🎉\n\n"
            f"🏆 Счёт: {match.p2_wins}:{match.p1_wins}\n"
            f"💰 Выигрыш: **{prize} ⭐**\n\n"
            f"Отличная игра! Ваши звёзды уже начислены на баланс."
        )

    # Отправляем персональные сообщения каждому игроку
    await asyncio.gather(
        safe_edit_caption(
            bot,
            p1_final_text,
            match.p1.id,
            match.p1.message_id,
            reply_markup=back_to_duels_keyboard(),
        ),
        safe_edit_caption(
            bot,
            p2_final_text,
            match.p2.id,
            match.p2.message_id,
            reply_markup=back_to_duels_keyboard(),
        ),
    )
    if match.match_id in active_duels:
        del active_duels[match.match_id]


async def start_duel_game(
    bot: Bot,
    match_id: int,
    p1_id: int,
    p2_id: int,
    stake: int,
    p1_msg_id: int,
    p2_msg_id: int,
    trace_id: str,
):
    p1 = Player(id=p1_id, message_id=p1_msg_id, hand=deal_hand())
    p2 = Player(id=p2_id, message_id=p2_msg_id, hand=deal_hand())
    match = DuelMatch(match_id=match_id, p1=p1, p2=p2, stake=stake, trace_id=trace_id)
    active_duels[match_id] = match
    logging.info(
        f"Duel game starting. Match ID: {match_id}",
        extra={"trace_id": trace_id, "p1_id": p1_id, "p2_id": p2_id, "stake": stake},
    )
    await update_game_interface(bot, match)


@router.callback_query(GameCallback.filter((F.name == "duel") & (F.action == "start")))
async def duel_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
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
    user_language = await db.get_user_language(callback.from_user.id)
    await safe_edit_caption(
        bot,
        caption,
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=duel_stake_keyboard(user_language),
        photo=settings.PHOTO_DUEL_MENU,
    )
    await callback.answer()


@router.callback_query(DuelCallback.filter(F.action == "stake"))
async def find_duel_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot, **data
):
    raw_stake = callback_data.value
    if raw_stake is None or not callback.message:
        return
    stake = int(raw_stake)
    user_id = callback.from_user.id
    balance = await db.get_user_balance(user_id)
    trace_id = data.get("trace_id", "unknown")
    extra = {"trace_id": trace_id, "user_id": user_id, "stake": stake}
    if balance < stake:
        return await callback.answer("Недостаточно средств!", show_alert=True)
    async with DUEL_MATCHMAKING_LOCK:
        if stake in duel_queue:
            opponent_id, opponent_msg_id, opponent_trace_id = duel_queue[stake]
            if opponent_id == user_id:
                return await callback.answer("Вы уже в поиске.", show_alert=True)
            match_id = await db.create_duel(opponent_id, user_id, stake)
            if match_id:
                del duel_queue[stake]
                logging.info(
                    f"Duel match created successfully: {match_id}", extra=extra
                )

                # Показываем красивое сообщение о начале матча
                prize = stake * 2 - int(stake * 2 * (settings.DUEL_RAKE_PERCENT / 100))
                match_text = LEXICON["duel_match_found"].format(
                    stake=stake, prize=prize
                )

                # Отправляем сообщение обоим игрокам
                await asyncio.gather(
                    safe_edit_caption(
                        bot, match_text, opponent_id, opponent_msg_id, reply_markup=None
                    ),
                    safe_edit_caption(
                        bot,
                        match_text,
                        callback.message.chat.id,
                        callback.message.message_id,
                        reply_markup=None,
                    ),
                )

                # Небольшая пауза для драматического эффекта
                await asyncio.sleep(2)
                asyncio.create_task(
                    start_duel_game(
                        bot,
                        match_id,
                        opponent_id,
                        user_id,
                        stake,
                        opponent_msg_id,
                        callback.message.message_id,
                        trace_id,
                    )
                )
            else:
                logging.warning(
                    f"Failed to create duel atomically for stake {stake}", extra=extra
                )
                await callback.answer(
                    "Не удалось начать игру. Возможно, у вас или у соперника не хватило средств.",
                    show_alert=True,
                )
                await safe_send_message(
                    bot,
                    opponent_id,
                    "Попытка начать дуэль не удалась, поиск продолжается.",
                )
        else:
            logging.info("User started duel search", extra=extra)
            if callback.message:
                duel_queue[stake] = (user_id, callback.message.message_id, trace_id)
    await safe_edit_caption(
        bot,
        LEXICON["duel_searching"].format(stake=stake),
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=duel_searching_keyboard(stake),
    )
    await callback.answer()


@router.callback_query(DuelCallback.filter(F.action == "cancel_search"))
async def cancel_duel_search_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot, state: FSMContext
):
    raw_stake = callback_data.value
    if raw_stake is None or not callback.message:
        return
    stake = int(raw_stake)
    user_id = callback.from_user.id
    trace_id = state.key.user_id if state.key else "unknown"
    extra = {"trace_id": trace_id, "user_id": user_id, "stake": stake}
    async with DUEL_MATCHMAKING_LOCK:
        if stake in duel_queue and duel_queue[stake][0] == user_id:
            del duel_queue[stake]
            logging.info("User cancelled duel search", extra=extra)
            await callback.answer("Поиск отменен.", show_alert=True)
            await duel_menu_handler(callback, state, bot)
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
    match_id = callback_data.match_id
    raw_card_value = callback_data.value
    if match_id is None or raw_card_value is None:
        return
    card_value = int(raw_card_value)
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
        # Красивые сообщения при игре карт
        card_messages = {
            1: "🃏 Скромно, но смело!",
            2: "🃏 Начинаем с малого!",
            3: "🃏 Осторожная стратегия!",
            4: "🃏 Средняя карта в деле!",
            5: "🃏 Золотая середина!",
            6: "🃏 Неплохой выбор!",
            7: "🔥 Сильная карта!",
            8: "🔥 Отличный ход!",
            9: "✨ Мощная атака!",
            10: "🎆 МАКСИМАЛЬНАЯ МОЩЬ!",
        }

        message = card_messages.get(card_value, f"🃏 Карта {card_value} в игре!")
        await callback.answer(message)
        if match.p1.played_card and match.p2.played_card:
            asyncio.create_task(resolve_round(bot, match))
        else:
            await update_game_interface(bot, match)


@router.callback_query(DuelCallback.filter(F.action == "boost"))
async def boost_card_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot
):
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
            f"Недостаточно средств. Нужна {settings.DUEL_BOOST_COST} ⭐.",
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
    match_id = callback_data.match_id
    raw_card_to_boost = callback_data.value
    if match_id is None or raw_card_to_boost is None:
        return
    card_to_boost = int(raw_card_to_boost)
    user_id = callback.from_user.id
    if match_id not in active_duels:
        return await callback.answer("Игра не найдена.", show_alert=True)
    match = active_duels[match_id]
    async with match.lock:
        player = match.p1 if user_id == match.p1.id else match.p2
        if player.has_boosted or card_to_boost not in player.hand:
            return await update_game_interface(bot, match)
        success = await db.spend_balance(
            user_id, settings.DUEL_BOOST_COST, "duel_boost", ref_id=str(match_id)
        )
        if not success:
            await callback.answer("Не удалось списать средства.", show_alert=True)
            return await update_game_interface(bot, match)
        card_index = player.hand.index(card_to_boost)
        player.hand[card_index] += 2
        player.has_boosted = True
        await callback.answer(
            f"⚡ **МАГИЧЕСКОЕ УСИЛЕНИЕ!** ⚡\n"
            f"🃏 Карта {card_to_boost} превращается в мощную {player.hand[card_index]}! 🔥",
            show_alert=True,
        )
        await update_game_interface(bot, match)


@router.callback_query(DuelCallback.filter(F.action == "boost_cancel"))
async def boost_cancel_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot
):
    match_id = callback_data.match_id
    if not match_id or match_id not in active_duels:
        return await callback.answer("Игра не найдена.", show_alert=True)
    await callback.answer()
    await update_game_interface(bot, active_duels[match_id])


@router.callback_query(DuelCallback.filter(F.action == "reroll"))
async def reroll_hand_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot
):
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
        success = await db.spend_balance(
            user_id, settings.DUEL_REROLL_COST, "duel_reroll", ref_id=str(match_id)
        )
        if not success:
            await callback.answer("Не удалось списать средства.", show_alert=True)
            return
        player.hand = deal_hand()
        player.has_rerolled = True
        await callback.answer(
            "🌀 **МАГИЯ ПЕРЕТАСОВКИ!** 🌀\n"
            "🃏 Вы получили новые карты! Может, судьба будет к вам благосклоннее? ✨",
            show_alert=True,
        )
        await update_game_interface(bot, match)


@router.callback_query(DuelCallback.filter(F.action == "surrender"))
async def surrender_handler(
    callback: CallbackQuery, callback_data: DuelCallback, bot: Bot
):
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
    if match.p1.id == callback.from_user.id:
        match.p2_wins = 2
        match.p1_wins = 0
    else:
        match.p1_wins = 2
        match.p2_wins = 0
    await resolve_game_end(bot, match)
    await callback.answer("Вы сдались.", show_alert=True)


@router.callback_query(DuelCallback.filter(F.action == "stuck"))
async def duel_stuck_handler(callback: CallbackQuery, bot: Bot):
    cleaned_count = 0
    for match_id in list(active_duels.keys()):
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


# Новые обработчики для обучения и статистики
@router.callback_query(
    GameCallback.filter((F.name == "help") & (F.action == "duel_tutorial"))
)
async def duel_tutorial_handler(callback: CallbackQuery, bot: Bot):
    """Обработчик обучения по дуэлям."""
    if not callback.message:
        return

    await safe_edit_caption(
        bot,
        LEXICON["duel_tutorial"],
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=back_to_duels_keyboard(),
    )
    await callback.answer()


@router.callback_query(
    GameCallback.filter((F.name == "help") & (F.action == "duel_stats"))
)
async def duel_stats_handler(callback: CallbackQuery, bot: Bot):
    """Обработчик статистики дуэлей."""
    if not callback.message:
        return

    user_id = callback.from_user.id
    stats = await db.get_user_duel_stats(user_id)
    balance = await db.get_user_balance(user_id)

    total_games = stats.get("wins", 0) + stats.get("losses", 0)
    win_rate = (stats.get("wins", 0) / total_games * 100) if total_games > 0 else 0

    stats_text = (
        f"📊 **ВАША СТАТИСТИКА В ДУЭЛЯХ** 📊\n\n"
        f"💰 **Баланс:** {balance} ⭐\n\n"
        f"⚔️ **ОБЩАЯ СТАТИСТИКА:**\n"
        f"🏆 Побед: {stats.get('wins', 0)}\n"
        f"❌ Поражений: {stats.get('losses', 0)}\n"
        f"🎲 Всего игр: {total_games}\n"
        f"💯 Процент побед: {win_rate:.1f}%\n\n"
    )

    if win_rate >= 70:
        stats_text += "🎆 **ЛЕГЕНДА!** Невероятные результаты!"
    elif win_rate >= 60:
        stats_text += "🏅 **МАСТЕР!** Отличная игра!"
    elif win_rate >= 50:
        stats_text += "🔥 **ОПЫТНЫЙ!** Хорошие результаты!"
    elif total_games > 0:
        stats_text += "🌱 **НОВИЧОК!** Продолжай тренироваться!"
    else:
        stats_text += "🎆 **ГОТОВ К ПЕРВОЙ ДУЭЛИ!** Покажи на что способен!"

    await safe_edit_caption(
        bot,
        stats_text,
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=back_to_duels_keyboard(),
    )
    await callback.answer()
