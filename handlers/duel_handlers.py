# handlers/duel_handlers.py
import asyncio
import random
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import database.db as db
from keyboards.inline import (
    duel_stake_keyboard, duel_round_keyboard, duel_finish_keyboard,
    entertainment_menu_keyboard, duel_boost_choice_keyboard,
    duel_replace_choice_keyboard, duel_surrender_confirm_keyboard,
    duel_stuck_keyboard, back_to_duels_keyboard
)
from config import PHOTO_MAIN_MENU

router = Router()

duel_queue = {}
active_duels = {}
rematch_offers = {}

class DuelMatch:
    """Класс для хранения состояния активной дуэли."""
    def __init__(self, match_id, p1_id, p2_id, stake):
        self.match_id = match_id
        self.p1_id = p1_id
        self.p2_id = p2_id
        self.stake = stake
        self.p1_hand = random.sample(range(1, 11), 5)
        self.p2_hand = random.sample(range(1, 11), 5)
        self.p1_wins = 0
        self.p2_wins = 0
        self.current_round = 1
        self.p1_choice = None
        self.p2_choice = None
        self.p1_message_id = None
        self.p2_message_id = None
        self.p1_boosts_left = 1
        self.p2_boosts_left = 1
        self.p1_replace_left = 1
        self.p2_replace_left = 1
        self.bonus_pool = 0
        self.current_round_special = None
        self.p1_timer: asyncio.Task = None
        self.p2_timer: asyncio.Task = None
        self.lock = asyncio.Lock()

    def cancel_timers(self):
        """Отменяет все активные таймеры для раунда."""
        if self.p1_timer and not self.p1_timer.done():
            self.p1_timer.cancel()
        if self.p2_timer and not self.p2_timer.done():
            self.p2_timer.cancel()

async def clean_junk_message(callback: CallbackQuery, state: FSMContext):
    """Удаляет предыдущее 'мусорное' сообщение, если оно было."""
    data = await state.get_data()
    junk_message_id = data.get('junk_message_id')
    if junk_message_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, junk_message_id)
        except TelegramBadRequest:
            pass
        await state.update_data(junk_message_id=None)

def roll_special_card():
    """Определяет, будет ли в раунде спецкарта."""
    roll = random.randint(1, 100)
    if roll <= 8: return 'black_hole'
    if roll <= 18: return 'comet'
    return None

async def round_timeout_task(bot: Bot, match_id: int, player_id: int):
    """Задача, которая ждёт 15 секунд и засчитывает поражение в раунде."""
    await asyncio.sleep(15)
    match = active_duels.get(match_id)
    if not match: return
    
    async with match.lock:
        timed_out_player_id = None
        if player_id == match.p1_id and match.p1_choice is None:
            timed_out_player_id = match.p1_id
            match.p1_choice = -1
        elif player_id == match.p2_id and match.p2_choice is None:
            timed_out_player_id = match.p2_id
            match.p2_choice = -1

        if timed_out_player_id:
            try:
                opponent_id = match.p2_id if timed_out_player_id == match.p1_id else match.p1_id
                await bot.send_message(timed_out_player_id, "⏳ Вы не успели сделать ход. Раунд засчитан как поражение.")
                await bot.send_message(opponent_id, "⏳ Соперник не успел сделать ход!")
            except Exception as e:
                print(f"Ошибка уведомления о таймауте: {e}")
            
            if match.p1_choice is None: match.p1_choice = -1
            if match.p2_choice is None: match.p2_choice = -1
            
            await resolve_round(bot, match_id)

