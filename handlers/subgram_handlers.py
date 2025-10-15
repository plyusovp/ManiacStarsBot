"""
Обработчики для работы с SubGram API.
Включает проверку подписок и получение спонсоров.
"""

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from utils.subgram_api import (
    check_user_subscription,
    get_subgram_sponsors,
    handle_subgram_callback,
)

logger = logging.getLogger(__name__)

# Создаем роутер для SubGram обработчиков
router = Router()


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки "Проверить подписку".
    """
    try:
        user = callback.from_user
        chat_id = callback.message.chat.id if callback.message else 0

        if not user or not chat_id:
            await callback.answer(
                "Ошибка получения данных пользователя", show_alert=True
            )
            return

        # Показываем индикатор загрузки
        await callback.answer("Проверяем подписку...")

        # Проверяем подписку через новую универсальную API функцию
        subscription_result = await check_user_subscription(user.id, chat_id)

        if subscription_result.get("success") and subscription_result.get("subscribed"):
            # Пользователь подписан
            await callback.message.edit_text(
                "✅ Отлично! Вы подписаны на все обязательные каналы.\n\n"
                "Теперь вы можете пользоваться всеми функциями бота!",
                reply_markup=None,
            )
            await callback.answer("Подписка подтверждена! Добро пожаловать!")
        elif subscription_result.get("requires_registration"):
            # Пользователь не зарегистрирован - показываем анкету или сообщение об админской регистрации
            form_url = subscription_result.get("form_url")
            form_data = subscription_result.get("form")
            sponsors = subscription_result.get("sponsors", [])
            requires_admin_registration = subscription_result.get(
                "requires_admin_registration", False
            )

            logger.info(
                f"SubGram Handler: Требуется регистрация. form_url: {form_url}, form_data: {form_data}, requires_admin_registration: {requires_admin_registration}"
            )

            if requires_admin_registration:
                # Пользователь не зарегистрирован в системе Subgram
                message_text = "🔒 *ДОСТУП ОГРАНИЧЕН*\n\n"
                message_text += "❌ *Ваш аккаунт не зарегистрирован в системе.*\n\n"
                message_text += (
                    "📞 *Для получения доступа обратитесь к администратору:*\n"
                )
                message_text += "• Напишите администратору\n"
                message_text += "• Укажите ваш Telegram ID\n"
                message_text += "• Дождитесь регистрации в системе\n\n"
                message_text += "⚠️ *После регистрации администратором вы сможете пользоваться ботом*\n\n"
            else:
                # Обычная регистрация с анкетой
                message_text = (
                    "🧪 *ТЕСТ:* Для использования бота необходимо заполнить анкету\n\n"
                )

                if form_url:
                    message_text += f"🔗 *Перейдите по ссылке для заполнения анкеты:*\n{form_url}\n\n"
                elif form_data:
                    message_text += f"📋 *Данные для анкеты:*\n{form_data}\n\n"
                else:
                    message_text += (
                        "📋 *Обратитесь к администратору для заполнения анкеты*\n\n"
                    )

                message_text += (
                    "⚠️ *После заполнения анкеты подпишитесь на каналы ниже:*\n\n"
                )

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

                for i, sponsor in enumerate(sponsors[:5], 1):
                    title = sponsor.get("title", f"Канал {i}")
                    url = sponsor.get("url", "")
                    required = sponsor.get("required", True)
                    status_icon = "✅" if not required else "🔴"

                    if url:
                        message_text += f"{status_icon} {i}. *{title}*\n{url}\n\n"
            else:
                message_text += (
                    "📢 *Подпишитесь на обязательный канал для продолжения*\n\n"
                )

            message_text += (
                "✅ *После выполнения всех условий нажмите кнопку 'Проверить подписку'*"
            )
        else:
            # Пользователь не подписан
            error_message = subscription_result.get("message", "Подписка не найдена")
            sponsors = subscription_result.get("sponsors", [])

            message_text = f"🔒 {error_message}\n\n"

            if sponsors:
                message_text += "📢 *Подпишитесь на обязательные каналы:*\n\n"
                for i, sponsor in enumerate(sponsors[:3], 1):
                    title = sponsor.get("title", f"Канал {i}")
                    url = sponsor.get("url", "")
                    if url:
                        message_text += f"{i}. *{title}*\n{url}\n\n"
            else:
                message_text += (
                    "📢 *Подпишитесь на обязательный канал для продолжения*\n\n"
                )

            message_text += "✅ *После подписки нажмите кнопку 'Проверить подписку'*"

            # Создаем клавиатуру с кнопкой проверки
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

            await callback.message.edit_text(
                message_text, reply_markup=keyboard, parse_mode="Markdown"
            )
            await callback.answer(
                "Подписка не найдена. Пожалуйста, подпишитесь на каналы выше."
            )

    except TelegramBadRequest as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
        await callback.answer("Ошибка при проверке подписки", show_alert=True)
    except Exception as e:
        logger.error(f"Неожиданная ошибка при проверке подписки: {e}")
        await callback.answer("Произошла ошибка при проверке подписки", show_alert=True)


@router.callback_query(F.data.startswith("subgram"))
async def handle_subgram_callbacks(callback: CallbackQuery) -> None:
    """
    Обработчик callback'ов от SubGram (пол, возраст и т.д.).
    """
    try:
        user = callback.from_user
        chat_id = callback.message.chat.id if callback.message else 0
        callback_data = callback.data

        if not user or not chat_id:
            await callback.answer(
                "Ошибка получения данных пользователя", show_alert=True
            )
            return

        # Показываем индикатор загрузки
        if callback_data == "subgram-op":
            await callback.answer("⏳ Проверяем подписки...")
        else:
            await callback.answer("⏳ Обрабатываем данные...")

        # Обрабатываем callback через универсальную функцию
        result = await handle_subgram_callback(user.id, chat_id, callback_data)

        if result.get("success") and result.get("subscribed"):
            # Пользователь прошел проверку
            await callback.message.edit_text(
                "✅ Отлично! Вы подписаны на все обязательные каналы.\n\n"
                "Теперь вы можете пользоваться всеми функциями бота!",
                reply_markup=None,
            )
            await callback.answer("Подписка подтверждена! Добро пожаловать!")
        else:
            # Пользователь не прошел проверку
            error_message = result.get(
                "message", "Требуется выполнение дополнительных условий"
            )
            sponsors = result.get("sponsors", [])
            form = result.get("form")
            form_url = result.get("form_url")

            message_text = f"🔒 {error_message}\n\n"

            # Показываем форму если есть
            if form_url:
                message_text += (
                    f"🔗 *Перейдите по ссылке для заполнения анкеты:*\n{form_url}\n\n"
                )
            elif form:
                message_text += f"📋 *Данные для анкеты:*\n{form}\n\n"

            # Показываем каналы для подписки
            if sponsors:
                total_fixed_link = result.get("total_fixed_link", 0)
                requires_full_subscription = result.get(
                    "requires_full_subscription", False
                )

                if requires_full_subscription:
                    message_text += f"📢 *Подпишитесь на ВСЕ обязательные каналы ({total_fixed_link} каналов):*\n\n"
                else:
                    message_text += "📢 *Подпишитесь на обязательные каналы:*\n\n"

                for i, sponsor in enumerate(sponsors[:5], 1):
                    title = sponsor.get("title", f"Канал {i}")
                    url = sponsor.get("url", "")
                    required = sponsor.get("required", True)
                    status_icon = "✅" if not required else "🔴"

                    if url:
                        message_text += f"{status_icon} {i}. *{title}*\n{url}\n\n"
            else:
                message_text += (
                    "📢 *Подпишитесь на обязательный канал для продолжения*\n\n"
                )

            message_text += (
                "✅ *После выполнения всех условий нажмите кнопку 'Проверить подписку'*"
            )

            # Создаем клавиатуру с кнопкой проверки
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

            await callback.message.edit_text(
                message_text, reply_markup=keyboard, parse_mode="Markdown"
            )
            await callback.answer("Требуется выполнение дополнительных условий")

    except TelegramBadRequest as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
        await callback.answer("Ошибка при обработке данных", show_alert=True)
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке SubGram callback: {e}")
        await callback.answer("Произошла ошибка при обработке данных", show_alert=True)


@router.message(Command("sponsors"))
async def get_sponsors_command(message: Message) -> None:
    """
    Команда для получения списка спонсоров.
    """
    try:
        user = message.from_user
        chat_id = message.chat.id

        if not user:
            await message.answer("Ошибка получения данных пользователя")
            return

        # Проверяем подписку перед показом спонсоров
        from handlers.subscription_checker import check_subscription_and_block

        if not await check_subscription_and_block(message, user.id, chat_id):
            return  # Пользователь заблокирован, сообщение уже отправлено

        # Получаем спонсоров
        sponsors_result = await get_subgram_sponsors(user.id, chat_id, max_sponsors=10)

        if (
            sponsors_result
            and sponsors_result.get("status") == "ok"
            and sponsors_result.get("result")
        ):
            sponsors = sponsors_result["result"]

            message_text = "📢 Доступные каналы для подписки:\n\n"

            for i, sponsor in enumerate(sponsors, 1):
                title = sponsor.get("title", f"Канал {i}")
                url = sponsor.get("url", "")
                description = sponsor.get("description", "")

                message_text += f"{i}. **{title}**\n"
                if description:
                    message_text += f"   {description}\n"
                if url:
                    message_text += f"   {url}\n"
                message_text += "\n"

            await message.answer(message_text, parse_mode="Markdown")
        else:
            error_message = (
                sponsors_result.get("message", "Не удалось получить список каналов")
                if sponsors_result
                else "Не удалось получить список каналов"
            )
            await message.answer(f"❌ {error_message}")

    except Exception as e:
        logger.error(f"Ошибка при получении спонсоров: {e}")
        await message.answer("Произошла ошибка при получении списка каналов")


@router.message(Command("subscription_status"))
async def subscription_status_command(message: Message) -> None:
    """
    Команда для проверки статуса подписки.
    """
    try:
        user = message.from_user
        chat_id = message.chat.id

        if not user:
            await message.answer("Ошибка получения данных пользователя")
            return

        # Проверяем подписку перед показом статуса
        from handlers.subscription_checker import check_subscription_and_block

        if not await check_subscription_and_block(message, user.id, chat_id):
            return  # Пользователь заблокирован, сообщение уже отправлено

        # Проверяем подписку
        subscription_result = await check_user_subscription(user.id, chat_id)

        if subscription_result.get("success"):
            if subscription_result.get("subscribed"):
                await message.answer(
                    "✅ Вы подписаны на все обязательные каналы!\n\n"
                    "Можете пользоваться всеми функциями бота."
                )
            else:
                await message.answer(
                    "❌ Вы не подписаны на обязательные каналы.\n\n"
                    "Используйте команду /sponsors для просмотра доступных каналов."
                )
        else:
            error_message = subscription_result.get(
                "message", "Ошибка проверки подписки"
            )
            await message.answer(f"❌ {error_message}")

    except Exception as e:
        logger.error(f"Ошибка при проверке статуса подписки: {e}")
        await message.answer("Произошла ошибка при проверке статуса подписки")
