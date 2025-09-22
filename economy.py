# plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/economy.py

from typing import Any, Dict

# --- GENERAL ECONOMIC RULES ---
NEW_USER_QUARANTINE_HOURS: int = 24
WITHDRAW_COOLDOWN_HOURS: int = 12
BIG_EARN_THRESHOLD: int = 50

# --- RULES FOR EARNINGS (add_balance_with_checks) ---
# Keys: source (reason)
# Values: dictionary with limits
# daily_cap: max amount per day
# rpm: max operations per minute
# rph: max operations per hour
# unlimited: True if there are no limits
EARN_RULES: Dict[str, Dict[str, Any]] = {
    "referral_bonus": {"daily_cap": 50},
    "promo_activation": {"unlimited": True},
    "daily_bonus": {"daily_cap": 10},
    "achievement_reward": {"unlimited": True},
    "duel_win": {"unlimited": True},
    "timer_win": {"unlimited": True},
    "coinflip_win": {"unlimited": True},
    "compensation": {"unlimited": True},
    "admin_grant": {"unlimited": True},
    "duel_draw_refund": {"unlimited": True},
    "duel_creation_refund": {"unlimited": True},
    "duel_boost_refund": {"unlimited": True},
    "timer_draw_refund": {"unlimited": True},
    "reward_revert": {"unlimited": True},
    "initial_balance": {"unlimited": True},
}

# --- COINFLIP GAME MATHEMATICS ---
# Новая логика "Рискни и умножь"
# chance: шанс на победу на данном шаге (в процентах)
# multiplier: множитель выигрыша от *первоначальной* ставки на данном шаге
COINFLIP_RAKE_PERCENT: int = 7
COINFLIP_STAGES = [
    {"chance": 50, "multiplier": 2.0},  # 1-й бросок
    {"chance": 40, "multiplier": 3.0},  # 2-й бросок
    {"chance": 30, "multiplier": 5.0},  # 3-й бросок
    {"chance": 20, "multiplier": 8.0},  # 4-й бросок
    {"chance": 10, "multiplier": 15.0},  # 5-й бросок
]