async def send_round_interface(bot: Bot, match: DuelMatch):
    """Отправляет или редактирует обоим игрокам интерфейс раунда."""
    match.cancel_timers()
    match.p1_choice = None
    match.p2_choice = None
    
    match.p1_boosts_left = 1
    match.p2_boosts_left = 1
    match.p1_replace_left = 1
    match.p2_replace_left = 1
    await db.create_duel_round(match.match_id, match.current_round)
    match.current_round_special = roll_special_card()
    
    special_text = ""
    if match.current_round_special == 'comet':
        special_text = "\n\n🌠 **КОМЕТА!** Ставка этого раунда удвоена!"
    elif match.current_round_special == 'black_hole':
        special_text = "\n\n🕳️ **ЧЁРНАЯ ДЫРА!** Этот раунд будет аннулирован!"
    
    score_text = f"Счёт: <b>{match.p1_wins} - {match.p2_wins}</b> (до 2 побед)"
    
    p1_text = f"⚔️ **Раунд {match.current_round}** ⚔️\n\n{score_text}{special_text}\n\nТвои карты:"
    p2_text = f"⚔️ **Раунд {match.current_round}** ⚔️\n\n{score_text}{special_text}\n\nТвои карты:"
    
    p1_keyboard = duel_round_keyboard(match.p1_hand, match.match_id, match.p1_boosts_left, match.p1_replace_left)
    p2_keyboard = duel_round_keyboard(match.p2_hand, match.match_id, match.p2_boosts_left, match.p2_replace_left)

    try:
        await asyncio.gather(
            bot.edit_message_caption(chat_id=match.p1_id, message_id=match.p1_message_id, caption=p1_text, reply_markup=p1_keyboard),
            bot.edit_message_caption(chat_id=match.p2_id, message_id=match.p2_message_id, caption=p2_text, reply_markup=p2_keyboard)
        )
    except TelegramBadRequest as e:
        print(f"Ошибка при отправке интерфейса раунда: {e}")
    
    match.p1_timer = asyncio.create_task(round_timeout_task(bot, match.match_id, match.p1_id))
    match.p2_timer = asyncio.create_task(round_timeout_task(bot, match.match_id, match.p2_id))

async def resolve_round(bot: Bot, match_id: int):
    """Проверяет и завершает раунд, если оба игрока сделали ход."""
    match = active_duels.get(match_id)
    if not match or not (match.p1_choice is not None and match.p2_choice is not None): return
    match.cancel_timers()
    
    if match.current_round_special == 'black_hole':
        await db.save_duel_round(match.match_id, match.current_round, match.p1_choice, match.p2_choice, 'void', 'black_hole')
        await asyncio.gather(
            bot.edit_message_caption(caption="🕳️ **Чёрная дыра!** Раунд аннулирован. Карты возвращены в руку. Переигровка...", chat_id=match.p1_id, message_id=match.p1_message_id, reply_markup=None),
            bot.edit_message_caption(caption="🕳️ **Чёрная дыра!** Раунд аннулирован. Карты возвращены в руку. Переигровка...", chat_id=match.p2_id, message_id=match.p2_message_id, reply_markup=None)
        )
        await asyncio.sleep(3)
        return await send_round_interface(bot, match)
        
    p1_card, p2_card = match.p1_choice, match.p2_choice
    round_winner = 'p1' if p1_card > p2_card else 'p2' if p2_card > p1_card else 'draw'

    comet_bonus = 0
    if match.current_round_special == 'comet' and round_winner != 'draw':
        match.bonus_pool += match.stake
        comet_bonus = match.stake

    if round_winner == 'p1': match.p1_wins += 1
    elif round_winner == 'p2': match.p2_wins += 1
    
    p1_result_text = "Ты победил в раунде!" if round_winner == 'p1' else "Ты проиграл раунд." if round_winner == 'p2' else "Ничья в раунде."
    p2_result_text = "Ты победил в раунде!" if round_winner == 'p2' else "Ты проиграл раунд." if round_winner == 'p1' else "Ничья в раунде."
    
    p1_reveal = f"Вскрытие! Ты: 🃏<b>{p1_card if p1_card != -1 else 'Таймаут'}</b> vs Соперник: 🃏<b>{p2_card if p2_card != -1 else 'Таймаут'}</b>\n\n{p1_result_text}{f' 🌠 Комета принесла бонус в {comet_bonus} ⭐!' if comet_bonus else ''}"
    p2_reveal = f"Вскрытие! Ты: 🃏<b>{p2_card if p2_card != -1 else 'Таймаут'}</b> vs Соперник: 🃏<b>{p1_card if p1_card != -1 else 'Таймаут'}</b>\n\n{p2_result_text}{f' 🌠 Комета принесла бонус в {comet_bonus} ⭐!' if comet_bonus else ''}"

    await db.save_duel_round(match.match_id, match.current_round, p1_card, p2_card, round_winner, match.current_round_special)
    await asyncio.gather(
        bot.edit_message_caption(caption=p1_reveal, chat_id=match.p1_id, message_id=match.p1_message_id, reply_markup=None),
        bot.edit_message_caption(caption=p2_reveal, chat_id=match.p2_id, message_id=match.p2_message_id, reply_markup=None)
    )
    await asyncio.sleep(3)

    is_match_over = match.p1_wins >= 2 or match.p2_wins >= 2 or match.current_round >= 5
    if is_match_over:
        await resolve_match(bot, match_id)
    else:
        match.current_round += 1
        await send_round_interface(bot, match)

