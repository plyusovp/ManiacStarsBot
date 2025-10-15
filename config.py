# plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/config.py

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Секреты ---
    BOT_TOKEN: str = ""
    ADMIN_IDS: List[int] = []
    CHANNEL_ID: int = 0
    BOT_USERNAME: str = ""
    # SubGram API настройки
    # ВАЖНО: Используйте API Key бота, а не Secret Key!
    # Получите в @subgram_officialbot → Профиль → Скопировать api token
    SUBGRAM_API_KEY: str = (
        "f042a25b7c52bbabf29b1a9fdcdd8ede7e098b622359ecfa4a1f7dbdefe51e3d"
    )
    SUBGRAM_BASE_URL: str = "https://api.subgram.org"

    # --- Настройки веб-сервера ---
    WEB_SERVER_HOST: str = "0.0.0.0"  # nosec B104
    WEB_SERVER_PORT: int = 8080

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

    # --- ID администраторов для админ-панели ---
    MARK_ID: int = 1711962100
    MAXIM_ID: int = 1196053514

    # --- Настройки экономики и игр ---
    INITIAL_BALANCE: int = 0
    DUEL_RAKE_PERCENT: int = 10
    DUEL_BOOST_COST: int = 1
    DUEL_REROLL_COST: int = 2
    REFERRAL_BONUS: int = 5
    MIN_REFERRALS_FOR_WITHDRAW: int = 5
    DAILY_BONUS_HOURS: int = 24
    DAILY_BONUS_AMOUNT: int = 1
    COINFLIP_RAKE_PERCENT: int = 7

    # --- Настройки вывода ---
    REWARDS_ENABLED: bool = True
    MIN_WITHDRAWAL_AMOUNT: int = 100
    MAX_REWARDS_PER_DAY: int = 3
    MAX_REWARDS_STARS_PER_DAY: int = 500

    # --- Технические настройки ---
    THROTTLING_RATE_LIMIT: float = 0.7
    ADMIN_PAGE_SIZE: int = 5

    # --- Ссылки ---
    URL_CHANNEL: str = "https://t.me/kolostats"
    URL_CHAT: str = "https://t.me/kolochats"
    URL_WITHDRAWALS: str = "https://t.me/withdraw0000"
    URL_MANUAL: str = "https://t.me/manualstar"
    URL_SUPPORT: str = "https://t.me/limejko"
    URL_WEBAPP_GAME: str = (
        "https://plyusovp.github.io/ManiacClic/"  # Замените на ваш URL
    )

    # --- Медиа (FILE_ID) ---
    # Временно отключены из-за устаревших FILE_ID
    PHOTO_MAIN_MENU: str = "AgACAgQAAxkBAAMWaO_XnA8cb6rIjtqnR7LzHc__1Y0AAu3NMRv-bIBTH8ueqXIHToUBAAMCAAN5AAM2BA"  # Экран Меню
    PHOTO_GAMES_MENU: str = "AgACAgQAAxkBAAMZaO_YLHolZAhr5ZaIyFEwYvcHstAAAvDNMRv-bIBTi-DLIQw4zEsBAAMCAAN5AAM2BA"  # Экран игр
    PHOTO_WITHDRAW: str = "AgACAgQAAxkBAAMbaO_YUU8XDdjTVVCpN5NQ7CXJsIMAAhnPMRsocSFSjTxn5PHCP0UBAAMCAAN5AAM2BA"  # Выводы
    PHOTO_PROFILE: str = "AgACAgQAAxkBAAMdaO_YZM1N-4I5tLNigYoOzIEtnXIAAmjKMRszgSlRCmv-a9ynyakBAAMCAAN5AAM2BA"  # Профиль
    PHOTO_TOP: str = "AgACAgQAAxkBAAMgaO_YklSMmZ9huhaWGHxA6smgyX4AAvHNMRv-bIBTKV9195dSTbcBAAMCAAN5AAM2BA"  # Топ игроков
    PHOTO_PROMO: str = "AgACAgQAAxkBAAMiaO_YxZLZhaKqoEcd64j8B4KR9PQAAmfKMRszgSlRq5z-pGEQtaEBAAMCAAN5AAM2BA"  # Промокоды
    PHOTO_EARN_STARS: str = "AgACAgQAAxkBAAMlaO_ZBCd2CPKOM3wnrIu0JdsWrh0AAvPNMRv-bIBT7artb4mO1LcBAAMCAAN5AAM2BA"  # Заработок звёзд
    PHOTO_ACHIEVEMENTS: str = "AgACAgQAAxkBAAMnaO_ZFwfFPHxXyrZodsa4x1F7omkAAvXNMRv-bIBTBT6hK4F5qaIBAAMCAAN5AAM2BA"  # Для достижений
    PHOTO_RESOURCES: str = "AgACAgQAAxkBAAMzaO_aGuChCXU6wqy2NqvoImpcT-EAAhrPMRsocSFSxgJxCY3RVYIBAAMCAAN5AAM2BA"  # Наши ресурсы
    PHOTO_DUEL_MENU: str = "AgACAgQAAxkBAAM4aO_aT7kAAd5I-wop6N-FjoFL1t6-AAKZyzEbgr8gUudybv5KTy7IAQADAgADeQADNgQ"  # Дуели
    PHOTO_COINFLIP_MENU: str = "AgACAgQAAxkBAAM2aO_aOv46SbvkyCoCW5WHpQRkgiEAA84xG_5sgFPObcXgHdkI_wEAAwIAA3kAAzYE"  # Орёл и решка
    PHOTO_COINFLIP_PROCESS: str = "AgACAgQAAxkBAAM2aO_aOv46SbvkyCoCW5WHpQRkgiEAA84xG_5sgFPObcXgHdkI_wEAAwIAA3kAAzYE"  # Орёл и решка (процесс)

    # --- Фотографии для игр ---
    PHOTO_FOOTBALL: str = "AgACAgQAAxkBAAMxaO_ZSPuBXvjSJs3RCLa8n4NCK18AAvvNMRv-bIBTkWo3eDwqmmcBAAMCAAN5AAM2BA"  # Для игры футбол
    PHOTO_BOWLING: str = "AgACAgQAAxkBAAMvaO_ZP65robpokR9dshjBVgRtGpEAAvrNMRv-bIBTjkUAAbhEnUKFAQADAgADeQADNgQ"  # Для боулинга
    PHOTO_BASKETBALL: str = "AgACAgQAAxkBAAMtaO_ZPNE1M3KCFpkC4XWyfeQhewkAAvnNMRv-bIBT5Mq3WN6cGGkBAAMCAAN5AAM2BA"  # Баскетбол
    PHOTO_DARTS: str = "AgACAgQAAxkBAAMtaO_ZPNE1M3KCFpkC4XWyfeQhewkAAvnNMRv-bIBT5Mq3WN6cGGkBAAMCAAN5AAM2BA"  # Для дартса (временно используем баскетбол)
    PHOTO_SLOTS: str = "AgACAgQAAxkBAAMpaO_ZH51uZJCALrclW3WLfW637VMAAvbNMRv-bIBTuKlfSaoFZV8BAAMCAAN5AAM2BA"  # Для слотов
    PHOTO_DICE: str = "AgACAgQAAxkBAAMnaO_ZFwfFPHxXyrZodsa4x1F7omkAAvXNMRv-bIBTBT6hK4F5qaIBAAMCAAN5AAM2BA"  # Для костей (dice игра)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

# --- Ставки для всех игр ---
# Сложные игры
DUEL_STAKES = [1, 2, 3, 4, 5]
TIMER_STAKES = [1, 2, 3, 4, 5]
COINFLIP_STAKES = [10, 25, 50, 100, 250, 500]

# Игры с маленькими ставками
SLOTS_STAKES = [1, 3, 5, 10]
BOWLING_STAKES = [1, 3, 5, 10]
FOOTBALL_STAKES = [1, 3, 5, 10]
BASKETBALL_STAKES = [1, 3, 5, 10]
DARTS_STAKES = [1, 3, 5, 10]
DICE_STAKES = [1, 3, 5, 10]
