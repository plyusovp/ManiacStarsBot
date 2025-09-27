# plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/config.py

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

    # --- ID администраторов для админ-панели ---
    MARK_ID: int = 1711962100
    MAXIM_ID: int = 1196053514

    # --- Настройки экономики и игр ---
    INITIAL_BALANCE: int = 0
    DUEL_RAKE_PERCENT: int
    DUEL_BOOST_COST: int = 1
    DUEL_REROLL_COST: int = 2
    REFERRAL_BONUS: int = 5
    MIN_REFERRALS_FOR_WITHDRAW: int = 5

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

    # --- Старые Медиа (FILE_ID) ---
    PHOTO_MAIN_MENU: str = "AgACAgQAAxkBAAIH42jElgmn6BB8_Id-jKc7SwEWjaIxAAKJzzEbKHEhUmI1AAFPzWmoQAEAAwIAA3kAAzYE"
    PHOTO_GAMES_MENU: str = "AgACAgQAAxkBAAIH5WjEl27FsoitJkCDl_fls8xltAABPwACMcoxG_KCKVK5XWe6RKn9OQEAAwIAA3kAAzYE"
    PHOTO_WITHDRAW: str = "AgACAgQAAxkBAAIH52jEmQABRRDUNSU5oeleD3mxdoZ34wACNsoxG_KCKVIa4lfrb-fI6QEAAwIAA3kAAzYE"
    PHOTO_PROFILE: str = "AgACAgQAAxkBAAIH6WjEmTvcYbN-DwMbOyPrpvg0JVdDAAI3yjEb8oIpUufbqS5NjCJ6AQADAgADeQADNgQ"
    PHOTO_TOP: str = "AgACAgQAAxkBAAIH62jEmV80plSZCho_rs2aF5NoZuJSAAI4yjEb8oIpUmsSCvSg6q-RAQADAgADeQADNgQ"
    PHOTO_PROMO: str = "AgACAgQAAxkBAAIH7WjEmZyC46umULOyFQ_eaCVEZz6HAAI6yjEb8oIpUnqOncQsYsXlAQADAgADeQADNgQ"
    PHOTO_EARN_STARS: str = "AgACAgQAAxkBAAIH8WjEmyW1XdLZSG_qd4z-nEfewxUDAAI9yjEb8oIpUvfGPlFenoImAQADAgADeQADNgQ"
    PHOTO_ACHIEVEMENTS: str = "AgACAgQAAxkBAAIH72jEmf5nIhZVIeyHkl7o4i3PUrV3AAI7yjEb8oIpUi4QwQoZ0aMDAQADAgADeQADNgQ"

    # --- Новые и обновленные фото ---
    PHOTO_RESOURCES: str = "AgACAgQAAxkBAAEBRahoxtbkPuDr2vkDniunHd1eDQRjfwACGs8xGyhxIVIL4TQKmD6kGwEAAwIAA3kAAzYE"
    PHOTO_DUEL_MENU: str = "AgACAgQAAxkBAAEBRbloxtd_hT3U2PWdnDfyISJsQkYS9AACmcsxG4K_IFLOUIM0qh2bfwEAAwIAA3kAAzYE"
    PHOTO_COINFLIP_MENU: str = "AgACAgQAAxkBAAEBRatoxtb8z0zCYYgYO9AdMkKTi5FwgAACFc8xGyhxIVJz7d0SDKi2oQEAAwIAA3kAAzYE"
    PHOTO_COINFLIP_PROCESS: str = "AgACAgQAAxkBAAEBRa5oxtcE-LOFVz26ZnIrRx7SZR9WsgACocsxG4K_IFLHLjFwpfluEgEAAwIAA3kAAzYE"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

DUEL_STAKES = [10, 25, 50, 100, 250]
TIMER_STAKES = [10, 25, 50, 100]
COINFLIP_STAKES = [10, 25, 50, 100, 250, 500]
SLOTS_STAKES = [1, 3, 5, 10]
BOWLING_STAKES = [1, 3, 5, 10]