async def resolve_match(bot: Bot, match_id: int, surrendered_player_id: int = None):
    match = active_duels.get(match_id)
    if not match: return

    winner_id, loser_id = None, None
    if surrendered_player_id:
        winner_id = match.p2_id if surrendered_player_id == match.p1_id else match.p1_id
        loser_id = surrendered_player_id
    elif match.p1_wins > match.p2_wins:
        winner_id, loser_id = match.p1_id, match.p2_id
    elif match.p2_wins > match.p1_wins:
        winner_id, loser_id = match.p2_id, match.p1_id
    else:
        draw_text = f"🤝 Ничья!\n\nСчёт матча: {match.p1_wins}:{match.p2_wins}.\n\nСтавки возвращены игрокам."
        await asyncio.gather(
            bot.edit_message_caption(caption=draw_text, chat_id=match.p1_id, message_id=match.p1_message_id, reply_markup=duel_finish_keyboard(match_id)),
            bot.edit_message_caption(caption=draw_text, chat_id=match.p2_id, message_id=match.p2_message_id, reply_markup=duel_finish_keyboard(match_id))
        )
        await db.finish_duel(match_id, None, None)
        if match_id in active_duels: del active_duels[match_id]
        return

    score = f"{match.p1_wins}:{match.p2_wins}" if winner_id == match.p1_id else f"{match.p2_wins}:{match.p1_wins}"
    bank = match.stake * 2
    rake = int(bank * 0.07)
    prize = bank - rake + match.bonus_pool
    
    await db.update_user_balance(winner_id, prize)
    await db.update_user_balance(loser_id, -match.stake)
    await db.finish_duel(match_id, winner_id, loser_id)
    
    winner_text = f"🏆 **ПОБЕДА!** 🏆\n\nТы выиграл матч со счётом {score}.\n\nТвой приз: <b>{prize} ⭐</b> (банк {bank}⭐ - комиссия {rake}⭐ + бонусы {match.bonus_pool}⭐)."
    loser_text = f"😿 **Поражение** 😿\n\nСчёт матча: {score}.\n\nНе отчаивайся, в следующий раз повезёт!"
    
    if surrendered_player_id:
        winner_text = f"🏆 **Техническая победа!** 🏆\n\nСоперник сдался. Твой приз: <b>{prize} ⭐</b>."
        loser_text = f"🏳️ **Вы сдались** 🏳️\n\nВы проиграли {match.stake} ⭐."
    
    await asyncio.gather(
        bot.edit_message_caption(caption=winner_text, chat_id=winner_id, message_id=match.p1_message_id, reply_markup=duel_finish_keyboard(match_id)),
        bot.edit_message_caption(caption=loser_text, chat_id=loser_id, message_id=match.p2_message_id, reply_markup=duel_finish_keyboard(match_id))
    )
    if match_id in active_duels: del active_duels[match_id]

async def start_match(bot: Bot, p1_id: int, p2_id: int, stake: int, p1_msg_id: int, p2_msg_id: int):
    if await db.is_user_in_active_duel(p1_id) or await db.is_user_in_active_duel(p2_id):
        return

    match_id = await db.create_duel(p1_id, p2_id, stake)
    match = DuelMatch(match_id, p1_id, p2_id, stake)
    match.p1_message_id = p1_msg_id
    match.p2_message_id = p2_msg_id
    active_duels[match_id] = match
    
    try:
        p1 = await bot.get_chat(p1_id)
        p2 = await bot.get_chat(p2_id)
        p1_username = f"@{p1.username}" if p1.username else p1.full_name
        p2_username = f"@{p2.username}" if p2.username else p2.full_name
    except Exception as e:
        print(f"Не удалось получить информацию об игроках: {e}")
        if match_id in active_duels: del active_duels[match_id]
        return
    
    base_text = f"💥 **Матч найден!** 💥\n\n<b>{p1_username}</b> 🆚 <b>{p2_username}</b>\n\n<b>Ставка:</b> {stake} ⭐ с каждого\n"

    for i in range(5, 0, -1):
        countdown_text = base_text + f"⚔️ **Игра начнётся через: {i}** ⚔️"
        try:
            await asyncio.gather(
                bot.edit_message_caption(caption=countdown_text, chat_id=p1_id, message_id=p1_msg_id),
                bot.edit_message_caption(caption=countdown_text, chat_id=p2_id, message_id=p2_msg_id)
            )
        except TelegramBadRequest as e:
            print(f"Не удалось обновить лобби: {e}")
            if match_id in active_duels: del active_duels[match_id]
            return
        if i > 1:
            await asyncio.sleep(1)
        
    await send_round_interface(bot, match)

