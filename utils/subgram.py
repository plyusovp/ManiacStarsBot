"""
Модуль для интеграции с Subgram API для проверки обязательной подписки.
"""

import logging
from typing import Any, Dict, Optional

import aiohttp
from aiogram.types import User

from config import settings

logger = logging.getLogger(__name__)


class SubgramAPI:
    """Класс для работы с Subgram API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://subgram.ru/api"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Асинхронный контекстный менеджер для создания сессии."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии при выходе из контекста."""
        if self.session:
            await self.session.close()

    async def check_subscription(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Проверяет подписку пользователя на канал.

        Args:
            user_id: ID пользователя в Telegram
            username: Имя пользователя (без @)
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            language_code: Код языка пользователя

        Returns:
            Словарь с результатом проверки подписки
        """
        if not self.session:
            raise RuntimeError("Сессия не инициализирована. Используйте async with.")

        # Подготавливаем данные для запроса
        data = {
            "api_key": self.api_key,
            "user_id": user_id,
        }

        # Добавляем опциональные параметры, если они есть
        if username:
            data["username"] = username
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        if language_code:
            data["language_code"] = language_code

        try:
            async with self.session.post(
                f"{self.base_url}/check_subscription",
                json=data,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(
                        f"Subgram API: Проверка подписки для пользователя {user_id}: {result}"
                    )
                    return result
                else:
                    logger.error(
                        f"Subgram API: Ошибка HTTP {response.status} при проверке подписки"
                    )
                    # Если API возвращает ошибку, разрешаем доступ пользователю
                    return {
                        "success": True,
                        "subscribed": True,
                        "error": f"HTTP {response.status}",
                        "message": "Сервис проверки подписки временно недоступен",
                    }

        except aiohttp.ClientError as e:
            logger.error(f"Subgram API: Ошибка сети при проверке подписки: {e}")
            # Если API недоступен, разрешаем доступ пользователю
            return {
                "success": True,
                "subscribed": True,
                "error": str(e),
                "message": "Сервис проверки подписки временно недоступен",
            }
        except Exception as e:
            logger.error(f"Subgram API: Неожиданная ошибка при проверке подписки: {e}")
            # В случае неожиданной ошибки разрешаем доступ пользователю
            return {
                "success": True,
                "subscribed": True,
                "error": str(e),
                "message": "Сервис проверки подписки временно недоступен",
            }

    async def get_user_info(self, user: User) -> Dict[str, Any]:
        """
        Получает информацию о пользователе для проверки подписки.

        Args:
            user: Объект пользователя из aiogram

        Returns:
            Результат проверки подписки
        """
        return await self.check_subscription(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
        )


# Глобальная функция для удобства использования
async def check_user_subscription(user: User) -> Dict[str, Any]:
    """
    Проверяет подписку пользователя через Subgram API.

    Args:
        user: Объект пользователя из aiogram

    Returns:
        Словарь с результатом проверки подписки
    """
    if not hasattr(settings, "SUBGRAM_API_KEY") or not settings.SUBGRAM_API_KEY:
        logger.warning("Subgram API ключ не настроен")
        return {
            "success": False,
            "error": "API key not configured",
            "message": "Сервис проверки подписки не настроен",
        }

    async with SubgramAPI(settings.SUBGRAM_API_KEY) as api:
        return await api.get_user_info(user)
