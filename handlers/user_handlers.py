import logging
from typing import Dict  # <--- ДОБАВИЛ ЭТОТ ИМПОРТ

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from database.db import get_referrals_count  # Добавлено
from database.db import (
    add_user,
    get_daily_bonus,
    get_top_users_by_balance,
    get_user_gifts,
    get_user_info,
)
from gifts import GIFTS_CATALOG
from keyboards.inline import main_menu_keyboard

# ИСПРАВЛЕНО: Импортируем весь словарь LEXICON
from lexicon.texts import LEXICON

logger = logging.getLogger(__name__)

router = Router()

# Тексты, которых не было в лексиконе
HELP_TEXT = (
    "<b>Справка по боту Maniac Stars</b>\n\n"
    "Это бот, где вы можете зарабатывать звезды ⭐, играя в игры и приглашая друзей.\n\n"
    "<b>Основные команды:</b>\n"
    "/start - Перезапустить бота\n"
    "/menu - Открыть главное меню\n"
    "/profile - Посмотреть ваш профиль\n"
    "/top - Посмотреть топ игроков\n"
    "/mygifts - Посмотреть ваши подарки\n"
    "/bonus - Получить ежедневный бонус"
)
MY_GIFTS_TEXT = "<b>🎁 Ваши подарки</b>\n\n{gifts_list}"
TOP_USERS_TEXT = "🏆 <b>Топ-10 игроков по балансу</b> 🏆\n\n{top_list}"


# Команда /start
@router.message(CommandStart())
async def process_start_command(message: Message):
    """
    Обработчик команды /start.
    Добавляет пользователя в базу данных, если его там нет,
    и отправляет приветственное сообщение с основной клавиатурой.
    """
    if not message.from_user:
        return
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await message.answer(
        # ИСПРАВЛЕНО: Используем ключ из словаря
        LEXICON["start_message"].format(full_name=message.from_user.full_name),
        reply_markup=main_menu_keyboard(),
    )


# Команда /help
@router.message(Command(commands=["help"]))
async def process_help_command(message: Message):
    """
    Обработчик команды /help.
    Отправляет пользователю справочную информацию о боте.
    """
    await message.answer(HELP_TEXT)


# Команда /profile
@router.message(Command(commands=["profile"]))
async def process_profile_command(message: Message):
    """
    Обработчик команды /profile.
    Получает и отправляет информацию о профиле пользователя.
    """
    if not message.from_user:
        return
    user_id = message.from_user.id
    profile_data = await get_user_info(user_id)
    if profile_data:
        referrals_count = await get_referrals_count(user_id)
        # ИСПРАВЛЕНО: Собираем все данные для форматирования текста из LEXICON
        await message.answer(
            LEXICON["profile"].format(
                full_name=profile_data.get("full_name", "N/A"),
                user_id=user_id,
                referrals_count=referrals_count,
                duel_wins=profile_data.get("duel_wins", 0),
                duel_losses=profile_data.get("duel_losses", 0),
                balance=profile_data.get("balance", 0),
                status_text="",  # Пока оставляем пустым
            )
        )
    else:
        await message.answer("Не удалось получить данные профиля.")


# Команда /top
@router.message(Command(commands=["top"]))
async def process_top_users_command(message: Message):
    """
    Обработчик команды /top.
    Формирует и отправляет список топ-10 пользователей по балансу.
    """
    top_users = await get_top_users_by_balance()
    if top_users:
        top_list = "\n".join(
            [
                f"{i + 1}. ID: {user_id} - Баланс: {balance} 🪙"
                for i, (user_id, balance) in enumerate(top_users)
            ]
        )
        # ИСПРАВЛЕНО: Используем локальный текст
        await message.answer(TOP_USERS_TEXT.format(top_list=top_list))
    else:
        await message.answer("Пока нет данных для отображения топа.")


# **НОВЫЙ ХЕНДЛЕР ДЛЯ ПРОСМОТРА ПОДАРКОВ**
@router.message(Command(commands=["mygifts"]))
async def process_my_gifts_command(message: Message):
    """
    Обработчик команды /mygifts.
    Показывает пользователю список его подарков.
    """
    if not message.from_user:
        return
    user_id = message.from_user.id
    gifts = await get_user_gifts(user_id)

    if not gifts:
        await message.answer("У вас пока нет подарков.")
        return

    # ИСПРАВЛЕНИЕ: Добавлена аннотация типа для словаря.
    gift_counts: Dict[str, int] = {}
    for gift_data in gifts:
        gift_id = gift_data["item_id"]
        gift_counts[gift_id] = gift_counts.get(gift_id, 0) + 1

    gift_lines = []
    for gift_id, count in gift_counts.items():
        gift_info = next((g for g in GIFTS_CATALOG if g["id"] == gift_id), None)
        if gift_info:
            gift_lines.append(f"{gift_info['emoji']} {gift_info['name']} x{count}")

    if gift_lines:
        await message.answer(MY_GIFTS_TEXT.format(gifts_list="\n".join(gift_lines)))
    else:
        await message.answer("У вас пока нет подарков.")


# Ежедневный бонус
@router.message(F.text == "🎉 Бонус")
async def process_daily_bonus(message: Message):
    """
    Обработчик для получения ежедневного бонуса.
    """
    if not message.from_user:
        return
    user_id = message.from_user.id
    result = await get_daily_bonus(user_id)
    status = result.get("status")
    bonus_amount = result.get("reward")
    message_text = ""
    if status == "success":
        message_text = f"Вы получили {bonus_amount} ⭐!"
    elif status == "wait":
        seconds_left = result.get("seconds_left", 0)
        hours = int(seconds_left // 3600)
        minutes = int((seconds_left % 3600) // 60)
        message_text = f"Следующий бонус будет доступен через {hours} ч. {minutes} мин."
    else:
        message_text = "Не удалось получить бонус. Попробуйте позже."

    # ИСПРАВЛЕНО: Отправляем собранный текст напрямую
    await message.answer(message_text)
