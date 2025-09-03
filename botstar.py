# botstar.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import StorageKey
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
from middlewares.middlewares import LastSeenMiddleware

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_active_games():
    """Завершает все 'зомби-игры' при старте бота."""
    active_duels = await db.get_all_active_duels()
    if active_duels:
        print(f"Обнаружено {len(active_duels)} незавершённых дуэлей. Очистка...")
        for match_id in active_duels:
            await db.interrupt_duel(match_id)
        print("Очистка дуэлей завершена.")

    active_timers = await db.get_all_active_timers()
    if active_timers:
        print(f"Обнаружено {len(active_timers)} незавершённых таймеров. Очистка...")
        for match_id in active_timers:
            await db.interrupt_timer_match(match_id)
        print("Очистка таймеров завершена.")


async def send_bonus_reminders(bot: Bot):
    """Рассылает пользователям уведомления о доступном бонусе."""
    users_to_notify = await db.get_users_for_notification()
    if not users_to_notify:
        return

    print(
        f"Начинаю рассылку уведомлений о бонусе для {len(users_to_notify)} пользователей..."
    )
    sent_count = 0
    for user_id in users_to_notify:
        try:
            await bot.send_message(
                user_id,
                "⏰ Эй! Твой ежедневный бонус уже доступен. Не забудь забрать его 😉",
            )
            sent_count += 1
            await asyncio.sleep(0.1)
        except Exception:
            pass
    print(f"Уведомления о бонусе отправлены. Успешно: {sent_count}.")


# --- НОВАЯ ФУНКЦИЯ: Диагностика "зависших" состояний FSM ---
async def diagnose_stuck_states(dp: Dispatcher, bot: Bot):
    """Проверяет и логирует пользователей, находящихся в каком-либо состоянии FSM."""
    all_users = await db.get_all_users()
    if not all_users:
        return

    stuck_users_count = 0
    for user_id in all_users:
        storage_key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
        state = await dp.fsm.storage.get_state(key=storage_key)
        if state is not None:
            stuck_users_count += 1
            logger.warning(f"FSM DIAGNOSTICS: User {user_id} is in state '{state}'")

    if stuck_users_count > 0:
        logger.warning(
            f"FSM DIAGNOSTICS: Total users in FSM state: {stuck_users_count}"
        )


async def main():
    # Инициализация базы данных
    await db.init_db()

    # Создание объектов Бота и Диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Регистрация middleware для отслеживания активности
    dp.update.middleware.register(LastSeenMiddleware())

    print("Проверка незавершённых игр...")
    await cleanup_active_games()

    # Настройка и запуск планировщика
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_bonus_reminders, "interval", hours=2, args=(bot,))
    scheduler.add_job(db.cleanup_old_idempotency_keys, "interval", days=1)
    # --- НОВОЕ: Добавляем задачу диагностики FSM ---
    scheduler.add_job(
        diagnose_stuck_states, "interval", minutes=15, args=(dp, bot)
    )
    scheduler.start()
    print("Планировщик уведомлений, очистки ключей и диагностики FSM запущен.")

    # --- ГЛАВНОЕ: Подключаем все роутеры из папки handlers ---
    dp.include_router(admin_handlers.router)
    dp.include_router(duel_handlers.router)
    dp.include_router(timer_handlers.router)
    dp.include_router(game_handlers.router)
    dp.include_router(menu_handler.router)
    dp.include_router(
        user_handlers.router
    )  # Этот роутер отвечает за кнопку "Профиль" и /start

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")
