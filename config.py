# config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Секретные данные, которые читаются из .env
    BOT_TOKEN: str
    ADMIN_IDS: List[int]
    CHANNEL_ID: int
    DUEL_RAKE_PERCENT: int

    # Публичные данные, которые остаются в коде
    PHOTO_MAIN_MENU: str = "https://i.postimg.cc/0MJDw9T8/main_menu.jpg"
    PHOTO_WITHDRAW: str = "https://i.postimg.cc/kVLt9kBL/withdraw.jpg"
    PHOTO_PROFILE: str = "https://i.postimg.cc/9zdq5gVN/profile.jpg"
    PHOTO_TOP: str = "https://i.postimg.cc/Z9vCfVVH/top.jpg"
    PHOTO_PROMO: str = "https://i.postimg.cc/0r0ddy6Q/promo.jpg"
    PHOTO_EARN_STARS: str = "https://i.postimg.cc/tYRdrGPz/earn_stars.jpg"
    PHOTO_ACHIEVEMENTS: str = "https://i.postimg.cc/8JBWHZz3/achievements.jpg"
    
    class Config:
        # Имя файла, откуда будут читаться секреты
        env_file = ".env"
        env_file_encoding = "utf-8"

# Создаём один-единственный экземпляр настроек, который будем использовать везде
settings = Settings()