# keyboards/inline.py
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_reply_keyboard():
    """Создаёт постоянную клавиатуру с кнопкой 'Меню'."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 Меню")]],
        resize_keyboard=True,
        input_field_placeholder="Нажмите 'Меню', чтобы вернуться...",
    )


def main_menu():
    """Создаёт главное меню с компактным расположением кнопок."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Заработать на хлеб ⭐", callback_data="earn"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👾 Развлечения", callback_data="entertainment_menu"
                ),
                InlineKeyboardButton(text="🪪 Профиль", callback_data="profile"),
            ],
            [
                InlineKeyboardButton(text="💸 Вывод", callback_data="withdraw"),
                InlineKeyboardButton(text="📈 Топ", callback_data="top"),
            ],
            [
                InlineKeyboardButton(
                    text="📰 Наш канал", url="https://t.me/+Hu5bVLrGpRpiMTBk"
                ),
                InlineKeyboardButton(
                    text="😍 Наши выводы", url="https://t.me/+234P6hHN4YEwMDE8"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="☎️ Техподдержка", url="https://t.me/m/0gHWD35HYTZk"
                )
            ],
        ]
    )


def earn_menu_keyboard():
    """Создаёт меню для раздела 'Заработать' с кнопкой промокода."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎟️ Ввести промокод", callback_data="promo_code"
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )


def entertainment_menu_keyboard():
    """Создаёт клавиатуру для меню развлечений."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏆 Достижения", callback_data="achievements_menu"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🪙 Орёл и Решка", callback_data="game_coinflip"
                )
            ],
            [InlineKeyboardButton(text="⚡ Дуэли 1x1", callback_data="game_duel")],
            [
                InlineKeyboardButton(
                    text="⏳ Звёздный Таймер", callback_data="game_timer"
                )
            ],
            [InlineKeyboardButton(text="🎰 Казик", callback_data="game_casino")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )


def duel_stake_keyboard():
    """Создаёт клавиатуру для выбора ставки в дуэли."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="10 ⭐", callback_data="duel_stake:10"),
                InlineKeyboardButton(text="25 ⭐", callback_data="duel_stake:25"),
                InlineKeyboardButton(text="50 ⭐", callback_data="duel_stake:50"),
            ],
            [
                InlineKeyboardButton(text="ℹ️ Правила", callback_data="duel_rules"),
                InlineKeyboardButton(
                    text="⬅️ Назад", callback_data="entertainment_menu"
                ),
            ],
        ]
    )


def duel_searching_keyboard():
    """Клавиатура для отмены поиска дуэли."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отменить поиск", callback_data="duel_cancel_search"
                )
            ]
        ]
    )


