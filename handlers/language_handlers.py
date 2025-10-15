# handlers/language_handlers.py

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from database import db
from handlers.utils import safe_edit_caption
from keyboards.factories import LanguageCallback, MenuCallback
from keyboards.inline import language_selection_keyboard, language_settings_keyboard
from lexicon.languages import get_language_name, get_text

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(LanguageCallback.filter(F.action == "select"))
async def select_language_handler(
    callback: CallbackQuery, callback_data: LanguageCallback
):
    """Обработчик выбора языка."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    language = callback_data.language

    if not language or language not in ["ru", "en", "uk", "es"]:
        await callback.answer("Неверный язык!", show_alert=True)
        return

    # Сохраняем язык в базе данных
    success = await db.set_user_language(user_id, language)

    if success:
        language_name = get_language_name(language)
        success_text = get_text("language_changed", language, language=language_name)

        # Отправляем сообщение об успешной смене языка
        await callback.message.answer(success_text)

        # Показываем главное меню на новом языке с фотографией
        from handlers.menu_handler import show_main_menu

        # Получаем бота из callback
        bot = callback.bot

        # Отправляем главное меню с фотографией
        await show_main_menu(bot, callback.message.chat.id, state=None)

        await callback.answer("✅ Язык изменен!")
    else:
        await callback.answer("❌ Ошибка при смене языка!", show_alert=True)


@router.callback_query(LanguageCallback.filter(F.action == "change"))
async def change_language_handler(callback: CallbackQuery):
    """Обработчик для показа меню выбора языка."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    current_language = await db.get_user_language(user_id)

    # Показываем меню выбора языка
    text = get_text("language_selection", current_language)

    await safe_edit_caption(
        callback.bot,
        caption=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=language_selection_keyboard(),
    )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.name == "language_settings"))
async def language_settings_handler(callback: CallbackQuery):
    """Обработчик для показа настроек языка."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    current_language = await db.get_user_language(user_id)

    # Показываем настройки языка
    text = get_text("settings_menu", current_language)
    current_lang_name = get_language_name(current_language)
    current_lang_text = get_text(
        "current_language", current_language, language=current_lang_name
    )

    full_text = f"{text}\n\n{current_lang_text}"

    await safe_edit_caption(
        callback.bot,
        caption=full_text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=language_settings_keyboard(current_language),
    )
    await callback.answer()
