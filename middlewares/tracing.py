# plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/middlewares/tracing.py

import uuid
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update


class TracingMiddleware(BaseMiddleware):
    """
    Генерирует уникальный trace_id для каждого события и прокидывает его в data.
    """

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        # Генерируем уникальный ID для трассировки
        trace_id = str(uuid.uuid4())
        data["trace_id"] = trace_id

        # Прокидываем user_id для удобства доступа
        user = data.get("event_from_user")
        if user:
            data["user_id"] = user.id
        else:
            data["user_id"] = None

        return await handler(event, data)
        