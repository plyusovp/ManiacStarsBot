"""
Middleware для проверки обязательной подписки через Subgram.
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import settings
from utils.subgram import check_user_subscription

logger = logging.getLogger(__name__)


class SubgramMiddleware(BaseMiddleware):
    """
    Middleware для проверки подписки пользователя на обязательный канал.
    Блокирует доступ к боту, если пользователь не подписан.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Проверяем, включена ли проверка подписки
        if not self.enabled:
            return await handler(event, data)

        # Проверяем, что у события есть пользователь
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # Администраторы всегда имеют доступ
        if user.id in settings.ADMIN_IDS:
            return await handler(event, data)

        try:
            # Проверяем подписку пользователя
            subscription_result = await check_user_subscription(user)

            # Если проверка прошла успешно и пользователь подписан
            if subscription_result.get("success") and subscription_result.get(
                "subscribed", False
            ):
                return await handler(event, data)

            # Если пользователь не подписан, показываем сообщение о необходимости подписки
            await self._handle_subscription_required(event, subscription_result)
            return  # Блокируем дальнейшую обработку

        except Exception as e:
            logger.error(
                f"Ошибка при проверке подписки для пользователя {user.id}: {e}"
            )
            # В случае ошибки пропускаем проверку, чтобы не блокировать бота
            logger.warning(
                f"Subgram API недоступен, пропускаем проверку подписки для пользователя {user.id}"
            )
            return await handler(event, data)

    async def _handle_subscription_required(
        self, event: TelegramObject, subscription_result: Dict[str, Any]
    ) -> None:
        """
        Обрабатывает случай, когда пользователь не подписан на канал.
        """
        error_message = subscription_result.get(
            "message", "Для использования бота необходимо подписаться на канал"
        )

        # Получаем информацию о канале из результата API
        channel_info = subscription_result.get("channel", {})
        channel_username = channel_info.get("username", "")
        channel_url = channel_info.get("url", "")

        # Формируем сообщение
        message_text = f"🔒 {error_message}\n\n"

        if channel_url:
            message_text += f"📢 Подпишитесь на канал: {channel_url}"
        elif channel_username:
            message_text += f"📢 Подпишитесь на канал: @{channel_username}"
        else:
            message_text += "📢 Подпишитесь на обязательный канал для продолжения"

        message_text += "\n\nПосле подписки нажмите кнопку 'Проверить подписку'"

        try:
            # Создаем inline клавиатуру с кнопкой проверки подписки
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔍 Проверить подписку",
                            callback_data="check_subscription",
                        )
                    ]
                ]
            )

            if isinstance(event, Message):
                await event.answer(message_text, reply_markup=keyboard)
            elif isinstance(event, CallbackQuery):
                await event.message.edit_text(message_text, reply_markup=keyboard)
                await event.answer()

        except TelegramBadRequest as e:
            logger.error(f"Ошибка при отправке сообщения о подписке: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке требования подписки: {e}")
