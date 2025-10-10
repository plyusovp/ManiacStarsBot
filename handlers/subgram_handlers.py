"""
Обработчики для работы с Subgram (проверка подписки).
"""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import settings
from keyboards.reply import get_main_menu_keyboard
from lexicon.texts import SUBSCRIPTION_TEXTS
from utils.subgram import check_user_subscription

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):
    """
    Обработчик callback для проверки подписки пользователя.
    """
    user = callback.from_user

    # Администраторы всегда имеют доступ
    if user.id in settings.ADMIN_IDS:
        await callback.answer("✅ Вы администратор, доступ разрешен!", show_alert=True)
        await callback.message.delete()
        return

    try:
        # Проверяем подписку
        subscription_result = await check_user_subscription(user)

        if subscription_result.get("success") and subscription_result.get(
            "subscribed", False
        ):
            # Пользователь подписан
            await callback.answer(
                "✅ Подписка подтверждена! Добро пожаловать!", show_alert=True
            )
            await callback.message.delete()

            # Отправляем приветственное сообщение с главным меню
            await callback.message.answer(
                SUBSCRIPTION_TEXTS.get(
                    "welcome_message", "🎉 Добро пожаловать в бота!"
                ),
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            # Пользователь не подписан
            error_message = subscription_result.get(
                "message", "Вы не подписаны на канал"
            )

            # Получаем информацию о канале
            channel_info = subscription_result.get("channel", {})
            channel_url = channel_info.get("url", "")
            channel_username = channel_info.get("username", "")

            message_text = f"❌ {error_message}\n\n"

            if channel_url:
                message_text += f"📢 Подпишитесь на канал: {channel_url}"
            elif channel_username:
                message_text += f"📢 Подпишитесь на канал: @{channel_username}"
            else:
                message_text += "📢 Подпишитесь на обязательный канал для продолжения"

            message_text += "\n\nПосле подписки нажмите кнопку 'Проверить подписку'"

            # Обновляем сообщение
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

            await callback.message.edit_text(message_text, reply_markup=keyboard)
            await callback.answer("❌ Подписка не найдена", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка при проверке подписки для пользователя {user.id}: {e}")
        await callback.answer("❌ Ошибка при проверке подписки", show_alert=True)


@router.message(F.text.in_(["/start", "/help"]))
async def start_command_with_subscription_check(message: Message):
    """
    Обработчик команды /start с проверкой подписки.
    Этот обработчик будет срабатывать только если пользователь уже подписан.
    """
    user = message.from_user

    # Администраторы всегда имеют доступ
    if user.id in settings.ADMIN_IDS:
        await message.answer(
            SUBSCRIPTION_TEXTS.get(
                "admin_welcome", "👑 Добро пожаловать, администратор!"
            ),
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Если пользователь дошел до этого обработчика, значит он подписан
    await message.answer(
        SUBSCRIPTION_TEXTS.get("welcome_message", "🎉 Добро пожаловать в бота!"),
        reply_markup=get_main_menu_keyboard(),
    )
