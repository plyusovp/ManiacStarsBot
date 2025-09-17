# utils/commands.py
import logging
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

async def set_bot_commands(bot: Bot):
    """
    Устанавливает команды в меню Telegram при старте бота.
    """
    # Устанавливаем ОДИНАКОВЫЙ список для всех для максимальной надежности.
    # Команда /admin все равно не сработает у обычных пользователей из-за фильтров.
    commands_to_set = [
        BotCommand(command="start", description="🚀 Перезапустить бота"),
        BotCommand(command="menu", description="🏠 Главное меню"),
        BotCommand(command="bonus", description="🎁 Ежедневный бонус"),
        BotCommand(command="admin", description="🔒 Админ-панель"),
    ]

    try:
        await bot.set_my_commands(commands_to_set, scope=BotCommandScopeDefault())
        logging.info("✅ Команды меню успешно установлены для всех пользователей.")
    except Exception as e:
        logging.error(f"❌ Ошибка при установке команд меню: {e}")
