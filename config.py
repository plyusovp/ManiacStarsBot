# config.py
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Секреты ---
    BOT_TOKEN: str
    ADMIN_IDS: List[int]
    CHANNEL_ID: int
    PAYLOAD_HMAC_SECRET: str
    BOT_USERNAME: str

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def split_admin_ids(cls, v: str) -> List[int]:
        if isinstance(v, str):
            # Убираем скобки и пробелы, затем разделяем по запятой
            cleaned_v = v.strip("[] ")
            if cleaned_v:
                return [int(i.strip()) for i in cleaned_v.split(",")]
            return []
        return v

    # --- Настройки экономики и игр ---
    INITIAL_BALANCE: int = 0
    DUEL_RAKE_PERCENT: int
    DUEL_BOOST_COST: int = 10
    DUEL_REROLL_COST: int = 15
    REFERRAL_BONUS: int = 5
    MIN_REFERRALS_FOR_WITHDRAW: int = 5

    # --- Настройки вывода ---
    REWARDS_ENABLED: bool = True
    MIN_WITHDRAWAL_AMOUNT: int = 100
    MAX_REWARDS_PER_DAY: int = 3
    MAX_REWARDS_STARS_PER_DAY: int = 500

    # --- Технические настройки ---
    REFERRAL_LINK_TTL_HOURS: int = 720  # 30 дней
    THROTTLING_RATE_LIMIT: float = 0.7  # Секунд между апдейтами от одного юзера
    ADMIN_PAGE_SIZE: int = 5

    # --- Ссылки ---
    URL_CHANNEL: str
    URL_WITHDRAWALS: str
    URL_SUPPORT: str

    # --- Медиа ---
    PHOTO_MAIN_MENU: str = "https://i.postimg.cc/0MJDw9T8/main_menu.jpg"
    PHOTO_GAMES_MENU: str = "https://i.postimg.cc/5yL6Vz3F/games.jpg"
    PHOTO_WITHDRAW: str = "https://i.postimg.cc/kVLt9kBL/withdraw.jpg"
    PHOTO_PROFILE: str = "https://i.postimg.cc/9zdq5gVN/profile.jpg"
    PHOTO_TOP: str = "https://i.postimg.cc/Z9vCfVVH/top.jpg"
    PHOTO_PROMO: str = "https://i.postimg.cc/0r0ddy6Q/promo.jpg"
    PHOTO_EARN_STARS: str = "https://i.postimg.cc/tYRdrGPz/earn_stars.jpg"
    PHOTO_ACHIEVEMENTS: str = "https://i.postimg.cc/8JBWHZz3/achievements.jpg"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

DUEL_STAKES = [10, 25, 50, 100, 250]
TIMER_STAKES = [10, 25, 50, 100]

# This is now defined in economy.py to avoid circular dependencies
# and keep economic constants in one place.
# COINFLIP_LEVELS will be imported from economy where needed.