@router.callback_query(F.data == "game_duel")
async def duel_menu_handler(callback: CallbackQuery, state: FSMContext):
    await clean_junk_message(callback, state)
    
    if await db.is_user_in_active_duel(callback.from_user.id):
        text = "Вы уже находитесь в активной дуэли. Вы можете сдаться, чтобы начать новую (вы потеряете свою ставку)."
        return await callback.message.edit_media(
            media=InputMediaPhoto(media=PHOTO_MAIN_MENU, caption=text),
            reply_markup=duel_stuck_keyboard()
        )
    
    balance = await db.get_user_balance(callback.from_user.id)
    stats = await db.get_user_duel_stats(callback.from_user.id)
    text = (
        f"⚡ <b>Космические дуэли 1x1</b> ⚡\n\n"
        f"Сразись с другим игроком до 2 побед и забери банк!\n\n"
        f"<i>- У каждого 5 карт (от 1 до 10).\n"
        f"- В свой ход можно 1 раз усилить карту (+1 сила за 1⭐) или 1 раз заменить (2⭐).\n"
        f"- Побеждает тот, чья карта сильнее.</i>\n\n"
        f"<b>Ваш баланс:</b> {balance} ⭐\n"
        f"<b>Побед/Поражений:</b> {stats['wins']}/{stats['losses']}\n\n"
        f"<b>Выберите ставку для поиска игры:</b>"
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(media=PHOTO_MAIN_MENU, caption=text),
        reply_markup=duel_stake_keyboard()
    )

@router.callback_query(F.data == "duel_rules")
async def duel_rules_handler(callback: CallbackQuery):
    rules_text = """
    📜 **Полные правила дуэли** 📜

    • **Цель:** Победить в 2 раундах (или иметь больше побед к концу 5-го раунда).
    • **Карты:** В начале матча вам выдаётся 5 случайных карт с силой от 1 до 10.
    • **Ход:** В каждом раунде вы и ваш соперник выбираете по одной карте. Побеждает тот, чья карта сильнее. Сыгранные карты сбрасываются.
    • **Усиление:** 1 раз за раунд можно потратить 1⭐, чтобы добавить +1 к силе выбранной карты.
    • **Замена:** 1 раз за раунд можно потратить 2⭐, чтобы заменить одну случайную карту из руки на новую.
    • **Спецкарты:** В начале раунда может выпасть случайное событие:
        - 🌠 **Комета:** Победитель раунда добавляет ставку в общий призовой фонд, который заберёт победитель всего матча.
        - 🕳️ **Чёрная дыра:** Раунд аннулируется, карты не сбрасываются. Происходит переигровка.
    • **Таймер:** На каждый ход даётся 15 секунд. Если не успел — раунд засчитывается как поражение.
    """
    await callback.message.edit_caption(
        caption=rules_text,
        reply_markup=back_to_duels_keyboard()
    )

