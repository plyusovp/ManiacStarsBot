"""
Универсальный модуль для проверки подписки пользователей.
Используется во всех обработчиках для блокировки доступа до подписки.
"""

import logging
from typing import Any, Dict, Union

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from utils.subgram_api import check_user_subscription

logger = logging.getLogger(__name__)


async def check_subscription_and_block(
    event: Union[Message, CallbackQuery], user_id: int, chat_id: int
) -> bool:
    """
    Проверяет подписку пользователя и блокирует доступ если не подписан.
    Администраторы пропускаются без проверки.

    Args:
        event: Событие (Message или CallbackQuery)
        user_id: ID пользователя
        chat_id: ID чата

    Returns:
        True если пользователь подписан и может продолжить, False если заблокирован
    """

    # Проверяем, является ли пользователь администратором
    from config import settings
    if user_id in settings.ADMIN_IDS:
        return True  # Администраторы пропускаются без проверки подписки

    try:
        # Проверяем подписку через SubGram API
        subscription_result = await check_user_subscription(user_id, chat_id)

        # Если проверка прошла успешно и пользователь подписан
        if subscription_result.get("success") and subscription_result.get(
            "subscribed", False
        ):
            return True

        # Если пользователь не подписан или не зарегистрирован - блокируем
        await _handle_subscription_required(event, subscription_result)
        return False

    except Exception as e:
        logger.error(f"Ошибка при проверке подписки для пользователя {user_id}: {e}")
        # В случае ошибки пропускаем проверку, чтобы не блокировать бота
        logger.warning(
            f"SubGram API недоступен, пропускаем проверку подписки для пользователя {user_id}"
        )
        return True


async def _handle_subscription_required(
    event: Union[Message, CallbackQuery], subscription_result: Dict[str, Any]
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
        message_text += "⚠️ *Для доступа к боту требуется дополнительная информация*\n\n"
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

        for i, sponsor in enumerate(sponsors[:5], 1):  # Показываем максимум 5 каналов
            title = sponsor.get("title", f"Канал {i}")
            url = sponsor.get("url", "")
            required = sponsor.get("required", True)
            status_icon = "✅" if not required else "🔴"

            if url:
                message_text += f"{status_icon} {i}. *{title}*\n{url}\n\n"
    else:
        # Показываем каналы только если не статус warning
        if status != "warning":
            message_text += "📢 *Подпишитесь на обязательный канал для продолжения*\n\n"

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


async def check_subscription_silent(user_id: int, chat_id: int) -> bool:
    """
    Тихо проверяет подписку пользователя без отправки сообщений.
    Администраторы пропускаются без проверки.

    Args:
        user_id: ID пользователя
        chat_id: ID чата

    Returns:
        True если пользователь подписан, False если нет
    """

    # Проверяем, является ли пользователь администратором
    from config import settings
    if user_id in settings.ADMIN_IDS:
        return True  # Администраторы пропускаются без проверки подписки

    try:
        # Проверяем подписку через SubGram API
        subscription_result = await check_user_subscription(user_id, chat_id)

        # Возвращаем True только если пользователь действительно подписан
        return subscription_result.get("success", False) and subscription_result.get(
            "subscribed", False
        )

    except Exception as e:
        logger.error(f"Ошибка при проверке подписки для пользователя {user_id}: {e}")
        # В случае ошибки пропускаем проверку
        return True
