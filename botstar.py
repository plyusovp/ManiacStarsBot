import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# Если используешь Redis на сервере, раскомментируй следующую строку
# from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from database import db
from handlers import (
    admin_handlers,
    duel_handlers,
    game_handlers,
    menu_handler,
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

# Определяем логгер в глобальной области видимости
logger = logging.getLogger(__name__)


# Function to configure and run the scheduler
def setup_scheduler(bot: Bot):
    """
    Настраивает и запускает планировщик задач.
    """
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    # Здесь можно будет добавить задачи, если понадобятся
    return scheduler


# A function that is called when the application starts
async def on_startup(bot: Bot):
    """
    Выполняется при запуске бота.
    Устанавливает команды и отправляет уведомление администраторам.
    """
    # Устанавливаем команды бота
    await set_bot_commands(bot)

    # Получаем ID администраторов из настроек
    admins = settings.ADMIN_IDS

    # Отправляем сообщение каждому администратору о запуске бота
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


# Main function to run the bot
async def main():
    """
    Главная функция для запуска бота.
    """
    setup_logging()
    logger.info("Starting bot...")

    # Инициализируем базу данных
    await db.init_db()

    # Используем MemoryStorage для локального тестирования на твоём MacBook.
    # Это хранилище состояний работает в оперативной памяти.
    storage = MemoryStorage()
    logger.info("Using memory storage for local development.")

    # Если будешь запускать на сервере с Redis, используй этот код:
    # try:
    #     storage = RedisStorage.from_url(settings.REDIS_URL)
    #     logger.info("Successfully connected to Redis. Using Redis storage.")
    # except Exception as e:
    #     logger.error(f"Failed to connect to Redis: {e}. Falling back to memory storage.")
    #     storage = MemoryStorage()

    # Инициализируем бота и диспетчер
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)

    # Настраиваем планировщик
    scheduler = setup_scheduler(bot)

    # Регистрируем middlewares
    dp.update.outer_middleware(TracingMiddleware())
    dp.update.outer_middleware(LastSeenMiddleware())
    dp.update.middleware(ThrottlingMiddleware())
    # Важно: ErrorHandler должен быть последним, чтобы ловить все ошибки
    dp.errors.register(ErrorHandler())

    # Регистрируем роутеры
    dp.include_router(user_handlers.router)
    dp.include_router(menu_handler.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(game_handlers.router)
    dp.include_router(duel_handlers.router)
    dp.include_router(timer_handlers.router)

    # Регистрируем функцию on_startup
    dp.startup.register(on_startup)

    try:
        # Запускаем планировщик
        scheduler.start()
        # Удаляем вебхук и запускаем поллинг
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        # Корректно завершаем сессию бота и планировщик
        await bot.session.close()
        scheduler.shutdown()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
