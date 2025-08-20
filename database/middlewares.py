# handlers/middlewares.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
import database.db as db

class LastSeenMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем, что у события есть пользователь
        user = data.get('event_from_user')
        if user:
            # Обновляем время последнего визита
            await db.update_user_last_seen(user.id)
        
        # Пропускаем событие дальше, к основным обработчикам
        return await handler(event, data)