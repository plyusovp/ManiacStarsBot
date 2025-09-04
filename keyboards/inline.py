# keyboards/inline.py
from typing import Optional, Union

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import COINFLIP_LEVELS, DUEL_STAKES, TIMER_STAKES, settings
from keyboards.factories import (
    AchievementCallback,
    AdminCallback,
    CoinflipCallback,
    DuelCallback,
    GameCallback,
    MenuCallback,
    TimerCallback,
    UserCallback,
)


def main_menu_keyboard(back_only: bool = False) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру главного меню."""
    builder = InlineKeyboardBuilder()
    if back_only:
        builder.row(
            InlineKeyboardButton(
                text="⬅️ Назад в меню",
                callback_data=MenuCallback(name="main_menu").pack(),
            )
        )
        return builder.as_markup()

    builder.row(
        InlineKeyboardButton(
            text="🎮 Игры", callback_data=MenuCallback(name="games").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👤 Профиль", callback_data=MenuCallback(name="profile").pack()
        ),
        InlineKeyboardButton(
            text="🎁 Подарки", callback_data=MenuCallback(name="gifts").pack()
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🙋‍♂️ Рефералы", callback_data=MenuCallback(name="referrals").pack()
        ),
        InlineKeyboardButton(
            text="🏆 Топ игроков",
            callback_data=MenuCallback(name="top_users").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📜 Правила", url="https://telegra.ph/pravila-bota-08-11"
        ),
        InlineKeyboardButton(
            text="✨ Достижения", callback_data=MenuCallback(name="achievements").pack()
        ),
    )
    return builder.as_markup()


def games_menu_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру выбора игр."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🃏 Дуэли",
            callback_data=GameCallback(name="duel", action="start").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⏱️ Звёздный таймер",
            callback_data=GameCallback(name="timer", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="🪙 Орёл и Решка",
            callback_data=GameCallback(name="coinflip", action="start").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


# --- Profile & User Keyboards ---
def profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎁 Активировать промокод",
            callback_data=UserCallback(action="enter_promo").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def promo_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для возврата из ввода промокода/вывода."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuCallback(name="profile").pack()
        )
    )
    return builder.as_markup()


def referral_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def top_users_keyboard() -> InlineKeyboardMarkup:
    return referral_keyboard()  # Same as referral


def gifts_keyboard(
    can_withdraw: bool, confirm_mode: bool = False
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if confirm_mode:
        builder.row(
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=UserCallback(action="confirm_withdraw").pack(),
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отмена", callback_data=MenuCallback(name="gifts").pack()
            )
        )
    else:
        if can_withdraw:
            builder.row(
                InlineKeyboardButton(
                    text="💸 Подать заявку",
                    callback_data=UserCallback(action="withdraw").pack(),
                )
            )
        builder.row(
            InlineKeyboardButton(
                text="⬅️ Назад в меню",
                callback_data=MenuCallback(name="main_menu").pack(),
            )
        )
    return builder.as_markup()


# --- Duel Keyboards ---
def duel_stake_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора ставки для дуэли."""
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{stake} ⭐",
            callback_data=DuelCallback(action="stake", value=stake).pack(),
        )
        for stake in DUEL_STAKES
    ]
    builder.row(*buttons, width=3)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()


def duel_searching_keyboard(stake: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить поиск",
            callback_data=DuelCallback(action="cancel_search", value=stake).pack(),
        )
    )
    return builder.as_markup()


def duel_game_keyboard(
    match_id: int,
    hand: list[int],
    opponent_id: int,
    can_boost: bool,
    can_reroll: bool,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    card_buttons = [
        InlineKeyboardButton(
            text=f"Карта {card}",
            callback_data=DuelCallback(
                action="play", match_id=match_id, value=card
            ).pack(),
        )
        for card in hand
    ]
    builder.row(*card_buttons, width=len(hand) or 1)
    if can_boost:
        builder.row(
            InlineKeyboardButton(
                text=f"💥 Усилить карту ({settings.DUEL_BOOST_COST} ⭐)",
                callback_data=DuelCallback(action="boost", match_id=match_id).pack(),
            )
        )
    if can_reroll:
        builder.row(
            InlineKeyboardButton(
                text=f"♻️ Новая рука ({settings.DUEL_REROLL_COST} ⭐)",
                callback_data=DuelCallback(action="reroll", match_id=match_id).pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="🏳️ Сдаться",
            callback_data=DuelCallback(
                action="surrender", match_id=match_id, opponent_id=opponent_id
            ).pack(),
        )
    )
    return builder.as_markup()


def duel_boost_choice_keyboard(match_id: int, hand: list[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"Усилить {card}",
            callback_data=DuelCallback(
                action="boost_confirm", match_id=match_id, value=card
            ).pack(),
        )
        for card in hand
    ]
    builder.row(*buttons, width=3)
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=DuelCallback(action="boost_cancel", match_id=match_id).pack(),
        )
    )
    return builder.as_markup()


def back_to_duels_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для возврата в меню дуэлей после игры/отмены."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="⬅️ Назад к дуэлям",
            callback_data=GameCallback(name="duel", action="start").pack(),
        )
    )
    return builder.as_markup()


# --- Timer Keyboards ---
def timer_stake_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{stake} ⭐",
            callback_data=TimerCallback(action="stake", value=stake).pack(),
        )
        for stake in TIMER_STAKES
    ]
    builder.row(*buttons, width=3)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()


