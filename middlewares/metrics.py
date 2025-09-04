# middlewares/metrics.py
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update

# Импортируем словари с активными играми
from handlers.duel_handlers import active_duels
from handlers.timer_handlers import active_timers


class MetricsMiddleware(BaseMiddleware):
    """
    Собирает и логирует ключевые метрики о состоянии бота.
    """

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        # Логируем метрики до обработки хендлером
        extra = {
            "user_id": data.get("user_id"),
            "trace_id": data.get("trace_id"),
            "metrics": {
                "duels_active": len(active_duels),
                "timers_active": len(active_timers),
            },
        }
        logging.info("Bot metrics collected", extra=extra)

        return await handler(event, data)
