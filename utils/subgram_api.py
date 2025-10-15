"""
Универсальный модуль для интеграции с SubGram API.
Поддерживает получение спонсоров, проверку подписок и обработку callback'ов.
"""

import logging
from typing import Any, Dict, Optional

import aiohttp

from config import settings

logger = logging.getLogger(__name__)

# API настройки
API_KEY = settings.SUBGRAM_API_KEY
URL = "https://api.subgram.org/get-sponsors"
BLOCKING_SUBGRAM_STATUSES = ["warning", "gender", "age", "register"]


async def get_subgram_sponsors(
    user_id: int, chat_id: int, **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Универсальная функция для запроса спонсоров.

    Args:
        user_id: ID пользователя в Telegram
        chat_id: ID чата
        **kwargs: Дополнительные параметры (gender, age, action и т.д.)

    Returns:
        Словарь с результатом запроса или None в случае ошибки
    """
    headers = {"Auth": API_KEY}
    payload = {"user_id": user_id, "chat_id": chat_id}
    payload.update(kwargs)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                URL, headers=headers, json=payload, timeout=10
            ) as response:
                result = await response.json()
                logger.info(
                    f"SubGram API: Запрос для пользователя {user_id}, chat_id {chat_id}, результат: {result}"
                )
                return result
        except Exception as e:
            logger.error(f"Ошибка запроса к SubGram API: {e}")
            return None


async def check_user_subscription(
    user_id: int, chat_id: int, **kwargs
) -> Dict[str, Any]:
    """
    Проверяет подписку пользователя через SubGram API.

    Args:
        user_id: ID пользователя в Telegram
        chat_id: ID чата
        **kwargs: Дополнительные параметры

    Returns:
        Словарь с результатом проверки подписки
    """
    # Вызываем функцию для проверки подписки
    response = await get_subgram_sponsors(user_id=user_id, chat_id=chat_id, **kwargs)

    if not response:
        logger.error("Ошибка запроса к SubGram API: Не удалось осуществить запрос")
        # Если API недоступен, выдаем доступ, чтобы не терять пользователя
        return {
            "success": True,
            "subscribed": True,
            "error": "API недоступен",
            "message": "Сервис проверки подписки временно недоступен",
        }

    # Проверяем, если API возвращает ошибку о приостановке продаж
    if response.get("code") == 400 and "приостановлена продажа" in response.get(
        "message", ""
    ):
        logger.warning(
            f"SubGram API: Продажа ОП приостановлена. Предоставляем доступ пользователю {user_id}"
        )
        return {
            "success": True,
            "subscribed": True,
            "error": "Продажа ОП приостановлена",
            "message": "Доступ предоставлен",
        }

    status = response.get("status")

    if status and status in BLOCKING_SUBGRAM_STATUSES:
        # Если бот добавлен по токену и "Получать ссылки в API" - Выкл,
        # SubGram самостоятельно отправит сообщение
        # Вам как владельцу бота делать ничего не нужно
        return {
            "success": False,
            "subscribed": False,
            "status": status,
            "message": response.get(
                "message", "Требуется выполнение дополнительных условий"
            ),
            "sponsors": response.get("result", []),
            "form": response.get("form"),
            "form_url": response.get("form_url"),
            "total_fixed_link": response.get("total_fixed_link", 0),
        }
    else:
        if status and status == "error":
            logger.warning(
                f"Ошибка SubGram API: {response.get('message')}. Предоставляем доступ."
            )
            return {
                "success": True,
                "subscribed": True,
                "error": response.get("message"),
                "message": "Доступ предоставлен",
            }

        # Проверяем, что пользователь подписан на ВСЕ обязательные каналы
        sponsors = response.get("result", [])
        total_fixed_link = response.get("total_fixed_link", 0)

        # Если есть обязательные каналы для подписки, проверяем что пользователь подписан на все
        if total_fixed_link > 0 and sponsors:
            # Подсчитываем количество каналов, на которые пользователь должен быть подписан
            required_subscriptions = len(
                [s for s in sponsors if s.get("required", True)]
            )

            # Если есть каналы для подписки, но пользователь не подписан на все
            if required_subscriptions > 0:
                return {
                    "success": False,
                    "subscribed": False,
                    "message": f"Необходимо подписаться на все обязательные каналы ({required_subscriptions} из {required_subscriptions})",
                    "sponsors": sponsors,
                    "total_fixed_link": total_fixed_link,
                    "requires_full_subscription": True,
                }

        return {
            "success": True,
            "subscribed": True,
            "message": "Доступ предоставлен!",
            "sponsors": sponsors,
        }


async def handle_subgram_callback(
    user_id: int, chat_id: int, callback_data: str
) -> Dict[str, Any]:
    """
    Обрабатывает callback'и от SubGram (пол, возраст и т.д.).

    Args:
        user_id: ID пользователя в Telegram
        chat_id: ID чата
        callback_data: Данные callback'а

    Returns:
        Результат обработки callback'а
    """
    api_kwargs = {}

    if callback_data == "subgram-op":
        # Обычная проверка подписки
        pass
    elif callback_data.startswith("subgram_"):
        # Универсальная обработка для пола и возраста
        parts = callback_data.split("_")
        if len(parts) >= 3:
            param_type = parts[1]  # 'gender' или 'age'
            param_value = parts[2]  # 'male', 'c1', и т.д.
            api_kwargs[param_type] = param_value

    # Отправляем повторный запрос в SubGram API с новыми данными
    response = await get_subgram_sponsors(user_id, chat_id, **api_kwargs)

    if not response:
        logger.error(
            "Ошибка запроса к SubGram API при обработке callback: Не удалось осуществить запрос"
        )
        return {
            "success": True,
            "subscribed": True,
            "error": "API недоступен",
            "message": "Сервис проверки подписки временно недоступен",
        }

    # Проверяем, если API возвращает ошибку о приостановке продаж
    if response.get("code") == 400 and "приостановлена продажа" in response.get(
        "message", ""
    ):
        logger.warning(
            f"SubGram API: Продажа ОП приостановлена при обработке callback. Предоставляем доступ пользователю {user_id}"
        )
        return {
            "success": True,
            "subscribed": True,
            "error": "Продажа ОП приостановлена",
            "message": "Доступ предоставлен",
        }

    status = response.get("status")

    if status and status in BLOCKING_SUBGRAM_STATUSES:
        # Если бот добавлен по токену и "Получать ссылки в API" - Выкл,
        # SubGram самостоятельно отправит сообщение
        # Вам как владельцу бота делать ничего не нужно
        return {
            "success": False,
            "subscribed": False,
            "status": status,
            "message": response.get(
                "message", "Требуется выполнение дополнительных условий"
            ),
            "sponsors": response.get("result", []),
            "form": response.get("form"),
            "form_url": response.get("form_url"),
            "total_fixed_link": response.get("total_fixed_link", 0),
        }
    else:
        if status and status == "error":
            logger.warning(
                f"Ошибка SubGram API при обработке callback: {response.get('message')}. Предоставляем доступ."
            )

        # Проверяем, что пользователь подписан на ВСЕ обязательные каналы
        sponsors = response.get("result", [])
        total_fixed_link = response.get("total_fixed_link", 0)

        # Если есть обязательные каналы для подписки, проверяем что пользователь подписан на все
        if total_fixed_link > 0 and sponsors:
            # Подсчитываем количество каналов, на которые пользователь должен быть подписан
            required_subscriptions = len(
                [s for s in sponsors if s.get("required", True)]
            )

            # Если есть каналы для подписки, но пользователь не подписан на все
            if required_subscriptions > 0:
                return {
                    "success": False,
                    "subscribed": False,
                    "message": f"Необходимо подписаться на все обязательные каналы ({required_subscriptions} из {required_subscriptions})",
                    "sponsors": sponsors,
                    "total_fixed_link": total_fixed_link,
                    "requires_full_subscription": True,
                }

        return {
            "success": True,
            "subscribed": True,
            "message": "Доступ предоставлен!",
            "sponsors": sponsors,
        }
