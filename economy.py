# economy.py
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
}

# --- COINFLIP GAME MATHEMATICS ---
# RTP = (chance / 100) * prize_mult * (1 - rake)
# Rake (commission) is applied to the winnings, not the stake.
COINFLIP_RAKE_PERCENT: int = 7

COINFLIP_LEVELS: Dict[str, Dict[str, Any]] = {
    "easy": {
        "name": "Лёгкий",
        "win_chance": 48,
        "prize_mult": 2.0,
        "stakes": [10, 20, 30, 40, 50],
        "rtp": (48 / 100) * 2.0 * (1 - COINFLIP_RAKE_PERCENT / 100),
    },
    "medium": {
        "name": "Средний",
        "win_chance": 35,
        "prize_mult": 2.5,
        "stakes": [25, 50, 75, 100, 150],
        "rtp": (35 / 100) * 2.5 * (1 - COINFLIP_RAKE_PERCENT / 100),
    },
    "hard": {
        "name": "Сложный",
        "win_chance": 20,
        "prize_mult": 4.0,
        "stakes": [50, 100, 150, 200, 250],
        "rtp": (20 / 100) * 4.0 * (1 - COINFLIP_RAKE_PERCENT / 100),
    },
    "insane": {
        "name": "Безумный",
        "win_chance": 10,
        "prize_mult": 8.0,
        "stakes": [100, 200, 300, 400, 500],
        "rtp": (10 / 100) * 8.0 * (1 - COINFLIP_RAKE_PERCENT / 100),
    },
}