def duel_stuck_keyboard():
    """Клавиатура для игрока, который застрял в активной дуэли."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏳️ Сдаться и выйти (поражение)",
                    callback_data="duel_leave_active",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад в развлечения", callback_data="entertainment_menu"
                )
            ],
        ]
    )


def duel_round_keyboard(hand: list, match_id: int, boosts_left: int, replace_left: int):
    """Создаёт клавиатуру с картами и тактическими кнопками."""
    builder = InlineKeyboardBuilder()

    card_buttons = []
    for card in sorted(hand, key=lambda x: x[0] if isinstance(x, tuple) else x):
        card_value, original_value = (card, card)
        if isinstance(card, tuple):
            card_value, original_value = card

        card_text = f"🃏 {card_value}"
        if card_value != original_value:
            card_text += f" (+{card_value - original_value})"

        card_buttons.append(
            InlineKeyboardButton(
                text=card_text,
                callback_data=f"duel_play:{match_id}:{card_value}:{original_value}",
            )
        )
    builder.row(*card_buttons)

    action_buttons = []
    if boosts_left > 0:
        action_buttons.append(
            InlineKeyboardButton(
                text=f"⚡ Усилить ({boosts_left})",
                callback_data=f"duel_boost:{match_id}",
            )
        )
    if replace_left > 0:
        action_buttons.append(
            InlineKeyboardButton(
                text=f"🔄 Заменить ({replace_left})",
                callback_data=f"duel_replace:{match_id}",
            )
        )

    if action_buttons:
        builder.row(*action_buttons)

    builder.row(
        InlineKeyboardButton(
            text="🏳️ Сдаться", callback_data=f"duel_surrender:{match_id}"
        )
    )

    return builder.as_markup()


def duel_boost_choice_keyboard(hand: list, match_id: int):
    """Клавиатура для выбора карты, которую нужно усилить."""
    builder = InlineKeyboardBuilder()
    buttons = []
    for card in sorted(hand, key=lambda x: x[0] if isinstance(x, tuple) else x):
        card_value = card[0] if isinstance(card, tuple) else card
        buttons.append(
            InlineKeyboardButton(
                text=f"⚡ {card_value}",
                callback_data=f"duel_boost_choice:{match_id}:{card_value}",
            )
        )
    builder.row(*buttons)
    builder.row(
        InlineKeyboardButton(
            text="🔙 Отмена", callback_data=f"duel_cancel_action:{match_id}"
        )
    )
    return builder.as_markup()


def duel_replace_choice_keyboard(hand: list, match_id: int):
    """Клавиатура для выбора карты, которую нужно заменить."""
    builder = InlineKeyboardBuilder()
    buttons = []
    for card in sorted(hand, key=lambda x: x[0] if isinstance(x, tuple) else x):
        card_value = card[0] if isinstance(card, tuple) else card
        buttons.append(
            InlineKeyboardButton(
                text=f"🔄 {card_value}",
                callback_data=f"duel_replace_choice:{match_id}:{card_value}",
            )
        )
    builder.row(*buttons)
    builder.row(
        InlineKeyboardButton(
            text="🔙 Отмена", callback_data=f"duel_cancel_action:{match_id}"
        )
    )
    return builder.as_markup()


def duel_surrender_confirm_keyboard(match_id: int):
    """Клавиатура для подтверждения сдачи в дуэли."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, сдаться",
                    callback_data=f"duel_surrender_confirm:{match_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Нет, в бой!",
                    callback_data=f"duel_cancel_action:{match_id}",
                ),
            ]
        ]
    )


def duel_finish_keyboard(match_id: int, opponent_id: int):
    """Клавиатура для экрана после матча."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔁 Реванш",
                    callback_data=f"duel_rematch:{match_id}:{opponent_id}",
                )
            ],
            [InlineKeyboardButton(text="🏠 В лобби дуэлей", callback_data="game_duel")],
        ]
    )


def timer_stake_keyboard():
    """Создаёт клавиатуру для выбора ставки в 'Звёздном таймере'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="5 ⭐", callback_data="timer_stake:5"),
                InlineKeyboardButton(text="10 ⭐", callback_data="timer_stake:10"),
                InlineKeyboardButton(text="25 ⭐", callback_data="timer_stake:25"),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад в развлечения", callback_data="entertainment_menu"
                )
            ],
        ]
    )


def timer_game_keyboard(match_id: int):
    """Создаёт клавиатуру для игры в 'Звёздный таймер'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ ЗАБРАТЬ БАНК ⚡", callback_data=f"timer_play:{match_id}"
                )
            ]
        ]
    )


def timer_finish_keyboard(match_id: int, opponent_id: int):
    """Клавиатура для экрана после 'Звёздного таймера'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔁 Реванш",
                    callback_data=f"timer_rematch:{match_id}:{opponent_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В лобби таймера", callback_data="game_timer"
                )
            ],
        ]
    )


def timer_stuck_keyboard():
    """Клавиатура для игрока, который застрял в 'Звёздном таймере'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Покинуть игру", callback_data="timer_leave_active"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад в развлечения", callback_data="entertainment_menu"
                )
            ],
        ]
    )


def coinflip_bet_keyboard():
    """Клавиатура для выбора ставки в 'Орёл и Решка'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 ⭐", callback_data="coinflip_bet:1"),
                InlineKeyboardButton(text="5 ⭐", callback_data="coinflip_bet:5"),
                InlineKeyboardButton(text="10 ⭐", callback_data="coinflip_bet:10"),
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="entertainment_menu")],
        ]
    )


