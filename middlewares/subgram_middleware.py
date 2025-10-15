"""
Middleware для проверки обязательной подписки через новый SubGram API.
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, TelegramObject

from utils.subgram_api import check_user_subscription

logger = logging.getLogger(__name__)


class SubgramMiddleware(BaseMiddleware):
    """
    Middleware для проверки подписки пользователя на обязательный канал.
    Блокирует доступ к боту, если пользователь не подписан.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        super().__init__()

    def _get_chat_id(self, event: TelegramObject) -> int:
        """Получает chat_id из события."""
        if isinstance(event, Message):
            return event.chat.id
        elif isinstance(event, CallbackQuery):
            return event.message.chat.id if event.message else 0
        return 0

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
        if not isinstance(data, dict):
            logger.error(f"Данные middleware не являются словарем: {type(data)}")
            return await handler(event, data)

        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        try:
            # Получаем chat_id из события
            chat_id = self._get_chat_id(event)
            if not chat_id:
                return await handler(event, data)

            # Проверяем подписку пользователя через новую универсальную API функцию
            subscription_result = await check_user_subscription(user.id, chat_id)

            # Если проверка прошла успешно и пользователь подписан
            if subscription_result.get("success") and subscription_result.get(
                "subscribed", False
            ):
                return await handler(event, data)

            # Если пользователь не подписан или не зарегистрирован
            status = subscription_result.get("status")

            # Если статус "warning" и нет каналов - значит SubGram сам отправит сообщение
            if status == "warning" and not subscription_result.get("sponsors"):
                logger.info(
                    f"SubGram самостоятельно отправит сообщение пользователю {user.id}"
                )
                return  # Блокируем дальнейшую обработку, SubGram сам отправит сообщение

            # Иначе показываем наше сообщение
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
        Показывает каналы для подписки и формы если нужно.
        """
        message_text = ""

        # Получаем данные из результата
        error_message = subscription_result.get(
            "message", "Для использования бота необходимо подписаться на канал"
        )
        sponsors = subscription_result.get("sponsors", [])
        form = subscription_result.get("form")
        form_url = subscription_result.get("form_url")
        status = subscription_result.get("status")

        # Показываем сообщение об ошибке
        message_text += f"🔒 {error_message}\n\n"

        # Специальная обработка для статуса "warning"
        if status == "warning":
            message_text += (
                "⚠️ *Для доступа к боту требуется дополнительная информация*\n\n"
            )
            message_text += "📋 *Возможные причины:*\n"
            message_text += "• Вы не зарегистрированы в системе SubGram\n"
            message_text += "• Требуется заполнить анкету\n"
            message_text += "• Нужно подписаться на каналы\n\n"
            message_text += "🔗 *Обратитесь к администратору для получения доступа*\n\n"

        # Показываем форму если есть
        if form_url:
            message_text += (
                f"🔗 *Перейдите по ссылке для заполнения анкеты:*\n{form_url}\n\n"
            )
        elif form:
            message_text += f"📋 *Данные для анкеты:*\n{form}\n\n"

        # Показываем каналы для подписки
        if sponsors:
            total_fixed_link = subscription_result.get("total_fixed_link", 0)
            requires_full_subscription = subscription_result.get(
                "requires_full_subscription", False
            )

            if requires_full_subscription:
                message_text += f"📢 *Подпишитесь на ВСЕ обязательные каналы ({total_fixed_link} каналов):*\n\n"
            else:
                message_text += "📢 *Подпишитесь на обязательные каналы:*\n\n"

            for i, sponsor in enumerate(
                sponsors[:5], 1
            ):  # Показываем максимум 5 каналов
                title = sponsor.get("title", f"Канал {i}")
                url = sponsor.get("url", "")
                required = sponsor.get("required", True)
                status_icon = "✅" if not required else "🔴"

                if url:
                    message_text += f"{status_icon} {i}. *{title}*\n{url}\n\n"
        else:
            # Показываем каналы только если не статус warning
            if status != "warning":
                message_text += (
                    "📢 *Подпишитесь на обязательный канал для продолжения*\n\n"
                )

        message_text += (
            "✅ *После выполнения всех условий нажмите кнопку 'Проверить подписку'*"
        )

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
                await event.answer(
                    message_text, reply_markup=keyboard, parse_mode="Markdown"
                )
            elif isinstance(event, CallbackQuery):
                await event.message.edit_text(
                    message_text, reply_markup=keyboard, parse_mode="Markdown"
                )
                await event.answer()

        except TelegramBadRequest as e:
            logger.error(f"Ошибка при отправке сообщения о подписке: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке требования подписки: {e}")
