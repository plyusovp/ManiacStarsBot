# economy.py
from config import settings

# --- ОБЩИЕ ПРАВИЛА ЭКОНОМИКИ ---
NEW_USER_QUARANTINE_HOURS = 24
WITHDRAW_COOLDOWN_HOURS = 12
BIG_EARN_THRESHOLD = 50

# --- ПРАВИЛА ДЛЯ НАЧИСЛЕНИЙ (add_balance_with_checks) ---
# Ключи: источник (reason)
# Значения: словарь с лимитами
# daily_cap: макс. сумма в день
# rpm: макс. операций в минуту
# rph: макс. операций в час
# unlimited: True, если лимитов нет
EARN_RULES = {
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

# --- МАТЕМАТИКА ИГРЫ COINFLIP (ОРЁЛ И РЕШКА) ---
# RTP = (chance / 100) * prize_mult * (1 - rake)
# Rake (комиссия) применяется к выигрышу, а не к ставке.
COINFLIP_RAKE_PERCENT = 7

COINFLIP_LEVELS = {
    "easy": {
        "name": "Лёгкий",
        "chance": 48,  # %
        "prize_mult": 2.0,
        "rtp": (48 / 100) * 2.0 * (1 - COINFLIP_RAKE_PERCENT / 100),
    },
    "medium": {
        "name": "Средний",
        "chance": 35,  # %
        "prize_mult": 2.5,
        "rtp": (35 / 100) * 2.5 * (1 - COINFLIP_RAKE_PERCENT / 100),
    },
    "hard": {
        "name": "Сложный",
        "chance": 20,  # %
        "prize_mult": 4.0,
        "rtp": (20 / 100) * 4.0 * (1 - COINFLIP_RAKE_PERCENT / 100),
    },
    "insane": {
        "name": "Безумный",
        "chance": 10,  # %
        "prize_mult": 8.0,
        "rtp": (10 / 100) * 8.0 * (1 - COINFLIP_RAKE_PERCENT / 100),
    },
}
