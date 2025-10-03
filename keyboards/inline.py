# keyboards/inline.py
from typing import Optional, Union
from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (
    BASKETBALL_STAKES,
    BOWLING_STAKES,
    COINFLIP_STAKES,
    DARTS_STAKES,
    DICE_STAKES,
    DUEL_STAKES,
    FOOTBALL_STAKES,
    SLOTS_STAKES,
    TIMER_STAKES,
    settings,
)
from gifts import GIFTS_CATALOG
from keyboards.factories import (
    AchievementCallback,
    AdminCallback,
    BasketballCallback,
    BowlingCallback,
    CoinflipCallback,
    DartsCallback,
    DiceCallback,
    DuelCallback,
    FootballCallback,
    GameCallback,
    GiftCallback,
    MenuCallback,
    SlotsCallback,
    TimerCallback,
    UserCallback,
)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Генерирует новую клавиатуру главного меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💰 Заработать",
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
            text="🎁 Призы", callback_data=MenuCallback(name="gifts").pack()
        ),
        InlineKeyboardButton(
            text="🏆 Лидеры",
            callback_data=MenuCallback(name="top_users").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🧑‍💻 Наши ресурсы",
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
    # Наши игры
    builder.row(
        InlineKeyboardButton(
            text="🃏 Дуэли",
            callback_data=GameCallback(name="duel", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="⏱️ Таймер",
            callback_data=GameCallback(name="timer", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="🪙Орёл/Решка",
            callback_data=GameCallback(name="coinflip", action="start").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🎰 Слоты",
            callback_data=GameCallback(name="slots", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="⚽️ Футбол",
            callback_data=GameCallback(name="football", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="🎳 Боулинг",
            callback_data=GameCallback(name="bowling", action="start").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🏀 Баскетбол",
            callback_data=GameCallback(name="basketball", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="🎯 Дартс",
            callback_data=GameCallback(name="darts", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="🎲 Кости",
            callback_data=GameCallback(name="dice", action="start").pack(),
        ),
    )
    # Игры-заглушки (теперь их нет)

    # WebApp игра
    builder.row(
        InlineKeyboardButton(
            text="🎮 Maniac Clic Game", web_app=WebAppInfo(url=settings.URL_WEBAPP_GAME)
        )
    )
    # Дополнительные кнопки
    builder.row(
        InlineKeyboardButton(
            text="📈 Пассивный доход",
            callback_data=MenuCallback(name="passive_income").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💰 Получить ежедневный бонус",
            callback_data=MenuCallback(name="get_daily_bonus").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    # Управляем количеством кнопок в ряду для красивого отображения
    builder.adjust(3, 3, 3, 1, 1, 1)

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
            text="📊 Мои транзакции",
            callback_data=UserCallback(action="transactions").pack(),
        ),
        InlineKeyboardButton(
            text="⚡ Челленджи",
            callback_data=UserCallback(action="daily_challenges").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📱 Контент для репостов",
            callback_data=UserCallback(action="social_content").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def back_to_profile_keyboard() -> InlineKeyboardMarkup:
    """Кнопка 'Назад в профиль'."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в профиль",
            callback_data=MenuCallback(name="profile").pack(),
        )
    )
    return builder.as_markup()


def daily_challenges_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ежедневных челленджей."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в профиль",
            callback_data=MenuCallback(name="profile").pack(),
        )
    )
    return builder.as_markup()


def social_content_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора платформы социального контента."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎵 TikTok",
            callback_data=UserCallback(action="tiktok_content").pack(),
        ),
        InlineKeyboardButton(
            text="📸 Instagram",
            callback_data=UserCallback(action="instagram_content").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📱 Telegram",
            callback_data=UserCallback(action="telegram_content").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в профиль",
            callback_data=MenuCallback(name="profile").pack(),
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
    return back_to_menu_keyboard()


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
    builder.adjust(2)
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
    builder = InlineKeyboardBuilder()
    stake_emojis = ["🪙", "💰", "🔥", "⭐", "💎"]

    buttons = []
    for i, stake in enumerate(DUEL_STAKES):
        emoji = stake_emojis[i] if i < len(stake_emojis) else "💰"
        buttons.append(
            InlineKeyboardButton(
                text=f"{emoji} {stake} ⭐",
                callback_data=DuelCallback(action="stake", value=stake).pack(),
            )
        )

    builder.row(*buttons, width=3)
    builder.row(
        InlineKeyboardButton(
            text="🎓 Обучение",
            callback_data=GameCallback(name="help", action="duel_tutorial").pack(),
        ),
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data=GameCallback(name="help", action="duel_stats").pack(),
        ),
    )
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
            text="⏹️ Отменить поиск",
            callback_data=DuelCallback(action="cancel_search", value=stake).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎓 Как играть?",
            callback_data=GameCallback(name="help", action="duel_tutorial").pack(),
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
    # Создаем красивые кнопки для карт с эмодзи
    card_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    card_buttons = []

    for card in sorted(hand):
        emoji = card_emojis[card - 1] if card <= 10 else f"{card}"
        card_buttons.append(
            InlineKeyboardButton(
                text=f"🃏 {emoji}",
                callback_data=DuelCallback(
                    action="play", match_id=match_id, value=card
                ).pack(),
            )
        )
    builder.row(*card_buttons, width=len(hand) or 1)
    # Кнопки улучшений
    improvement_buttons = []
    if can_boost:
        improvement_buttons.append(
            InlineKeyboardButton(
                text=f"⚡ Усилить карту ({settings.DUEL_BOOST_COST} ⭐)",
                callback_data=DuelCallback(action="boost", match_id=match_id).pack(),
            )
        )
    if can_reroll:
        improvement_buttons.append(
            InlineKeyboardButton(
                text=f"🔄 Новые карты ({settings.DUEL_REROLL_COST} ⭐)",
                callback_data=DuelCallback(action="reroll", match_id=match_id).pack(),
            )
        )

    if improvement_buttons:
        if len(improvement_buttons) == 2:
            builder.row(*improvement_buttons)
        else:
            builder.row(improvement_buttons[0])

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
    stake_emojis = ["⏱️", "⚡", "🔥", "🎆", "💎"]

    buttons = []
    for i, stake in enumerate(TIMER_STAKES):
        emoji = stake_emojis[i] if i < len(stake_emojis) else "⏱️"
        buttons.append(
            InlineKeyboardButton(
                text=f"{emoji} {stake} ⭐",
                callback_data=TimerCallback(action="stake", value=stake).pack(),
            )
        )

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
            text="⏹️ Отменить поиск",
            callback_data=TimerCallback(action="cancel_search").pack(),
        )
    )
    return builder.as_markup()


def timer_game_keyboard(match_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🚨 СТОП! 🚨",
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


def coinflip_choice_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Орёл",
            callback_data=CoinflipCallback(action="choice", choice="орел").pack(),
        ),
        InlineKeyboardButton(
            text="Решка",
            callback_data=CoinflipCallback(action="choice", choice="решка").pack(),
        ),
    )
    return builder.as_markup()


def coinflip_continue_keyboard() -> InlineKeyboardMarkup:
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
    promo_code: Optional[str] = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=AdminCallback(
                action=f"{action}_confirm",
                target_id=target_id,
                value=str(value),
                promo_code=promo_code,
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
        ),
        InlineKeyboardButton(
            text="📋 Список промокодов",
            callback_data=AdminCallback(action="promo_list", page=1).pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data=AdminCallback(action="main_panel").pack()
        )
    )
    return builder.as_markup()


def admin_promos_list_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav_row = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=AdminCallback(action="promo_list", page=page - 1).pack(),
            )
        )
    if page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=AdminCallback(action="promo_list", page=page + 1).pack(),
            )
        )
    if nav_row:
        builder.row(*nav_row)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К промокодам",
            callback_data=AdminCallback(action="promos").pack(),
        )
    )
    return builder.as_markup()


def admin_promo_manage_keyboard(code: str, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_active:
        builder.row(
            InlineKeyboardButton(
                text="🚫 Деактивировать",
                callback_data=AdminCallback(
                    action="promo_deactivate", promo_code=code
                ).pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить активаций",
            callback_data=AdminCallback(
                action="promo_add_uses", promo_code=code
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К списку",
            callback_data=AdminCallback(action="promo_list", page=1).pack(),
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


# --- Slots Keyboards ---
def slots_stake_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в слотах."""
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{stake} ⭐",
            callback_data=SlotsCallback(action="spin", value=stake).pack(),
        )
        for stake in SLOTS_STAKES
    ]
    builder.row(*buttons, width=4)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К другим играм", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()

    # --- Football Keyboards ---


# ЭТОТ БЛОК НУЖНО ДОБАВИТЬ


def football_stake_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в футболе."""
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{stake} ⭐",
            callback_data=FootballCallback(action="kick", value=stake).pack(),
        )
        for stake in FOOTBALL_STAKES
    ]
    # Создаем ряд из кнопок со ставками, по 4 в ряд
    builder.row(*buttons, width=4)
    # Добавляем кнопку "Назад"
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К другим играм", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()


def bowling_stake_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в боулинге."""
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{stake} ⭐",
            callback_data=BowlingCallback(action="throw", value=stake).pack(),
        )
        for stake in BOWLING_STAKES
    ]
    builder.row(*buttons, width=4)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К другим играм", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()


def bowling_play_again_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для боулинга с кнопкой 'Играть снова'."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎳 Играть снова",
            callback_data=GameCallback(name="bowling", action="start").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К другим играм", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()

    # --- Basketball Keyboards ---


# ЭТОТ БЛОК НУЖНО ДОБАВИТЬ


def basketball_stake_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в баскетболе."""
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{stake} ⭐",
            callback_data=BasketballCallback(action="throw", value=stake).pack(),
        )
        for stake in BASKETBALL_STAKES
    ]
    builder.row(*buttons, width=4)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К другим игам", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()

    # --- Darts Keyboards ---


# ЭТОТ БЛОК НУЖНО ДОБАВИТЬ


def darts_stake_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в дартсе."""
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{stake} ⭐",
            callback_data=DartsCallback(action="throw", value=stake).pack(),
        )
        for stake in DARTS_STAKES
    ]
    builder.row(*buttons, width=4)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К другим играм", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()


# ЭТОТ БЛОК НУЖНО ДОБАВИТЬ ПЕРЕД ФУНКЦИЕЙ ВЫШЕ


def dice_stake_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в костях."""
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{stake} ⭐",
            callback_data=DiceCallback(action="stake", value=stake).pack(),
        )
        for stake in DICE_STAKES
    ]
    builder.row(*buttons, width=4)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К другим играм", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()


# --- Dice Keyboards ---
def dice_range_choice_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для игры в кости с выбором диапазона."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎲 Поставить на 1-3",
            callback_data=DiceCallback(action="choice", choice="low").pack(),
        ),
        InlineKeyboardButton(
            text="🎲 Поставить на 4-6",
            callback_data=DiceCallback(action="choice", choice="high").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К другим играм", callback_data=MenuCallback(name="games").pack()
        )
    )
    return builder.as_markup()