def timer_searching_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить поиск",
            callback_data=TimerCallback(action="cancel_search").pack(),
        )
    )
    return builder.as_markup()


def timer_game_keyboard(match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛑 СТОП",
            callback_data=TimerCallback(action="stop", match_id=match_id).pack(),
        )
    )
    return builder.as_markup()


def timer_finish_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад к играм", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()


# --- Coinflip Keyboards ---
def coinflip_level_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for level_id, level_data in COINFLIP_LEVELS.items():
        builder.row(
            InlineKeyboardButton(
                text=f"{level_data['name']} ({level_data['win_chance']}%)",
                callback_data=CoinflipCallback(
                    action="select_level", value=level_id
                ).pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()


def coinflip_stake_keyboard(level_id: str) -> InlineKeyboardMarkup:
    level = COINFLIP_LEVELS.get(level_id)
    if not level:
        return InlineKeyboardMarkup(inline_keyboard=[])
    builder = InlineKeyboardBuilder()
    stakes = [
        InlineKeyboardButton(
            text=f"{stake} ⭐",
            callback_data=CoinflipCallback(action="select_stake", value=stake).pack(),
        )
        for stake in level["stakes"]
    ]
    builder.row(*stakes, width=3)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=GameCallback(name="coinflip", action="start").pack(),
        )
    )
    return builder.as_markup()


def coinflip_play_again_keyboard(level_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎲 Играть снова",
            callback_data=CoinflipCallback(
                action="select_level", value=level_id
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К выбору сложности",
            callback_data=GameCallback(name="coinflip", action="start").pack(),
        )
    )
    return builder.as_markup()


# --- Achievements Keyboards ---
def achievements_keyboard(
    all_achs: list, user_achs: set, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Pagination
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=AchievementCallback(action="page", page=page - 1).pack(),
            )
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=AchievementCallback(action="page", page=page + 1).pack(),
            )
        )
    if nav_buttons:
        builder.row(*nav_buttons)

    # Achievements list
    for ach in all_achs:
        ach_id, ach_name = ach["id"], ach["name"]
        status = "✅" if ach_id in user_achs else "❌"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {ach_name}",
                callback_data=AchievementCallback(action="info", ach_id=ach_id).pack(),
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def back_to_achievements_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К списку",
            callback_data=MenuCallback(name="achievements").pack(),
        )
    )
    return builder.as_markup()


# --- Admin Keyboards ---
def admin_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📢 Рассылка", callback_data=AdminCallback(action="broadcast").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 Статистика", callback_data=AdminCallback(action="stats").pack()
        ),
        InlineKeyboardButton(
            text="💸 Заявки на вывод",
            callback_data=AdminCallback(action="rewards_list", page=1).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="ℹ️ Инфо о юзере",
            callback_data=AdminCallback(action="user_info_prompt").pack(),
        ),
        InlineKeyboardButton(
            text="🎁 Промокоды", callback_data=AdminCallback(action="promos").pack()
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🛠️ Управление", callback_data=AdminCallback(action="manage").pack()
        )
    )
    return builder.as_markup()


def admin_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в админку",
            callback_data=AdminCallback(action="main_panel").pack(),
        )
    )
    return builder.as_markup()


def admin_confirm_keyboard(
    action: str,
    target_id: Optional[int] = None,
    value: Optional[Union[int, str]] = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=AdminCallback(
                action=f"{action}_confirm", target_id=target_id, value=value
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=AdminCallback(action="main_panel").pack(),
        )
    )
    return builder.as_markup()


def admin_rewards_menu(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav_row = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=AdminCallback(
                    action="rewards_list", page=page - 1
                ).pack(),
            )
        )
    if page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=AdminCallback(
                    action="rewards_list", page=page + 1
                ).pack(),
            )
        )
    if nav_row:
        builder.row(*nav_row)

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в админку",
            callback_data=AdminCallback(action="main_panel").pack(),
        )
    )
    return builder.as_markup()


def admin_reward_details_menu(reward_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=AdminCallback(
                action="reward_approve", target_id=reward_id
            ).pack(),
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=AdminCallback(
                action="reward_reject", target_id=reward_id
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🎉 Выполнено",
            callback_data=AdminCallback(
                action="reward_fulfill", target_id=reward_id
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="ℹ️ Инфо о юзере",
            callback_data=AdminCallback(action="user_info", target_id=user_id).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К списку",
            callback_data=AdminCallback(action="rewards_list", page=1).pack(),
        )
    )
    return builder.as_markup()


def admin_promos_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Создать промокод",
            callback_data=AdminCallback(action="promo_create").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=AdminCallback(action="main_panel").pack()
        )
    )
    return builder.as_markup()


def admin_user_info_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=AdminCallback(action="main_panel").pack()
        )
    )
    return builder.as_markup()


def admin_manage_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💰 Начислить баланс",
            callback_data=AdminCallback(action="grant").pack(),
        ),
        InlineKeyboardButton(
            text="💸 Списать баланс",
            callback_data=AdminCallback(action="debit").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔄 Сбросить состояние (FSM)",
            callback_data=AdminCallback(action="reset_fsm").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=AdminCallback(action="main_panel").pack()
        )
    )
    return builder.as_markup()
