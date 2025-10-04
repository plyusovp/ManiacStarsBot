# gifts.py
# Этот файл содержит каталог доступных подарков для вывода.
# Каждый подарок - это словарь с его свойствами.

from typing import Any, Dict, List

GIFTS_CATALOG: List[Dict[str, Any]] = [
    {"id": "heart_bow", "emoji": "💖", "name": "Сердце", "cost": 15},
    {"id": "teddy_bear", "emoji": "🧸", "name": "Мишка", "cost": 15},
    {"id": "present", "emoji": "🎁", "name": "Подарок", "cost": 25},
    {"id": "rose", "emoji": "🌹", "name": "Роза", "cost": 25},
    {"id": "cake", "emoji": "🎂", "name": "Торт", "cost": 50},
    {"id": "bouquet", "emoji": "💐", "name": "Букет", "cost": 50},
    {"id": "rocket", "emoji": "🚀", "name": "Ракета", "cost": 50},
    {"id": "champagne", "emoji": "🍾", "name": "Шампанское", "cost": 50},
    {"id": "trophy", "emoji": "🏆", "name": "Трофей", "cost": 100},
    {"id": "ring", "emoji": "💍", "name": "Кольцо", "cost": 100},
    {"id": "diamond", "emoji": "💎", "name": "Бриллиант", "cost": 100},
]
