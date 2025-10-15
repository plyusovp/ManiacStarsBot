"""
Модуль для интеграции с новым SubGram API (api.subgram.org).
Поддерживает получение спонсоров, проверку подписок и webhooks.
"""

import logging
from typing import Any, Dict, List, Optional

import aiohttp
from aiogram.types import User

from config import settings

logger = logging.getLogger(__name__)


class SubGramAPI:
    """Класс для работы с новым SubGram API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = settings.SUBGRAM_BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Асинхронный контекстный менеджер для создания сессии."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии при выходе из контекста."""
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Получает заголовки для запросов к API."""
        return {"Auth": self.api_key, "Content-Type": "application/json"}

    async def register_user(
        self,
        chat_id: int,
        user_id: int,
        first_name: Optional[str] = None,
        username: Optional[str] = None,
        language_code: Optional[str] = None,
        is_premium: Optional[bool] = None,
        gender: Optional[str] = None,
        age: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Регистрирует пользователя в системе Subgram.

        Args:
            chat_id: ID чата, откуда идет запрос
            user_id: ID пользователя Telegram
            first_name: Имя пользователя
            username: Юзернейм пользователя (без @)
            language_code: Язык интерфейса Telegram
            is_premium: Наличие Telegram Premium
            gender: Пол пользователя (male/female)
            age: Возраст пользователя

        Returns:
            Результат регистрации
        """
        if not self.session:
            raise RuntimeError("Сессия не инициализирована. Используйте async with.")

        # Подготавливаем данные для регистрации
        data = {"chat_id": chat_id, "user_id": user_id, "action": "newtask"}

        # Добавляем опциональные параметры
        if first_name:
            data["first_name"] = first_name
        if username:
            data["username"] = username
        if language_code:
            data["language_code"] = language_code
        if is_premium is not None:
            data["is_premium"] = is_premium
        if gender:
            data["gender"] = gender
        if age:
            data["age"] = age

        try:
            logger.info(
                f"SubGram API: Регистрация пользователя {user_id}, chat_id {chat_id}"
            )
            logger.debug(f"SubGram API: Данные регистрации: {data}")

            async with self.session.post(
                f"{self.base_url}/get-sponsors",
                json=data,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                result = await response.json()
                logger.info(
                    f"SubGram API: Ответ регистрации - статус {response.status}, результат: {result}"
                )

                if response.status == 200:
                    logger.info(
                        f"SubGram API: Пользователь {user_id} успешно зарегистрирован"
                    )
                    return result
                else:
                    logger.error(
                        f"SubGram API: Ошибка регистрации HTTP {response.status}: {result}"
                    )
                    return {
                        "status": "error",
                        "code": response.status,
                        "message": result.get(
                            "message", "Ошибка при регистрации пользователя"
                        ),
                        "result": None,
                    }

        except aiohttp.ClientError as e:
            logger.error(f"SubGram API: Ошибка сети при регистрации: {e}")
            return {
                "status": "error",
                "code": 0,
                "message": f"Ошибка сети: {str(e)}",
                "result": None,
            }
        except Exception as e:
            logger.error(f"SubGram API: Неожиданная ошибка при регистрации: {e}")
            return {
                "status": "error",
                "code": 0,
                "message": f"Неожиданная ошибка: {str(e)}",
                "result": None,
            }

    async def get_sponsors(
        self,
        chat_id: int,
        user_id: int,
        first_name: Optional[str] = None,
        username: Optional[str] = None,
        language_code: Optional[str] = None,
        is_premium: Optional[bool] = None,
        action: str = "subscribe",
        gender: Optional[str] = None,
        age: Optional[int] = None,
        max_sponsors: int = 5,
        exclude_resource_ids: Optional[List[str]] = None,
        exclude_ads_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Получает список спонсоров для обязательной подписки.

        Args:
            chat_id: ID чата, откуда идет запрос
            user_id: ID пользователя Telegram
            first_name: Имя пользователя
            username: Юзернейм пользователя (без @)
            language_code: Язык интерфейса Telegram
            is_premium: Наличие Telegram Premium
            action: Тип действия (subscribe/newtask)
            gender: Пол пользователя (male/female)
            age: Возраст пользователя
            max_sponsors: Максимальное количество спонсоров
            exclude_resource_ids: ID ресурсов для исключения
            exclude_ads_ids: ID заказов для исключения

        Returns:
            Результат запроса с данными о спонсорах
        """
        if not self.session:
            raise RuntimeError("Сессия не инициализирована. Используйте async with.")

        # Подготавливаем данные для запроса
        data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "action": action,
            "max_sponsors": max_sponsors,
        }

        # Добавляем опциональные параметры
        if first_name:
            data["first_name"] = first_name
        if username:
            data["username"] = username
        if language_code:
            data["language_code"] = language_code
        if is_premium is not None:
            data["is_premium"] = is_premium
        if gender:
            data["gender"] = gender
        if age:
            data["age"] = age
        if exclude_resource_ids:
            data["exclude_resource_ids"] = exclude_resource_ids
        if exclude_ads_ids:
            data["exclude_ads_ids"] = exclude_ads_ids

        try:
            logger.info(
                f"SubGram API: Запрос спонсоров для пользователя {user_id}, chat_id {chat_id}"
            )
            logger.debug(f"SubGram API: Данные запроса: {data}")

            async with self.session.post(
                f"{self.base_url}/get-sponsors",
                json=data,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                result = await response.json()
                logger.info(
                    f"SubGram API: Ответ от сервера - статус {response.status}, результат: {result}"
                )

                if response.status == 200:
                    logger.info(
                        f"SubGram API: Получены спонсоры для пользователя {user_id}"
                    )
                    return result
                else:
                    logger.error(
                        f"SubGram API: Ошибка HTTP {response.status}: {result}"
                    )
                    return {
                        "status": "error",
                        "code": response.status,
                        "message": result.get(
                            "message", "Ошибка при получении спонсоров"
                        ),
                        "result": None,
                    }

        except aiohttp.ClientError as e:
            logger.error(f"SubGram API: Ошибка сети при получении спонсоров: {e}")
            return {
                "status": "error",
                "code": 0,
                "message": f"Ошибка сети: {str(e)}",
                "result": None,
            }
        except Exception as e:
            logger.error(
                f"SubGram API: Неожиданная ошибка при получении спонсоров: {e}"
            )
            return {
                "status": "error",
                "code": 0,
                "message": f"Неожиданная ошибка: {str(e)}",
                "result": None,
            }

    async def get_user_subscriptions(
        self, user_id: int, bot_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Проверяет подписки пользователя.

        Args:
            user_id: ID пользователя Telegram
            bot_id: ID бота (опционально)

        Returns:
            Результат проверки подписок
        """
        if not self.session:
            raise RuntimeError("Сессия не инициализирована. Используйте async with.")

        data = {"user_id": user_id}
        if bot_id:
            data["bot_id"] = bot_id

        try:
            async with self.session.post(
                f"{self.base_url}/get-user-subscriptions",
                json=data,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                result = await response.json()

                if response.status == 200:
                    logger.info(
                        f"SubGram API: Проверены подписки пользователя {user_id}"
                    )
                    return result
                else:
                    logger.error(
                        f"SubGram API: Ошибка HTTP {response.status}: {result}"
                    )
                    return {
                        "status": "error",
                        "code": response.status,
                        "message": result.get(
                            "message", "Ошибка при проверке подписок"
                        ),
                        "result": None,
                    }

        except aiohttp.ClientError as e:
            logger.error(f"SubGram API: Ошибка сети при проверке подписок: {e}")
            return {
                "status": "error",
                "code": 0,
                "message": f"Ошибка сети: {str(e)}",
                "result": None,
            }
        except Exception as e:
            logger.error(f"SubGram API: Неожиданная ошибка при проверке подписок: {e}")
            return {
                "status": "error",
                "code": 0,
                "message": f"Неожиданная ошибка: {str(e)}",
                "result": None,
            }

    async def get_user_info(
        self, user: User, chat_id: int, auto_register: bool = True
    ) -> Dict[str, Any]:
        """
        Получает информацию о пользователе и проверяет подписки.

        Args:
            user: Объект пользователя из aiogram
            chat_id: ID чата
            auto_register: Автоматически регистрировать пользователя если не найден

        Returns:
            Результат проверки подписки
        """
        # Сначала получаем спонсоров
        sponsors_result = await self.get_sponsors(
            chat_id=chat_id,
            user_id=user.id,
            first_name=user.first_name,
            username=user.username,
            language_code=user.language_code,
            is_premium=getattr(user, "is_premium", None),
        )

        # Обрабатываем результат получения спонсоров
        logger.info(
            f"SubGram API: Обработка результата для пользователя {user.id}: {sponsors_result}"
        )

        if isinstance(sponsors_result, dict):
            if sponsors_result.get("status") == "ok" and sponsors_result.get("result"):
                # Есть спонсоры, проверяем подписки
                logger.info(
                    f"SubGram API: Найдены спонсоры для пользователя {user.id}, проверяем подписки"
                )
                subscriptions_result = await self.get_user_subscriptions(user.id)
                subscribed = self._check_subscription_status(subscriptions_result)
                logger.info(
                    f"SubGram API: Пользователь {user.id} подписан: {subscribed}"
                )

                return {
                    "success": True,
                    "sponsors": sponsors_result.get("result", []),
                    "subscriptions": subscriptions_result.get("result", []),
                    "subscribed": subscribed,
                    "form": sponsors_result.get("form"),  # Анкета для заполнения
                    "form_url": sponsors_result.get("form_url"),  # Ссылка на анкету
                }
            elif sponsors_result.get(
                "code"
            ) == 400 and "пользователя нет в Вашем боте" in sponsors_result.get(
                "message", ""
            ):
                # Пользователь не зарегистрирован в боте
                logger.warning(
                    f"SubGram API: Пользователь {user.id} не найден в боте. Сообщение: {sponsors_result.get('message')}"
                )

                if auto_register:
                    # Пытаемся автоматически зарегистрировать пользователя
                    logger.info(
                        f"SubGram API: Попытка автоматической регистрации пользователя {user.id}"
                    )

                    # Пытаемся получить спонсоров с action=newtask для автоматической регистрации
                    register_sponsors_result = await self.get_sponsors(
                        chat_id=chat_id,
                        user_id=user.id,
                        first_name=user.first_name,
                        username=user.username,
                        language_code=user.language_code,
                        is_premium=getattr(user, "is_premium", None),
                        action="newtask",  # Пытаемся зарегистрировать через newtask
                    )

                    logger.info(
                        f"SubGram API: Результат регистрации: {register_sponsors_result}"
                    )

                    if register_sponsors_result.get("status") == "ok":
                        logger.info(
                            f"SubGram API: Пользователь {user.id} успешно зарегистрирован, получаем спонсоров"
                        )
                        # После регистрации снова получаем спонсоров для подписки
                        sponsors_result = await self.get_sponsors(
                            chat_id=chat_id,
                            user_id=user.id,
                            first_name=user.first_name,
                            username=user.username,
                            language_code=user.language_code,
                            is_premium=getattr(user, "is_premium", None),
                            action="subscribe",
                        )

                        if sponsors_result.get(
                            "status"
                        ) == "ok" and sponsors_result.get("result"):
                            # Теперь есть спонсоры, проверяем подписки
                            subscriptions_result = await self.get_user_subscriptions(
                                user.id
                            )
                            subscribed = self._check_subscription_status(
                                subscriptions_result
                            )

                            return {
                                "success": True,
                                "sponsors": sponsors_result.get("result", []),
                                "subscriptions": subscriptions_result.get("result", []),
                                "subscribed": subscribed,
                                "form": sponsors_result.get("form"),
                                "form_url": sponsors_result.get("form_url"),
                                "auto_registered": True,
                            }
                        else:
                            logger.warning(
                                f"SubGram API: После регистрации не удалось получить спонсоров: {sponsors_result}"
                            )
                    else:
                        logger.warning(
                            f"SubGram API: Не удалось зарегистрировать пользователя {user.id}: {register_sponsors_result}"
                        )

                # Если автоматическая регистрация не удалась или отключена
                logger.info(
                    f"SubGram API: Пользователь {user.id} не найден в боте, требуется регистрация"
                )

                # Извлекаем информацию о форме из ответа API
                form_info = self._extract_form_info(sponsors_result)

                # Если форма не найдена в ответе API, это означает, что пользователь не зарегистрирован в системе Subgram
                if not form_info.get("form") and not form_info.get("form_url"):
                    logger.warning(
                        f"SubGram API: Пользователь {user.id} не зарегистрирован в системе Subgram. Анкета не настроена."
                    )
                    return {
                        "success": False,
                        "error": "user_not_registered_in_subgram",
                        "message": "Для использования бота необходимо обратиться к администратору для регистрации в системе",
                        "sponsors": [],
                        "subscriptions": [],
                        "subscribed": False,
                        "form": None,
                        "form_url": None,
                        "requires_registration": True,
                        "requires_admin_registration": True,
                    }

                return {
                    "success": False,
                    "error": "user_not_found",
                    "message": "Для использования бота необходимо заполнить анкету",
                    "sponsors": [],
                    "subscriptions": [],
                    "subscribed": False,
                    "form": form_info.get("form"),
                    "form_url": form_info.get("form_url"),
                    "requires_registration": True,
                }
            else:
                # Другие ошибки
                error_msg = sponsors_result.get("message", "Ошибка получения спонсоров")
                logger.warning(
                    f"SubGram API: Ошибка для пользователя {user.id}: {error_msg}"
                )
                return {
                    "success": False,
                    "error": error_msg,
                    "message": error_msg,
                    "sponsors": [],
                    "subscriptions": [],
                    "subscribed": False,
                    "form": sponsors_result.get("form"),
                    "form_url": sponsors_result.get("form_url"),
                }
        else:
            logger.error(
                f"SubGram API: Некорректный ответ для пользователя {user.id}: {type(sponsors_result)}"
            )
            return {
                "success": False,
                "error": "invalid_response",
                "message": "Некорректный ответ от сервера",
                "sponsors": [],
                "subscriptions": [],
                "subscribed": False,
            }

    def _check_subscription_status(self, subscriptions_result: Dict[str, Any]) -> bool:
        """
        Проверяет статус подписки на основе результата API.

        Args:
            subscriptions_result: Результат проверки подписок

        Returns:
            True если пользователь подписан, False иначе
        """
        if subscriptions_result.get("status") != "ok":
            return False

        subscriptions = subscriptions_result.get("result", [])
        if not subscriptions:
            return False

        # Проверяем, есть ли активные подписки
        for subscription in subscriptions:
            if subscription.get("status") in ["subscribed", "notgetted"]:
                return True

        return False

    def _extract_form_info(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает информацию о форме из ответа API.

        Args:
            api_response: Ответ от Subgram API

        Returns:
            Словарь с информацией о форме
        """
        form_info = {"form": None, "form_url": None}

        # Проверяем различные возможные места, где может быть информация о форме
        if "form" in api_response:
            form_info["form"] = api_response["form"]
        if "form_url" in api_response:
            form_info["form_url"] = api_response["form_url"]

        # Проверяем в result, если это массив или объект
        result = api_response.get("result")
        if isinstance(result, dict):
            if "form" in result:
                form_info["form"] = result["form"]
            if "form_url" in result:
                form_info["form_url"] = result["form_url"]
        elif isinstance(result, list) and len(result) > 0:
            # Если result - массив, проверяем первый элемент
            first_item = result[0]
            if isinstance(first_item, dict):
                if "form" in first_item:
                    form_info["form"] = first_item["form"]
                if "form_url" in first_item:
                    form_info["form_url"] = first_item["form_url"]

        logger.info(f"SubGram API: Извлечена информация о форме: {form_info}")
        return form_info


# Глобальные функции для удобства использования
async def check_user_subscription_new(
    user: User, chat_id: int, auto_register: bool = True
) -> Dict[str, Any]:
    """
    Проверяет подписку пользователя через новый SubGram API.

    Args:
        user: Объект пользователя из aiogram
        chat_id: ID чата
        auto_register: Автоматически регистрировать пользователя если не найден

    Returns:
        Словарь с результатом проверки подписки
    """
    if not hasattr(settings, "SUBGRAM_API_KEY") or not settings.SUBGRAM_API_KEY:
        logger.warning("SubGram API ключ не настроен")
        return {
            "success": False,
            "error": "API key not configured",
            "message": "Сервис проверки подписки не настроен",
            "subscribed": False,
        }

    async with SubGramAPI(settings.SUBGRAM_API_KEY) as api:
        return await api.get_user_info(user, chat_id, auto_register)


async def register_user_in_subgram(user: User, chat_id: int) -> Dict[str, Any]:
    """
    Регистрирует пользователя в системе Subgram.

    Args:
        user: Объект пользователя из aiogram
        chat_id: ID чата

    Returns:
        Словарь с результатом регистрации
    """
    if not hasattr(settings, "SUBGRAM_API_KEY") or not settings.SUBGRAM_API_KEY:
        logger.warning("SubGram API ключ не настроен")
        return {
            "status": "error",
            "message": "Сервис регистрации не настроен",
            "result": None,
        }

    async with SubGramAPI(settings.SUBGRAM_API_KEY) as api:
        return await api.register_user(
            chat_id=chat_id,
            user_id=user.id,
            first_name=user.first_name,
            username=user.username,
            language_code=user.language_code,
            is_premium=getattr(user, "is_premium", None),
        )


async def get_sponsors_for_user(
    user: User, chat_id: int, max_sponsors: int = 5
) -> Dict[str, Any]:
    """
    Получает спонсоров для пользователя.

    Args:
        user: Объект пользователя из aiogram
        chat_id: ID чата
        max_sponsors: Максимальное количество спонсоров

    Returns:
        Результат с данными о спонсорах
    """
    if not hasattr(settings, "SUBGRAM_API_KEY") or not settings.SUBGRAM_API_KEY:
        logger.warning("SubGram API ключ не настроен")
        return {
            "status": "error",
            "message": "Сервис проверки подписки не настроен",
            "result": None,
        }

    async with SubGramAPI(settings.SUBGRAM_API_KEY) as api:
        return await api.get_sponsors(
            chat_id=chat_id,
            user_id=user.id,
            first_name=user.first_name,
            username=user.username,
            language_code=user.language_code,
            is_premium=getattr(user, "is_premium", None),
            max_sponsors=max_sponsors,
        )


async def test_subgram_api_key() -> Dict[str, Any]:
    """
    Тестирует API ключ Subgram, проверяя доступность сервиса.

    Returns:
        Результат проверки API ключа
    """
    if not hasattr(settings, "SUBGRAM_API_KEY") or not settings.SUBGRAM_API_KEY:
        return {
            "success": False,
            "error": "API key not configured",
            "message": "API ключ не настроен",
        }

    # Тестируем с несуществующим пользователем
    test_data = {"chat_id": 123456789, "user_id": 987654321, "action": "subscribe"}

    async with SubGramAPI(settings.SUBGRAM_API_KEY) as api:
        try:
            result = await api.get_sponsors(**test_data)
            logger.info(f"SubGram API: Тест API ключа - результат: {result}")

            if result.get(
                "code"
            ) == 400 and "пользователя нет в Вашем боте" in result.get("message", ""):
                return {
                    "success": True,
                    "message": "API ключ работает корректно",
                    "details": "Сервис отвечает, но пользователь не найден (это нормально для тестового запроса)",
                }
            elif result.get("status") == "ok":
                return {
                    "success": True,
                    "message": "API ключ работает корректно",
                    "details": "Получены спонсоры для тестового пользователя",
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Неизвестная ошибка"),
                    "details": f"Код ответа: {result.get('code')}",
                }
        except Exception as e:
            logger.error(f"SubGram API: Ошибка при тестировании API ключа: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Ошибка при проверке API ключа",
            }
