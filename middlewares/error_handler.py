# middlewares/error_handler.py
import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict

import aiosqlite
from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Update

from lexicon.texts import LEXICON_ERRORS


class ErrorHandler(BaseMiddleware):
    """
    Перехватывает исключения в хендлерах, логирует их и
    отправляет пользователю вежливое сообщение об ошибке.
    """

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        extra = {
            "user_id": data.get("user_id"),
            "trace_id": data.get("trace_id"),
        }
        try:
            return await handler(event, data)
        except TelegramBadRequest as e:
            logging.info(
                "Telegram API error (BadRequest): %s. Update: %s",
                e,
                event.model_dump_json(exclude_none=True),
                extra=extra,
            )
        except (aiosqlite.Error, aiosqlite.Warning) as e:
            logging.error(
                "Database error: %s. Update: %s",
                e,
                event.model_dump_json(exclude_none=True),
                exc_info=True,
                extra=extra,
            )
            await self._send_error_message(event, "db_error")
        except asyncio.TimeoutError as e:
            logging.warning(
                "Timeout error: %s. Update: %s",
                e,
                event.model_dump_json(exclude_none=True),
                exc_info=True,
                extra=extra,
            )
            await self._send_error_message(event, "timeout_error")
        except Exception as e:
            logging.error(
                "Unhandled exception: %s. Update: %s",
                e,
                event.model_dump_json(exclude_none=True),
                exc_info=True,
                extra=extra,
            )
            await self._send_error_message(event, "unknown_error")

    async def _send_error_message(self, event: Update, error_key: str):
        """Отправляет сообщение пользователю в зависимости от типа события."""
        message_text = LEXICON_ERRORS.get(error_key, LEXICON_ERRORS["unknown_error"])
        if event.message:
            await event.message.answer(message_text)
        elif event.callback_query:
            await event.callback_query.answer(message_text, show_alert=True)
