# config.py
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Секретные данные, которые читаются из .env
    BOT_TOKEN: str

    ADMIN_IDS: List[int]

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def split_admin_ids(cls, v: str) -> List[int]:
        if isinstance(v, str):
            return [int(i.strip()) for i in v.split(",")]
        return v

    CHANNEL_ID: int
    DUEL_RAKE_PERCENT: int
    PAYLOAD_HMAC_SECRET: str

    # Ссылки для кнопок в меню
    URL_CHANNEL: str
    URL_WITHDRAWALS: str
    URL_SUPPORT: str

    # НАСТРОЙКИ ЭКОНОМИКИ ПОДАРКОВ
    REWARDS_ENABLED: bool = True
    MAX_REWARDS_PER_DAY: int = 3
    MAX_REWARDS_STARS_PER_DAY: int = 500

    # Публичные данные, которые остаются в коде
    REFERRAL_LINK_TTL_HOURS: int = 720
    PHOTO_MAIN_MENU: str = "https://i.postimg.cc/0MJDw9T8/main_menu.jpg"
    PHOTO_WITHDRAW: str = "https://i.postimg.cc/kVLt9kBL/withdraw.jpg"
    PHOTO_PROFILE: str = "https://i.postimg.cc/9zdq5gVN/profile.jpg"
    PHOTO_TOP: str = "https://i.postimg.cc/Z9vCfVVH/top.jpg"
    PHOTO_PROMO: str = "https://i.postimg.cc/0r0ddy6Q/promo.jpg"
    PHOTO_EARN_STARS: str = "https://i.postimg.cc/tYRdrGPz/earn_stars.jpg"
    PHOTO_ACHIEVEMENTS: str = "https://i.postimg.cc/8JBWHZz3/achievements.jpg"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
