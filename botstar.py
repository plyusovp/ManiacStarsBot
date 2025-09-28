# plyusovp/maniacstarsbot/ManiacStarsBot-4df23ef8bd5b8766acddffe6bca30a128458c7a5/botstar.py

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from database import db

# --- ИЗМЕНЕНИЕ: Добавлен импорт debug_handlers ---
from handlers import (
    admin_handlers,
    basketball_handlers,
    bowling_handlers,
    darts_handlers,
    debug_handlers,
    dice_handlers,
    duel_handlers,
    football_handlers,
    game_handlers,
    menu_handler,
    slots_handlers,
    timer_handlers,
    user_handlers,
)
from keyboards.reply import get_main_menu_keyboard
from logger_config import setup_logging
from middlewares.error_handler import ErrorHandler
from middlewares.middlewares import LastSeenMiddleware
from middlewares.throttling import ThrottlingMiddleware
from middlewares.tracing import TracingMiddleware
from utils.commands import set_bot_commands

logger = logging.getLogger(__name__)


def setup_scheduler(bot: Bot):
    """
    Настраивает и запускает планировщик задач.
    """
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    return scheduler


async def on_startup(bot: Bot):
    """
    Выполняется при запуске бота.

    """

    await set_bot_commands(bot)

    admins = settings.ADMIN_IDS

    for admin_id in admins:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text="✅ Бот успешно запущен!",
                reply_markup=get_main_menu_keyboard(),
            )
        except Exception as e:
            logger.error(
                f"Не удалось отправить сообщение администратору {admin_id}: {e}"
            )


async def main():
    """
    Главная функция для запуска бота.
    """
    setup_logging()

    logger.info("Starting bot...")

    await db.init_db()

    storage = MemoryStorage()

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

    dp = Dispatcher(storage=storage)

    scheduler = setup_scheduler(bot)

    # --- ИЗМЕНЕНИЕ: ErrorHandler теперь регистрируется как middleware ---
    dp.update.outer_middleware(ErrorHandler())
    dp.update.outer_middleware(TracingMiddleware())
    dp.update.outer_middleware(LastSeenMiddleware())
    dp.update.middleware(ThrottlingMiddleware())

    # Регистрируем все основные роутеры
    dp.include_router(user_handlers.router)
    dp.include_router(menu_handler.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(game_handlers.router)
    dp.include_router(duel_handlers.router)
    dp.include_router(timer_handlers.router)
    dp.include_router(slots_handlers.router)
    dp.include_router(football_handlers.router)
    dp.include_router(bowling_handlers.router)
    dp.include_router(basketball_handlers.router)
    dp.include_router(darts_handlers.router)
    dp.include_router(dice_handlers.router)

    # --- ИЗМЕНЕНИЕ: Роутер-ловушка регистрируется ПОСЛЕДНИМ ---
    dp.include_router(debug_handlers.router)

    dp.startup.register(on_startup)

    try:
        scheduler.start()

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        scheduler.shutdown()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
