import logging
from contextlib import suppress
from typing import Any, Optional, Union

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message

from config import settings
from database import db
from lexicon.texts import LEXICON

logger = logging.getLogger(__name__)


async def safe_send_message(bot: Bot, user_id: int, text: str, **kwargs: Any) -> bool:
    """Безопасно отправляет сообщение пользователю, обрабатывая возможные ошибки."""
    try:
        await bot.send_message(user_id, text, **kwargs)
        return True
    except TelegramBadRequest as e:
        logger.warning(f"Failed to send message to {user_id}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred sending to {user_id}: {e}")
    return False


async def safe_edit_caption(
    bot: Bot,
    caption: str,
    chat_id: Union[int, str],
    message_id: int,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    **kwargs: Any,
) -> Union[Message, bool]:
    """Безопасно изменяет подпись к медиа, с логированием ошибок."""
    try:
        return await bot.edit_message_caption(
            caption=caption,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
    except TelegramBadRequest as e:
        # Не молчим, а орём в логи, чтобы понять, в чем дело!
        logger.error(
            f"Failed to edit caption for message {message_id} in chat {chat_id}. Reason: {e.message}"
        )
    return False


async def safe_edit_media(
    bot: Bot,
    media: InputMediaPhoto,
    chat_id: int,
    message_id: int,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    **kwargs: Any,
) -> Union[Message, bool]:
    """Безопасно изменяет медиа в сообщении, с логированием ошибок."""
    try:
        return await bot.edit_message_media(
            media=media,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
            **kwargs,
        )
    except TelegramBadRequest as e:
        # И тут тоже орём!
        logger.error(
            f"Failed to edit media for message {message_id} in chat {chat_id}. Reason: {e.message}"
        )
    return False


async def safe_delete(bot: Bot, chat_id: int, message_id: int) -> bool:
    """Безопасно удаляет сообщение."""
    with suppress(TelegramBadRequest, Exception):
        return await bot.delete_message(chat_id, message_id)
    return False


async def get_user_info_text(user_id: int, for_admin: bool = False) -> str:
    """Формирует текст с информацией о пользователе."""
    user = await db.get_user(user_id)
    if not user:
        return "Пользователь не найден."

    referrals_count = await db.get_referrals_count(user_id)

    # Получаем дополнительную информацию
    level_info = await db.get_user_level_info(user_id)
    level_name = level_info.get("level_name", "Новичок")
    streak_days = level_info.get("streak_days", 0)

    text = LEXICON["profile"].format(
        user_id=user["user_id"],
        full_name=user["full_name"],
        balance=user["balance"],
        referrals_count=referrals_count,
        duel_wins=user["duel_wins"],
        duel_losses=user["duel_losses"],
        level_name=level_name,
        streak_days=streak_days,
        status_text="",
    )
    if for_admin:
        details = await db.get_user_full_details_for_admin(user_id)
        trans_text = "\n\nПоследние 15 транзакций:\n"
        if details and details.get("ledger"):
            for t in details["ledger"]:
                trans_text += f"`{t['created_at']}`: {t['amount']}⭐ ({t['reason']})\n"
        else:
            trans_text += "Транзакций не найдено.\n"
        text += trans_text

    return text


def generate_referral_link(user_id: int) -> str:
    """Генерирует правильную реферальную ссылку с префиксом ref_."""
    return f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user_id}"


async def clean_junk_message(state: FSMContext, bot: Bot):
    """Удаляет 'мусорное' сообщение, ID которого хранится в FSM."""
    data = await state.get_data()
    junk_message_id = data.get("junk_message_id")
    if junk_message_id:
        key = state.key
        if key:
            chat_id = key.chat_id
            await safe_delete(bot, chat_id, junk_message_id)
            current_data = await state.get_data()
            current_data.pop("junk_message_id", None)
            await state.set_data(current_data)


async def check_subscription(bot: Bot, user_id: int) -> bool:
    """Проверяет, подписан ли пользователь на основной канал."""
    try:
        member = await bot.get_chat_member(chat_id=settings.CHANNEL_ID, user_id=user_id)
        # Проверяет, является ли пользователь участником, создателем или администратором канала.
        return member.status in ["member", "creator", "administrator"]
    except Exception as e:
        logger.error(f"Не удалось проверить подписку для пользователя {user_id}: {e}")
        # В случае ошибки (например, бот не является администратором в канале), доступ запрещается.
        return False
