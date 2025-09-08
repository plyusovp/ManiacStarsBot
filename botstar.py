# botstar.py
import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
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
from keyboards.reply import persistent_menu_keyboard
from logger_config import setup_logging
from middlewares.error_handler import ErrorHandler
from middlewares.metrics import MetricsMiddleware
from middlewares.middlewares import LastSeenMiddleware
from middlewares.throttling import ThrottlingMiddleware
from middlewares.tracing import TracingMiddleware


async def cleanup_active_games():
    """Завершает все 'зомби-игры' при старте бота."""
    active_duels = await db.get_all_active_duels()
    if active_duels:
        logging.info(f"Обнаружено {len(active_duels)} незавершённых дуэлей. Очистка...")
        for match_id in active_duels:
            await db.interrupt_duel(match_id)
        logging.info("Очистка дуэлей завершена.")

    active_timers = await db.get_all_active_timers()
    if active_timers:
        logging.info(
            f"Обнаружено {len(active_timers)} незавершённых таймеров. Очистка..."
        )
        for match_id in active_timers:
            await db.interrupt_timer_match(match_id)
        logging.info("Очистка таймеров завершена.")


async def send_bonus_reminders(bot: Bot):
    """Рассылает пользователям уведомления о доступном бонусе."""
    users_to_notify = await db.get_users_for_notification()
    if not users_to_notify:
        return

    logging.info(
        f"Начинаю рассылку уведомлений о бонусе для {len(users_to_notify)} пользователей..."
    )
    sent_count = 0
    for user_id in users_to_notify:
        with suppress(Exception):  # Safely ignore users who blocked the bot
            await bot.send_message(
                user_id,
                "⏰ Эй! Твой ежедневный бонус уже доступен. Забери его командой /bonus",
                reply_markup=persistent_menu_keyboard(),
            )
            sent_count += 1
            await asyncio.sleep(0.1)  # Rate limit
    logging.info(f"Уведомления о бонусе отправлены. Успешно: {sent_count}.")


async def main():
    # Настройка логирования
    setup_logging()

    # Инициализация базы данных
    await db.init_db()

    # Используем MemoryStorage для FSM, т.к. состояния не требуют персистентности
    storage = MemoryStorage()

    # Создание объектов Бота и Диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # --- РЕГИСТРАЦИЯ MIDDLEWARES ---
    # Порядок важен:
    # 1. TracingMiddleware - создает trace_id и user_id в data
    # 2. ErrorHandler - ловит ошибки от всех последующих слоев
    # 3. MetricsMiddleware - собирает метрики
    # 4. ThrottlingMiddleware - защита от флуда
    # 5. LastSeenMiddleware - обновляет last_seen
    dp.update.middleware.register(TracingMiddleware())
    dp.update.middleware.register(ErrorHandler())
    dp.update.middleware.register(MetricsMiddleware())
    dp.update.middleware.register(
        ThrottlingMiddleware(rate_limit=settings.THROTTLING_RATE_LIMIT)
    )
    dp.update.middleware.register(LastSeenMiddleware())

    logging.info("Проверка незавершённых игр...")
    await cleanup_active_games()

    # Настройка и запуск планировщика
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_bonus_reminders, "interval", hours=2, args=(bot,))
    scheduler.add_job(db.cleanup_old_idempotency_keys, "interval", days=1)
    scheduler.start()
    logging.info("Планировщик уведомлений и очистки ключей запущен.")

    # --- Подключаем все роутеры из папки handlers ---
    # Важно: более конкретные хендлеры (admin) должны идти раньше общих (user)
    dp.include_router(admin_handlers.router)
    dp.include_router(duel_handlers.router)
    dp.include_router(timer_handlers.router)
    dp.include_router(game_handlers.router)
    dp.include_router(menu_handler.router)
    dp.include_router(user_handlers.router)

    # Установка постоянного меню (команды) для пользователей
    await bot.set_my_commands(
        [
            {"command": "start", "description": "🚀 Перезапустить бота"},
            {"command": "menu", "description": "🏠 Главное меню"},
            {"command": "bonus", "description": "🎁 Ежедневный бонус"},
        ]
    )

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
