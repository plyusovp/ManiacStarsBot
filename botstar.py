import asyncio
import logging
import platform

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
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
from keyboards.reply import (
    get_main_menu_keyboard,
)
from logger_config import setup_logging
from middlewares.throttling import ThrottlingMiddleware
from utils.commands import set_commands

# ИСПРАВЛЕНО: Определяем логгер в глобальной области видимости
logger = logging.getLogger(__name__)


# Function to configure and run the scheduler
def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    # Add a job to send duel reminders every 30 seconds
    scheduler.add_job(
        timer_handlers.send_duel_reminders,
        "interval",
        seconds=30,
        args=(bot,),
    )
    # Add a job to end duels every 30 seconds
    scheduler.add_job(
        timer_handlers.end_duels, "interval", seconds=30, args=(bot,)
    )
    return scheduler


# A function that is called when the application starts
async def on_startup(bot: Bot):
    # Set the bot's commands
    await set_commands(bot)
    # Get the list of administrators
    admins = await db.get_admins()
    # Send a message to each administrator that the bot has been launched
    for admin in admins:
        try:
            await bot.send_message(
                chat_id=admin,
                text="Бот запущен!",
                # Add a persistent menu keyboard
                reply_markup=get_main_menu_keyboard(),
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение администратору {admin}: {e}")


# Main function to run the bot
async def main():
    setup_logging()
    logger.info("Starting bot...")

    # Initialize the database
    await db.initialize()

    # Determine the storage to use based on the operating system
    if platform.system() == "Linux":
        storage = RedisStorage.from_url(settings.REDIS_URL)
        logger.info("Using Redis storage")
    else:
        storage = MemoryStorage()
        logger.info("Using memory storage")

    # Initialize the bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=storage)

    # Set up the scheduler
    scheduler = setup_scheduler(bot)

    # Register middlewares and routers
    dp.message.middleware(ThrottlingMiddleware(storage))
    dp.include_router(user_handlers.router)
    dp.include_router(menu_handler.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(game_handlers.router)
    dp.include_router(duel_handlers.router)

    # Register the on_startup function
    dp.startup.register(on_startup)

    try:
        # Start the scheduler
        scheduler.start()
        # Start polling for updates from Telegram
        await dp.start_polling(bot)
    finally:
        # Close the bot session when the application is shut down
        await bot.session.close()
        # Shut down the scheduler
        scheduler.shutdown()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot stopped manually.")

