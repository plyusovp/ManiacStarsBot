# keyboards/inline.py
from typing import Optional, Union
from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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
    LanguageCallback,
    MenuCallback,
    SlotsCallback,
    TimerCallback,
    UserCallback,
)
from lexicon.languages import get_available_languages


def main_menu_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует новую клавиатуру главного меню."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💰 " + get_text("earn_button", language, default="Заработать"),
            callback_data=MenuCallback(name="earn_bread").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👾 " + get_text("games_button", language, default="Развлечения"),
            callback_data=MenuCallback(name="games").pack(),
        ),
        InlineKeyboardButton(
            text="💳 " + get_text("profile_button", language, default="Профиль"),
            callback_data=MenuCallback(name="profile").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🎁 " + get_text("gifts_button", language, default="Призы"),
            callback_data=MenuCallback(name="gifts").pack(),
        ),
        InlineKeyboardButton(
            text="🏆 " + get_text("leaders_button", language, default="Лидеры"),
            callback_data=MenuCallback(name="top_users").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🧑‍💻 "
            + get_text("resources_button", language, default="Наши ресурсы"),
            callback_data=MenuCallback(name="resources").pack(),
        ),
        InlineKeyboardButton(
            text="🏆 "
            + get_text("achievements_button", language, default="Достижения"),
            callback_data=MenuCallback(name="achievements").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⚙️ " + get_text("settings_button", language, default="Настройки"),
            callback_data=MenuCallback(name="settings").pack(),
        )
    )
    support_text = quote_plus("Здравствуйте, у меня проблема с ботом, дело в том что..")
    builder.row(
        InlineKeyboardButton(
            text="Техподдержка 12:00-21:00 🆘",
            url=f"{settings.URL_SUPPORT}?start={support_text}",
        )
    )
    return builder.as_markup()


def resources_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для раздела 'Наши ресурсы'."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("our_channel_button", language, default="Наш канал"),
            url=settings.URL_CHANNEL,
        ),
        InlineKeyboardButton(
            text=get_text("our_chat_button", language, default="Наш чат"),
            url=settings.URL_CHAT,
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("our_withdrawals_button", language, default="Наши выводы"),
            url=settings.URL_WITHDRAWALS,
        ),
        InlineKeyboardButton(
            text=get_text("our_manual_button", language, default="Наш мануал"),
            url=settings.URL_MANUAL,
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_menu", language),
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def games_menu_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру выбора игр."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    # Наши игры
    builder.row(
        InlineKeyboardButton(
            text="🃏 " + get_text("duels_button", language, default="Дуэли"),
            callback_data=GameCallback(name="duel", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="⏱️ " + get_text("timer_button", language, default="Таймер"),
            callback_data=GameCallback(name="timer", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="🪙 " + get_text("coinflip_button", language, default="Орёл/Решка"),
            callback_data=GameCallback(name="coinflip", action="start").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🎰 " + get_text("slots_button", language, default="Слоты"),
            callback_data=GameCallback(name="slots", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="⚽️ " + get_text("football_button", language, default="Футбол"),
            callback_data=GameCallback(name="football", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="🎳 " + get_text("bowling_button", language, default="Боулинг"),
            callback_data=GameCallback(name="bowling", action="start").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🏀 " + get_text("basketball_button", language, default="Баскетбол"),
            callback_data=GameCallback(name="basketball", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="🎯 " + get_text("darts_button", language, default="Дартс"),
            callback_data=GameCallback(name="darts", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="🎲 " + get_text("dice_button", language, default="Кости"),
            callback_data=GameCallback(name="dice", action="start").pack(),
        ),
    )
    # Игры-заглушки (теперь их нет)

    # Дополнительные кнопки
    builder.row(
        InlineKeyboardButton(
            text="📈 "
            + get_text("passive_income_button", language, default="Пассивный доход"),
            callback_data=MenuCallback(name="passive_income").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_menu", language),
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    # Управляем количеством кнопок в ряду для красивого отображения
    builder.adjust(3, 3, 3, 1, 1)

    return builder.as_markup()


# --- Profile & User Keyboards ---
def profile_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎁 "
            + get_text(
                "activate_promo_button", language, default="Активировать промокод"
            ),
            callback_data=UserCallback(action="enter_promo").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 "
            + get_text("my_transactions_button", language, default="Мои транзакции"),
            callback_data=UserCallback(action="transactions").pack(),
        ),
        InlineKeyboardButton(
            text="⚡ " + get_text("challenges_button", language, default="Челленджи"),
            callback_data=UserCallback(action="daily_challenges").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📱 "
            + get_text(
                "social_content_button", language, default="Контент для репостов"
            ),
            callback_data=UserCallback(action="social_content").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_menu", language),
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def back_to_profile_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка 'Назад в профиль'."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_profile", language),
            callback_data=MenuCallback(name="profile").pack(),
        )
    )
    return builder.as_markup()


def daily_challenges_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для ежедневных челленджей."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_profile", language),
            callback_data=MenuCallback(name="profile").pack(),
        )
    )
    return builder.as_markup()


def social_content_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для выбора платформы социального контента."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎵 " + get_text("tiktok_button", language, default="TikTok"),
            callback_data=UserCallback(action="tiktok_content").pack(),
        ),
        InlineKeyboardButton(
            text="📸 " + get_text("instagram_button", language, default="Instagram"),
            callback_data=UserCallback(action="instagram_content").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📱 " + get_text("telegram_button", language, default="Telegram"),
            callback_data=UserCallback(action="telegram_content").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_profile", language),
            callback_data=MenuCallback(name="profile").pack(),
        )
    )
    return builder.as_markup()


def back_to_menu_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Универсальная кнопка 'Назад в меню'."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_menu", language),
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def promo_back_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для возврата из ввода промокода."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_profile", language),
            callback_data=MenuCallback(name="profile").pack(),
        )
    )
    return builder.as_markup()