def coinflip_choice_keyboard():
    """Клавиатура для выбора стороны монеты (уже без ставки)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🦅 Орёл", callback_data="coinflip_play:heads"
                ),
                InlineKeyboardButton(
                    text="🪙 Решка", callback_data="coinflip_play:tails"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Отмена", callback_data="game_coinflip_cancel"
                )
            ],
        ]
    )


def coinflip_continue_keyboard(prize: int):
    """Клавиатура для выбора: забрать выигрыш или рискнуть."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Забрать {prize} ⭐", callback_data="coinflip_cashout"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔥 Рискнуть дальше!", callback_data="coinflip_continue"
                )
            ],
        ]
    )


def back_to_main_menu_keyboard():
    """Создаёт простую клавиатуру с кнопкой 'Назад'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )


def back_to_duels_keyboard():
    """Клавиатура с кнопкой 'Назад' в меню дуэлей."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к выбору ставки", callback_data="game_duel"
                )
            ]
        ]
    )


def withdraw_menu():
    """Создаёт клавиатуру для меню вывода с подарками."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="15 ⭐ (🧸)", callback_data="gift_15_teddy"),
                InlineKeyboardButton(text="15 ⭐ (💝)", callback_data="gift_15_heart"),
            ],
            [
                InlineKeyboardButton(text="25 ⭐ (🌹)", callback_data="gift_25_rose"),
                InlineKeyboardButton(
                    text="25 ⭐ (🎁)", callback_data="gift_25_present"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="50 ⭐ (🍾)", callback_data="gift_50_champagne"
                ),
                InlineKeyboardButton(
                    text="50 ⭐ (💐)", callback_data="gift_50_flowers"
                ),
            ],
            [
                InlineKeyboardButton(text="50 ⭐ (🚀)", callback_data="gift_50_rocket"),
                InlineKeyboardButton(text="50 ⭐ (🎂)", callback_data="gift_50_cake"),
            ],
            [
                InlineKeyboardButton(text="100 ⭐ (🏆)", callback_data="gift_100_cup"),
                InlineKeyboardButton(text="100 ⭐ (💍)", callback_data="gift_100_ring"),
            ],
            [
                InlineKeyboardButton(
                    text="100 ⭐ (💎)", callback_data="gift_100_diamond"
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )


def achievements_menu_keyboard(
    all_achievements: list, user_achievements: list, page: int = 1
):
    """Создаёт клавиатуру для меню достижений с пагинацией."""
    builder = InlineKeyboardBuilder()
    items_per_page = 8
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page

    for ach_id, ach_name in all_achievements[start_index:end_index]:
        status_icon = "✅" if ach_id in user_achievements else "❌"
        builder.row(
            InlineKeyboardButton(
                text=f"{status_icon} {ach_name}", callback_data="ignore_click"
            )
        )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="« Пред.", callback_data=f"achievements_page:{page-1}"
            )
        )
    if end_index < len(all_achievements):
        nav_buttons.append(
            InlineKeyboardButton(
                text="След. »", callback_data=f"achievements_page:{page+1}"
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()


def timer_rematch_keyboard(match_id: int, opponent_id: int, bank: int):
    """Клавиатура для предложения реванша в 'Звёздном таймере'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🔁 Принять реванш на {bank} ⭐",
                    callback_data=f"timer_rematch:{match_id}:{opponent_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В лобби таймера", callback_data="game_timer"
                )
            ],
        ]
    )


def timer_rematch_offer_keyboard(match_id: int, opponent_id: int, bank: int):
    """Клавиатура для ПРИНЯТИЯ реванша."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Принять реванш на {bank} ⭐",
                    callback_data=f"timer_rematch_accept:{match_id}:{opponent_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"timer_rematch_decline:{match_id}",
                )
            ],
        ]
    )