@router.callback_query(F.data.startswith("duel_stake:"))
async def find_duel_handler(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if await db.is_user_in_active_duel(user_id):
        return await callback.answer("Вы уже находитесь в активной дуэли!", show_alert=True)

    stake = int(callback.data.split(":")[1])
    balance = await db.get_user_balance(user_id)
    if balance < stake:
        await callback.answer("У вас недостаточно звёзд для этой ставки!", show_alert=True)
        return

    for s, data in duel_queue.items():
        if data['user_id'] == user_id:
            return await callback.answer("Вы уже находитесь в поиске игры.", show_alert=True)

    opponent_data = duel_queue.get(stake)
    if opponent_data and opponent_data['user_id'] != user_id:
        del duel_queue[stake]
        opponent_id = opponent_data['user_id']
        opponent_msg_id = opponent_data['msg_id']
        
        await callback.message.edit_caption(caption="✅ Соперник найден! Загрузка лобби...")
        await start_match(bot, opponent_id, user_id, stake, opponent_msg_id, callback.message.message_id)
    else:
        duel_queue[stake] = {'user_id': user_id, 'msg_id': callback.message.message_id}
        
        for i in range(45):
            if stake not in duel_queue or duel_queue[stake]['user_id'] != user_id:
                return
            try:
                await callback.message.edit_caption(
                    caption=f"🔎 Ищем соперника со ставкой {stake} ⭐{'.' * (i % 3 + 1)}"
                )
            except TelegramBadRequest:
                if duel_queue.get(stake, {}).get('user_id') == user_id: del duel_queue[stake]
                return
            await asyncio.sleep(1)

        if duel_queue.get(stake, {}).get('user_id') == user_id:
            del duel_queue[stake]
            await callback.message.edit_caption(
                caption=f"😔 Никого не удалось найти со ставкой {stake} ⭐.\nПопробуйте позже или выберите другую ставку.",
                reply_markup=duel_stake_keyboard()
            )

@router.callback_query(F.data.startswith("duel_play:"))
async def duel_play_handler(callback: CallbackQuery, bot: Bot):
    try:
        _, match_id_str, card_value_str, original_value_str = callback.data.split(":")
        match_id, card_value, original_value = int(match_id_str), int(card_value_str), int(original_value_str)
    except ValueError:
        return await callback.answer("Ошибка данных. Попробуйте снова.")

    user_id = callback.from_user.id
    match = active_duels.get(match_id)
    if not match: return await callback.answer("Ошибка: матч не найден или уже завершён.", show_alert=True)

    async with match.lock:
        card_to_find = original_value
        player_hand = match.p1_hand if user_id == match.p1_id else match.p2_hand
        for card in player_hand:
            if isinstance(card, tuple) and card[1] == original_value:
                card_to_find = card
                break

        if user_id == match.p1_id:
            if match.p1_choice is not None: return await callback.answer("Вы уже сделали ход в этом раунде.")
            if card_to_find not in player_hand: return await callback.answer("У вас нет такой карты!")
            if match.p1_timer: match.p1_timer.cancel()
            match.p1_choice = card_value
            match.p1_hand.remove(card_to_find)
            await callback.message.edit_caption(caption="✅ Ваш ход принят. Ожидаем соперника...")
        elif user_id == match.p2_id:
            if match.p2_choice is not None: return await callback.answer("Вы уже сделали ход в этом раунде.")
            if card_to_find not in match.p2_hand: return await callback.answer("У вас нет такой карты!")
            if match.p2_timer: match.p2_timer.cancel()
            match.p2_choice = card_value
            match.p2_hand.remove(card_to_find)
            await callback.message.edit_caption(caption="✅ Ваш ход принят. Ожидаем соперника...")
        else:
            return await callback.answer("Это не ваш матч.")
            
        await callback.answer()
        await resolve_round(bot, match_id)

@router.callback_query(F.data.startswith("duel_replace:"))
async def duel_replace_handler(callback: CallbackQuery, bot: Bot):
    match_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    match = active_duels.get(match_id)
    if not match: return

    async with match.lock:
        player_hand = match.p1_hand if user_id == match.p1_id else match.p2_hand
        player_replaces_left = match.p1_replace_left if user_id == match.p1_id else match.p2_replace_left
        if player_replaces_left < 1: return await callback.answer("Ты уже заменял карту в этом раунде.", show_alert=True)
        
        balance = await db.get_user_balance(user_id)
        if balance < 2: return await callback.answer("Недостаточно звёзд для замены (нужно 2 ⭐).", show_alert=True)

        await db.update_user_balance(user_id, -2)
        
        card_to_replace_options = list(player_hand)
        if not card_to_replace_options: return await callback.answer("Нет карт для замены.")

        card_to_replace = random.choice(card_to_replace_options)
        player_hand.remove(card_to_replace)
        
        current_hand_values = [c[1] if isinstance(c, tuple) else c for c in player_hand]
        possible_new_cards = [c for c in range(1, 11) if c not in current_hand_values]
        new_card = random.choice(possible_new_cards)
        player_hand.append(new_card)

        if user_id == match.p1_id: match.p1_replace_left = 0
        else: match.p2_replace_left = 0

        original_card_value = card_to_replace[1] if isinstance(card_to_replace, tuple) else card_to_replace
        await callback.answer(f"🔄 Карта {original_card_value} заменена на {new_card}!")
        await send_round_interface(bot, match)

@router.callback_query(F.data.startswith("duel_boost:"))
async def duel_boost_handler(callback: CallbackQuery, bot: Bot):
    match_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    match = active_duels.get(match_id)
    if not match: return
    
    async with match.lock:
        player_boosts_left = match.p1_boosts_left if user_id == match.p1_id else match.p2_boosts_left
        if player_boosts_left < 1: return await callback.answer("У тебя не осталось усилений в этом раунде.", show_alert=True)
        
        balance = await db.get_user_balance(user_id)
        if balance < 1: return await callback.answer("Недостаточно звёзд для усиления (нужно 1 ⭐).", show_alert=True)

        player_hand = match.p1_hand if user_id == match.p1_id else match.p2_hand
        await callback.message.edit_caption(
            caption="Какую карту усилить? (+1 к силе за 1 ⭐)",
            reply_markup=duel_boost_choice_keyboard(player_hand, match_id)
        )

@router.callback_query(F.data.startswith("duel_boost_choice:"))
async def duel_boost_choice_handler(callback: CallbackQuery, bot: Bot):
    _, match_id_str, card_str = callback.data.split(":")
    match_id, card_to_boost_original = int(match_id_str), int(card_str)
    user_id = callback.from_user.id
    match = active_duels.get(match_id)
    if not match: return
    
    async with match.lock:
        await db.update_user_balance(user_id, -1)
        player_hand = match.p1_hand if user_id == match.p1_id else match.p2_hand
        
        boosted_value = 0
        card_found = False
        for i, card in enumerate(player_hand):
            current_value = card[0] if isinstance(card, tuple) else card
            original_value = card[1] if isinstance(card, tuple) else card
            if original_value == card_to_boost_original:
                boosted_value = current_value + 1
                player_hand[i] = (boosted_value, original_value)
                card_found = True
                break
        
        if not card_found: return
                
        if user_id == match.p1_id: match.p1_boosts_left -= 1
        else: match.p2_boosts_left -= 1

        await callback.answer(f"⚡ Карта {card_to_boost_original} усилена до {boosted_value}!")
        await send_round_interface(bot, match)

@router.callback_query(F.data.startswith("duel_cancel_action:"))
async def duel_cancel_action_handler(callback: CallbackQuery, bot: Bot):
    match_id = int(callback.data.split(":")[1])
    match = active_duels.get(match_id)
    if not match: return
    await send_round_interface(bot, match)

@router.callback_query(F.data.startswith("duel_surrender:"))
async def duel_surrender_handler(callback: CallbackQuery):
    match_id = int(callback.data.split(":")[1])
    await callback.message.edit_caption(
        caption="Ты уверен, что хочешь сдаться? Ты проиграешь свою ставку.",
        reply_markup=duel_surrender_confirm_keyboard(match_id)
    )

@router.callback_query(F.data.startswith("duel_surrender_confirm:"))
async def duel_surrender_confirm_handler(callback: CallbackQuery, bot: Bot):
    match_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    match = active_duels.get(match_id)
    if not match: return

    async with match.lock:
        match.cancel_timers()
        await resolve_match(bot, match_id, surrendered_player_id=user_id)

@router.callback_query(F.data == "duel_leave_active")
async def duel_leave_active_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id
    match_id = await db.get_active_duel_id(user_id)
    
    if not match_id:
        await callback.answer("Не найдено активных игр для завершения.", show_alert=True)
        return await duel_menu_handler(callback, state)

    match = active_duels.get(match_id)
    if match:
        async with match.lock:
            match.cancel_timers()
            await resolve_match(bot, match_id, surrendered_player_id=user_id)
    else:
        await db.interrupt_duel(match_id)
        await callback.answer("Ваша 'зависшая' игра была принудительно завершена.", show_alert=True)
        await duel_menu_handler(callback, state)

@router.callback_query(F.data.startswith("duel_rematch:"))
async def duel_rematch_handler(callback: CallbackQuery, bot: Bot):
    match_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    if match_id in rematch_offers:
        data = rematch_offers.pop(match_id)
        opponent_id = data['user_id']
        opponent_msg_id = data['msg_id']
        
        if opponent_id == user_id:
            rematch_offers[match_id] = data
            return await callback.answer("Ожидаем ответа соперника...", show_alert=True)
        
        details = await db.get_duel_details(match_id)
        if details:
            p1, p2, stake = details
            
            await bot.edit_message_caption(chat_id=opponent_id, message_id=opponent_msg_id, caption="Соперник принял реванш! Начинаем новый бой...")
            await callback.message.edit_caption(caption="Вы приняли реванш! Начинаем новый бой...")
            await start_match(bot, p1, p2, stake, opponent_msg_id, callback.message.message_id)
        else:
            await callback.answer("Не удалось найти детали прошлого матча.", show_alert=True)
    else:
        rematch_offers[match_id] = {'user_id': user_id, 'msg_id': callback.message.message_id}
        await callback.message.edit_caption(caption="✅ Запрос на реванш отправлен. Ожидаем ответа соперника...")