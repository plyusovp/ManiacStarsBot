# middlewares/throttling.py
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Update
from cachetools import TTLCache

from config import settings


class ThrottlingMiddleware(BaseMiddleware):
    """
    Мидлварь для защиты от спама (флуда).
    """

    def __init__(self, rate_limit: float = 0.7):
        # Используем TTL кеш для хранения времени последнего сообщения от пользователя.
        # Записи в кеше автоматически удаляются через `rate_limit` секунд.
        self.caches = {"default": TTLCache(maxsize=10_000, ttl=rate_limit)}

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем пользователя из события
        if event.message:
            user = event.message.from_user
        elif event.callback_query:
            user = event.callback_query.from_user
        else:
            # Если тип события не поддерживается, пропускаем
            return await handler(event, data)

        # Если пользователя нет или он админ, пропускаем
        if not user or user.id in settings.ADMIN_IDS:
            return await handler(event, data)

        # Получаем флаг 'throttling_key' из хендлера, если он есть
        throttling_key = get_flag(data, "throttling_key")
        if throttling_key is not None and throttling_key not in self.caches:
            self.caches[throttling_key] = TTLCache(
                maxsize=10_000, ttl=settings.THROTTLING_RATE_LIMIT
            )

        cache_key = throttling_key or "default"
        cache = self.caches[cache_key]

        # Если пользователь уже есть в кеше, значит он пишет слишком часто
        if user.id in cache:
            # Можно отправить сообщение о флуде, но лучше просто игнорировать
            # чтобы не создавать лишней нагрузки.
            return

        # Добавляем пользователя в кеш
        cache[user.id] = None

        # Передаем управление дальше по цепочке
        return await handler(event, data)
