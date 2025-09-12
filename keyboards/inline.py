# keyboards/inline.py
from typing import Optional, Union
from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import COINFLIP_STAKES, DUEL_STAKES, TIMER_STAKES, settings
from gifts import GIFTS_CATALOG
from keyboards.factories import (
    AchievementCallback,
    AdminCallback,
    CoinflipCallback,
    DuelCallback,
    GameCallback,
    GiftCallback,
    MenuCallback,
    TimerCallback,
    UserCallback,
)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Генерирует новую клавиатуру главного меню."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🌟 Заработать на хлеб 🌟",
            callback_data=MenuCallback(name="earn_bread").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👾 Развлечения", callback_data=MenuCallback(name="games").pack()
        ),
        InlineKeyboardButton(
            text="💳 Профиль", callback_data=MenuCallback(name="profile").pack()
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="💸 Вывод", callback_data=MenuCallback(name="gifts").pack()
        ),
        InlineKeyboardButton(
            text="📈 Топ игроков",
            callback_data=MenuCallback(name="top_users").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🎁 Наши ресурсы",
            callback_data=MenuCallback(name="resources").pack(),
        ),
        InlineKeyboardButton(
            text="🏆 Достижения",
            callback_data=MenuCallback(name="achievements").pack(),
        ),
    )
    support_text = quote_plus("Здравствуйте, у меня проблема с ботом, дело в том что..")
    builder.row(
        InlineKeyboardButton(
            text="Техподдержка 12:00-21:00 🆘",
            url=f"{settings.URL_SUPPORT}?start={support_text}",
        )
    )

    return builder.as_markup()


def resources_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для раздела 'Наши ресурсы'."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Наш канал", url=settings.URL_CHANNEL),
        InlineKeyboardButton(text="Наш чат", url=settings.URL_CHAT),
    )
    builder.row(
        InlineKeyboardButton(text="Наши выводы", url=settings.URL_WITHDRAWALS),
        InlineKeyboardButton(text="Наш мануал", url=settings.URL_MANUAL),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data=MenuCallback(name="main_menu").pack(),
        )
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


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Универсальная кнопка 'Назад в меню'."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def promo_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для возврата из ввода промокода."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuCallback(name="profile").pack()
        )
    )
    return builder.as_markup()


def top_users_keyboard() -> InlineKeyboardMarkup:
    return back_to_menu_keyboard()  # Use the generic back keyboard


def gifts_catalog_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру с каталогом подарков."""
    builder = InlineKeyboardBuilder()
    for gift in GIFTS_CATALOG:
        builder.add(
            InlineKeyboardButton(
                text=f"{gift['emoji']} - {gift['cost']} ⭐",
                callback_data=GiftCallback(
                    action="select", item_id=gift["id"], cost=gift["cost"]
                ).pack(),
            )
        )
    builder.adjust(2)  # По 2 подарка в ряду
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def gift_confirm_keyboard(item_id: str, cost: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения вывода подарка."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=GiftCallback(
                action="confirm", item_id=item_id, cost=cost
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена", callback_data=MenuCallback(name="gifts").pack()
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
            text=f"{card}",
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
                text=f"💥 Усилить ({settings.DUEL_BOOST_COST} ⭐)",
                callback_data=DuelCallback(action="boost", match_id=match_id).pack(),
            )
        )
    if can_reroll:
        builder.row(
            InlineKeyboardButton(
                text=f"♻️ Сменить карты ({settings.DUEL_REROLL_COST} ⭐)",
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
def coinflip_stake_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора ставки для 'Орла и решки'."""
    builder = InlineKeyboardBuilder()
    stakes = [
        InlineKeyboardButton(
            text=f"{stake} ⭐",
            callback_data=CoinflipCallback(action="stake", value=stake).pack(),
        )
        for stake in COINFLIP_STAKES
    ]
    builder.row(*stakes, width=3)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()


def coinflip_continue_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с выбором: продолжить игру или забрать выигрыш."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎲 Рискнуть!",
            callback_data=CoinflipCallback(action="continue").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💰 Забрать выигрыш",
            callback_data=CoinflipCallback(action="cashout").pack(),
        )
    )
    return builder.as_markup()


def coinflip_play_again_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после окончания игры."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎲 Играть снова",
            callback_data=GameCallback(name="coinflip", action="start").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К другим играм", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()


# --- Achievements Keyboards ---
def achievements_keyboard(
    all_achs: list, user_achs: set, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ach in all_achs:
        ach_id, ach_name = ach["id"], ach["name"]
        status = "✅" if ach_id in user_achs else "❌"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {ach_name}",
                callback_data=AchievementCallback(action="info", ach_id=ach_id).pack(),
            )
        )

    # Pagination
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=AchievementCallback(action="page", page=page - 1).pack(),
            )
        )
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop")
    )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=AchievementCallback(action="page", page=page + 1).pack(),
            )
        )
    if len(nav_buttons) > 1:
        builder.row(*nav_buttons)

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


def admin_back_keyboard(
    action: str = "main_panel",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в админку",
            callback_data=AdminCallback(action=action).pack(),
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
                action=f"{action}_confirm", target_id=target_id, value=str(value)
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
            text="⬅️ Назад",
            callback_data=AdminCallback(action="user_info_prompt").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ В админ-панель",
            callback_data=AdminCallback(action="main_panel").pack(),
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


def admin_grant_target_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Рабам",
            callback_data=AdminCallback(action="grant_target", name="user").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Админам",
            callback_data=AdminCallback(action="grant_target", name="admin").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=AdminCallback(action="manage").pack()
        )
    )
    return builder.as_markup()


def admin_grant_admin_select_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Марк",
            callback_data=AdminCallback(
                action="grant_admin_select", target_id=settings.MARK_ID
            ).pack(),
        ),
        InlineKeyboardButton(
            text="Максим",
            callback_data=AdminCallback(
                action="grant_admin_select", target_id=settings.MAXIM_ID
            ).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=AdminCallback(action="grant").pack()
        )
    )
    return builder.as_markup()