def top_users_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    return back_to_menu_keyboard(language)


def gifts_catalog_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру с каталогом подарков."""
    from lexicon.languages import get_text

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
            text="⬅️ " + get_text("back_to_menu", language),
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def gift_confirm_keyboard(
    item_id: str, cost: int, language: str = "ru"
) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения вывода подарка."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ " + get_text("confirm", language),
            callback_data=GiftCallback(
                action="confirm", item_id=item_id, cost=cost
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ " + get_text("cancel", language),
            callback_data=MenuCallback(name="gifts").pack(),
        )
    )
    return builder.as_markup()


# --- Duel Keyboards ---
def duel_stake_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

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
            text="🎓 " + get_text("training_button", language, default="Обучение"),
            callback_data=GameCallback(name="help", action="duel_tutorial").pack(),
        ),
        InlineKeyboardButton(
            text="📊 " + get_text("stats_button", language, default="Статистика"),
            callback_data=GameCallback(name="help", action="duel_stats").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_games", language, default="Назад"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()


def duel_searching_keyboard(stake: int, language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⏹️ "
            + get_text("cancel_search_button", language, default="Отменить поиск"),
            callback_data=DuelCallback(action="cancel_search", value=stake).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎓 "
            + get_text("how_to_play_button", language, default="Как играть?"),
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
    language: str = "ru",
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
    from lexicon.languages import get_text

    improvement_buttons = []
    if can_boost:
        improvement_buttons.append(
            InlineKeyboardButton(
                text=f"⚡ {get_text('boost_card_button', language, default='Усилить карту')} ({settings.DUEL_BOOST_COST} ⭐)",
                callback_data=DuelCallback(action="boost", match_id=match_id).pack(),
            )
        )
    if can_reroll:
        improvement_buttons.append(
            InlineKeyboardButton(
                text=f"🔄 {get_text('new_cards_button', language, default='Новые карты')} ({settings.DUEL_REROLL_COST} ⭐)",
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
            text="🏳️ " + get_text("surrender_button", language, default="Сдаться"),
            callback_data=DuelCallback(
                action="surrender", match_id=match_id, opponent_id=opponent_id
            ).pack(),
        )
    )
    return builder.as_markup()


def duel_boost_choice_keyboard(
    match_id: int, hand: list[int], language: str = "ru"
) -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{get_text('boost_card_button', language, default='Усилить')} {card}",
            callback_data=DuelCallback(
                action="boost_confirm", match_id=match_id, value=card
            ).pack(),
        )
        for card in hand
    ]
    builder.row(*buttons, width=3)
    builder.row(
        InlineKeyboardButton(
            text="❌ " + get_text("cancel", language),
            callback_data=DuelCallback(action="boost_cancel", match_id=match_id).pack(),
        )
    )
    return builder.as_markup()


def back_to_duels_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_games", language, default="Назад к дуэлям"),
            callback_data=GameCallback(name="duel", action="start").pack(),
        )
    )
    return builder.as_markup()


# --- Timer Keyboards ---
def timer_stake_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

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
            text="⬅️ " + get_text("back_to_games", language, default="Назад"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()


def timer_searching_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⏹️ "
            + get_text("cancel_search_button", language, default="Отменить поиск"),
            callback_data=TimerCallback(action="cancel_search").pack(),
        )
    )
    return builder.as_markup()


def timer_game_keyboard(match_id: int, language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🚨 " + get_text("stop_button", language, default="СТОП!") + " 🚨",
            callback_data=TimerCallback(action="stop", match_id=match_id).pack(),
        )
    )
    return builder.as_markup()


def timer_finish_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_games", language, default="Назад к играм"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()


# --- Coinflip Keyboards ---
def coinflip_stake_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

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
            text="⬅️ " + get_text("back_to_games", language, default="Назад"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()


def coinflip_choice_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("heads_button", language, default="Орёл"),
            callback_data=CoinflipCallback(action="choice", choice="орел").pack(),
        ),
        InlineKeyboardButton(
            text=get_text("tails_button", language, default="Решка"),
            callback_data=CoinflipCallback(action="choice", choice="решка").pack(),
        ),
    )
    return builder.as_markup()


def coinflip_continue_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎲 " + get_text("risk_button", language, default="Рискнуть!"),
            callback_data=CoinflipCallback(action="continue").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💰 "
            + get_text("cashout_button", language, default="Забрать выигрыш"),
            callback_data=CoinflipCallback(action="cashout").pack(),
        )
    )
    return builder.as_markup()


def coinflip_play_again_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎲 "
            + get_text("play_again_button", language, default="Играть снова"),
            callback_data=GameCallback(name="coinflip", action="start").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ "
            + get_text("to_other_games_button", language, default="К другим играм"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()


# --- Achievements Keyboards ---
def achievements_keyboard(
    all_achs: list, user_achs: set, page: int, total_pages: int, language: str = "ru"
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
    from lexicon.languages import get_text

    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_menu", language),
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )
    return builder.as_markup()


def back_to_achievements_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_menu", language, default="К списку"),
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
def slots_stake_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в слотах."""
    from lexicon.languages import get_text

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
            text="⬅️ "
            + get_text("to_other_games_button", language, default="К другим играм"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()

    # --- Football Keyboards ---


# ЭТОТ БЛОК НУЖНО ДОБАВИТЬ


def football_stake_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в футболе."""
    from lexicon.languages import get_text

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
            text="⬅️ "
            + get_text("to_other_games_button", language, default="К другим играм"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()


def bowling_stake_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в боулинге."""
    from lexicon.languages import get_text

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
            text="⬅️ "
            + get_text("to_other_games_button", language, default="К другим играм"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()


def bowling_play_again_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для боулинга с кнопкой 'Играть снова'."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎳 "
            + get_text("play_again_button", language, default="Играть снова"),
            callback_data=GameCallback(name="bowling", action="start").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ "
            + get_text("to_other_games_button", language, default="К другим играм"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()

    # --- Basketball Keyboards ---


# ЭТОТ БЛОК НУЖНО ДОБАВИТЬ


def basketball_stake_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в баскетболе."""
    from lexicon.languages import get_text

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
            text="⬅️ "
            + get_text("to_other_games_button", language, default="К другим играм"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()

    # --- Darts Keyboards ---


# ЭТОТ БЛОК НУЖНО ДОБАВИТЬ


def darts_stake_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в дартсе."""
    from lexicon.languages import get_text

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
            text="⬅️ "
            + get_text("to_other_games_button", language, default="К другим играм"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()


# ЭТОТ БЛОК НУЖНО ДОБАВИТЬ ПЕРЕД ФУНКЦИЕЙ ВЫШЕ


def dice_stake_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора ставки в костях."""
    from lexicon.languages import get_text

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
            text="⬅️ "
            + get_text("to_other_games_button", language, default="К другим играм"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()


# --- Language Selection Keyboards ---
def language_selection_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора языка."""
    builder = InlineKeyboardBuilder()
    languages = get_available_languages()

    buttons = []
    for lang_code, lang_name in languages.items():
        buttons.append(
            InlineKeyboardButton(
                text=lang_name,
                callback_data=LanguageCallback(
                    action="select", language=lang_code
                ).pack(),
            )
        )

    # Размещаем кнопки по 2 в ряд
    for i in range(0, len(buttons), 2):
        row_buttons = buttons[i : i + 2]
        builder.row(*row_buttons)

    return builder.as_markup()


def settings_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру настроек."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()

    # FAQ
    builder.row(
        InlineKeyboardButton(
            text="❓ " + get_text("faq_button", language, default="FAQ"),
            callback_data=MenuCallback(name="faq").pack(),
        )
    )

    # Пользовательское соглашение
    builder.row(
        InlineKeyboardButton(
            text="📋 "
            + get_text("terms_button", language, default="Пользовательское соглашение"),
            callback_data=MenuCallback(name="terms").pack(),
        )
    )

    # Настройки языка
    builder.row(
        InlineKeyboardButton(
            text="🌍 " + get_text("language_button", language, default="Язык"),
            callback_data=MenuCallback(name="language_settings").pack(),
        )
    )

    # Кнопка назад
    builder.row(
        InlineKeyboardButton(
            text="⬅️ " + get_text("back_to_menu", language),
            callback_data=MenuCallback(name="main_menu").pack(),
        )
    )

    return builder.as_markup()


def language_settings_keyboard(current_language: str) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру настроек языка."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()

    # Показываем текущий язык
    languages = get_available_languages()
    current_lang_name = languages.get(current_language, "🇷🇺 Русский")

    builder.row(
        InlineKeyboardButton(text=f"🌍 {current_lang_name}", callback_data="noop")
    )

    # Кнопка смены языка
    builder.row(
        InlineKeyboardButton(
            text="🔄 "
            + get_text("change_language", current_language, default="Сменить язык"),
            callback_data=LanguageCallback(action="change").pack(),
        )
    )

    # Кнопка назад в настройки
    builder.row(
        InlineKeyboardButton(
            text="⬅️ "
            + get_text(
                "back_to_settings", current_language, default="Назад в настройки"
            ),
            callback_data=MenuCallback(name="settings").pack(),
        )
    )

    return builder.as_markup()


def faq_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для FAQ."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()

    # Кнопка назад в настройки
    builder.row(
        InlineKeyboardButton(
            text="⬅️ "
            + get_text("back_to_settings", language, default="Назад в настройки"),
            callback_data=MenuCallback(name="settings").pack(),
        )
    )

    return builder.as_markup()


def terms_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для пользовательского соглашения."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()

    # Кнопка назад в настройки
    builder.row(
        InlineKeyboardButton(
            text="⬅️ "
            + get_text("back_to_settings", language, default="Назад в настройки"),
            callback_data=MenuCallback(name="settings").pack(),
        )
    )

    return builder.as_markup()


# --- Dice Keyboards ---
def dice_range_choice_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для игры в кости с выбором диапазона."""
    from lexicon.languages import get_text

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎲 "
            + get_text("bet_low_button", language, default="Поставить на 1-3"),
            callback_data=DiceCallback(action="choice", choice="low").pack(),
        ),
        InlineKeyboardButton(
            text="🎲 "
            + get_text("bet_high_button", language, default="Поставить на 4-6"),
            callback_data=DiceCallback(action="choice", choice="high").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ "
            + get_text("to_other_games_button", language, default="К другим играм"),
            callback_data=MenuCallback(name="games").pack(),
        )
    )
    return builder.as_markup()
