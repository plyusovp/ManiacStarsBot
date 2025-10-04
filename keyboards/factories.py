# keyboards/factories.py
from typing import Optional, Union

from aiogram.filters.callback_data import CallbackData


class MenuCallback(CallbackData, prefix="menu"):  # type: ignore
    """Фабрика для навигации по главному меню."""

    name: str
    action: Optional[str] = None


class GameCallback(CallbackData, prefix="game"):  # type: ignore
    """Фабрика для игровых меню."""

    name: str
    action: str


class UserCallback(CallbackData, prefix="user"):  # type: ignore
    """Фабрика для действий пользователя (промокоды, вывод)."""

    action: str
    value: Optional[Union[int, str]] = None


class CoinflipCallback(CallbackData, prefix="cf"):  # type: ignore
    """Фабрика для действий в игре 'Орёл и Решка'."""

    action: str
    value: Optional[int] = None
    choice: Optional[str] = None


class DuelCallback(CallbackData, prefix="duel"):  # type: ignore
    """Фабрика для всех действий в дуэлях."""

    action: str
    match_id: Optional[int] = None
    value: Optional[int] = None
    original_value: Optional[int] = None
    opponent_id: Optional[int] = None


class TimerCallback(CallbackData, prefix="timer"):  # type: ignore
    """Фабрика для всех действий в игре 'Таймер'."""

    action: str
    match_id: Optional[int] = None
    value: Optional[int] = None


class AdminCallback(CallbackData, prefix="admin"):  # type: ignore
    """Фабрика для всех действий в админ-панели."""

    action: str
    target_id: Optional[int] = None
    value: Optional[Union[int, str]] = None
    page: Optional[int] = None
    promo_code: Optional[str] = None  # Для управления конкретным промокодом


class AchievementCallback(CallbackData, prefix="ach"):  # type: ignore
    """Фабрика для меню достижений."""

    action: str
    ach_id: Optional[str] = None
    page: Optional[int] = None


class GiftCallback(CallbackData, prefix="gift"):  # type: ignore
    """Фабрика для каталога подарков."""

    action: str
    item_id: str
    cost: int


class SlotsCallback(CallbackData, prefix="slots"):  # type: ignore
    """Фабрика для действий в игре 'Слоты'."""

    action: str
    value: Optional[int] = None


class FootballCallback(CallbackData, prefix="football"):  # type: ignore
    """Фабрика для действий в игре 'Футбол'."""

    action: str
    # ИЗМЕНЯЕМ float НА int
    value: Optional[int] = None


class BowlingCallback(CallbackData, prefix="bowling"):  # type: ignore
    """Фабрика для действий в игре 'Боулинг'."""

    action: str
    value: Optional[int] = None  # ИЗМЕНЕНО: float -> int


class BasketballCallback(CallbackData, prefix="basketball"):  # type: ignore
    """Фабрика для действий в игре 'Баскетбол'."""

    action: str
    # ИЗМЕНЯЕМ float НА int
    value: Optional[int] = None


class DartsCallback(CallbackData, prefix="darts"):  # type: ignore
    """Фабрика для действий в игре 'Дартс'."""

    action: str
    # ИЗМЕНЯЕМ float НА int
    value: Optional[int] = None


class DiceCallback(CallbackData, prefix="dice"):  # type: ignore
    """Фабрика для действий в игре 'Кости'."""

    action: str
    choice: Optional[str] = None
    # ИЗМЕНЯЕМ float НА int
    value: Optional[int] = None