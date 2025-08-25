# keyboards/inline.py
from typing import List, Union

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import settings
from economy import COINFLIP_LEVELS


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню, восстановленное по скриншоту."""
    buttons = [
        [InlineKeyboardButton(text="⭐ Заработать на хлеб ⭐", callback_data="earn")],
        [
            InlineKeyboardButton(text="👾 Развлечения", callback_data="entertainment"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        ],
        [
            InlineKeyboardButton(text="✅ Вывод", callback_data="withdraw"),
            InlineKeyboardButton(text="🏆 Топ", callback_data="top"),
        ],
        [
            InlineKeyboardButton(text="Наш канал", url=settings.URL_CHANNEL),
            InlineKeyboardButton(text="Наши выводы", url=settings.URL_WITHDRAWALS),
        ],
        [InlineKeyboardButton(text="Техподдержка", url=settings.URL_SUPPORT)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def entertainment_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню 'Развлечения' с промокодом внутри."""
    buttons = [
        [InlineKeyboardButton(text="⚔️ Дуэли 1x1", callback_data="game_duel")],
        [InlineKeyboardButton(text="🪙 Орёл и Решка", callback_data="game_coinflip")],
        [InlineKeyboardButton(text="⏱️ Звёздный таймер", callback_data="game_timer")],
        [InlineKeyboardButton(text="🎟 Промокод", callback_data="promo_code")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def withdraw_menu() -> InlineKeyboardMarkup:
    """Меню вывода с 12 подарками. Названия и цены можно легко поменять здесь."""
    buttons = [
        [
            InlineKeyboardButton(text="🎁 Подарок 1 - 10 ⭐", callback_data="gift_10"),
            InlineKeyboardButton(text="🎁 Подарок 2 - 20 ⭐", callback_data="gift_20"),
        ],
        [
            InlineKeyboardButton(text="🎁 Подарок 3 - 30 ⭐", callback_data="gift_30"),
            InlineKeyboardButton(text="🎁 Подарок 4 - 40 ⭐", callback_data="gift_40"),
        ],
        [
            InlineKeyboardButton(text="🎁 Подарок 5 - 50 ⭐", callback_data="gift_50"),
            InlineKeyboardButton(text="🎁 Подарок 6 - 60 ⭐", callback_data="gift_60"),
        ],
        [
            InlineKeyboardButton(text="🎁 Подарок 7 - 70 ⭐", callback_data="gift_70"),
            InlineKeyboardButton(text="🎁 Подарок 8 - 80 ⭐", callback_data="gift_80"),
        ],
        [
            InlineKeyboardButton(text="🎁 Подарок 9 - 90 ⭐", callback_data="gift_90"),
            InlineKeyboardButton(text="🎁 Подарок 10 - 100 ⭐", callback_data="gift_100"),
        ],
        [
            InlineKeyboardButton(text="🎁 Подарок 11 - 150 ⭐", callback_data="gift_150"),
            InlineKeyboardButton(text="🎁 Подарок 12 - 200 ⭐", callback_data="gift_200"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- Остальные клавиатуры (без изменений, но привожу для полноты) ---

def back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def earn_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_main_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📬 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🎁 Заявки на вывод", callback_data="admin_rewards")],
        [
            InlineKeyboardButton(text="🎟 Промокоды", callback_data="admin_promos"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        ],
        [InlineKeyboardButton(text="⚙️ Управление", callback_data="admin_manage")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_rewards_menu(page: int, total_pages: int) -> InlineKeyboardMarkup:
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_rewards_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_rewards_page_{page+1}"))

    buttons = [
        nav_buttons,
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_reward_details_menu(reward_id: int, user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin_reward_approve_{reward_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reward_reject_{reward_id}")
        ],
        [
             InlineKeyboardButton(text="🎉 Выполнено", callback_data=f"admin_reward_fulfill_{reward_id}")
        ],
        [
            InlineKeyboardButton(text="👤 Инфо о юзере", callback_data=f"admin_user_info_{user_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ К списку", callback_data="admin_rewards")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_promos_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin_promo_create")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_manage_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="💰 Начислить", callback_data="admin_grant"),
            InlineKeyboardButton(text="💸 Списать", callback_data="admin_debit")
        ],
        [
            InlineKeyboardButton(text="🔄 Пересчитать баланс", callback_data="admin_recalc")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def duel_stake_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="1 ⭐", callback_data="duel_stake:1"),
            InlineKeyboardButton(text="3 ⭐", callback_data="duel_stake:3"),
            InlineKeyboardButton(text="5 ⭐", callback_data="duel_stake:5"),
        ],
        [
            InlineKeyboardButton(text="10 ⭐", callback_data="duel_stake:10"),
            InlineKeyboardButton(text="25 ⭐", callback_data="duel_stake:25"),
        ],
        [InlineKeyboardButton(text="📜 Правила", callback_data="duel_rules")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="entertainment")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def duel_searching_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="❌ Отменить поиск", callback_data="duel_cancel_search")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def duel_round_keyboard(
    hand: List[Union[int, tuple]], match_id: int, boosts: int, replaces: int
) -> InlineKeyboardMarkup:
    hand_buttons = []
    row = []
    for card in sorted(hand, key=lambda x: x[0] if isinstance(x, tuple) else x):
        if isinstance(card, tuple):
            value, original_value = card
            text = f"⚡️{value} ({original_value})"
        else:
            value, original_value = card, card
            text = str(value)
        row.append(
            InlineKeyboardButton(
                text=text,
                callback_data=f"duel_play:{match_id}:{value}:{original_value}",
            )
        )
        if len(row) == 5:
            hand_buttons.append(row)
            row = []
    if row:
        hand_buttons.append(row)

    action_buttons = []
    if boosts > 0:
        action_buttons.append(
            InlineKeyboardButton(
                text="⚡️ Усилить (1 ⭐)", callback_data=f"duel_boost:{match_id}"
            )
        )
    if replaces > 0:
        action_buttons.append(
            InlineKeyboardButton(
                text="🔄 Заменить (2 ⭐)", callback_data=f"duel_replace:{match_id}"
            )
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            *hand_buttons,
            action_buttons,
            [
                InlineKeyboardButton(
                    text="🏳️ Сдаться", callback_data=f"duel_surrender:{match_id}"
                )
            ],
        ]
    )


def duel_boost_choice_keyboard(
    hand: List[Union[int, tuple]], match_id: int
) -> InlineKeyboardMarkup:
    buttons = []
    for card in hand:
        original_value = card[1] if isinstance(card, tuple) else card
        buttons.append(
            InlineKeyboardButton(
                text=str(original_value),
                callback_data=f"duel_boost_choice:{match_id}:{original_value}",
            )
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            buttons,
            [
                InlineKeyboardButton(
                    text="❌ Отмена", callback_data=f"duel_cancel_action:{match_id}"
                )
            ],
        ]
    )


def duel_surrender_confirm_keyboard(match_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Да, сдаться",
                callback_data=f"duel_surrender_confirm:{match_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Нет, вернуться в бой",
                callback_data=f"duel_cancel_action:{match_id}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def duel_finish_keyboard(match_id: int, opponent_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🔄 Реванш", callback_data=f"duel_rematch:{match_id}:{opponent_id}"
            )
        ],
        [InlineKeyboardButton(text="⬅️ В меню дуэлей", callback_data="game_duel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_duels_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="game_duel")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def duel_stuck_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🏳️ Завершить зависшую игру", callback_data="duel_leave_active"
            )
        ],
        [InlineKeyboardButton(text="⬅️ В меню дуэлей", callback_data="game_duel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def timer_stake_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="1 ⭐", callback_data="timer_stake:1"),
            InlineKeyboardButton(text="3 ⭐", callback_data="timer_stake:3"),
            InlineKeyboardButton(text="5 ⭐", callback_data="timer_stake:5"),
        ],
        [
            InlineKeyboardButton(text="10 ⭐", callback_data="timer_stake:10"),
            InlineKeyboardButton(text="25 ⭐", callback_data="timer_stake:25"),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="entertainment")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def timer_searching_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="❌ Отменить поиск", callback_data="timer_cancel_search"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def timer_game_keyboard(match_id: int, stop_second: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"Остановить на {i}",
                callback_data=f"timer_stop:{match_id}:{i}",
            )
        ]
        for i in range(10)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def timer_finish_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="⬅️ В меню таймера", callback_data="game_timer")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def achievements_keyboard(
    all_achs: list, user_achs: list, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    buttons = []
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"ach_page_{page-1}")
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"ach_page_{page+1}")
        )
    buttons.append(nav_buttons)

    for ach_id, ach_name in all_achs:
        status = "✅" if ach_id in user_achs else "❌"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {ach_name}", callback_data=f"ach_info_{ach_id}"
                )
            ]
        )

    buttons.append(
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_achievements_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="⬅️ К списку", callback_data="achievements")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def coinflip_level_keyboard() -> InlineKeyboardMarkup:
    """Генерирует кнопки выбора уровня сложности для Coinflip."""
    buttons = []
    for level_id, level_data in COINFLIP_LEVELS.items():
        text = f"{level_data['name']} (x{level_data['prize_mult']:.1f}, {level_data['chance']}%)"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"cf_level:{level_id}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="entertainment")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def coinflip_stake_keyboard() -> InlineKeyboardMarkup:
    """Генерирует кнопки выбора ставки для Coinflip."""
    buttons = [
        [
            InlineKeyboardButton(text="1 ⭐", callback_data="cf_stake:1"),
            InlineKeyboardButton(text="3 ⭐", callback_data="cf_stake:3"),
            InlineKeyboardButton(text="5 ⭐", callback_data="cf_stake:5"),
        ],
        [
            InlineKeyboardButton(text="10 ⭐", callback_data="cf_stake:10"),
            InlineKeyboardButton(text="25 ⭐", callback_data="cf_stake:25"),
        ],
        [InlineKeyboardButton(text="⬅️ Выбрать другой уровень", callback_data="game_coinflip")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_games_keyboard() -> InlineKeyboardMarkup:
    """Кнопка для возврата в игровое меню."""
    buttons = [[InlineKeyboardButton(text="⬅️ Назад к развлечениям", callback_data="entertainment")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
