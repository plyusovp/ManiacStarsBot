# bot.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
import database.db as db
from handlers import (
    user_handlers, 
    admin_handlers, 
    game_handlers, 
    menu_handler, 
    duel_handlers, 
    timer_handlers
)

# Включаем логирование
logging.basicConfig(level=logging.INFO)

async def cleanup_active_duels():
    """Завершает все 'зомби-дуэли' при старте бота."""
    active_duels = await db.get_all_active_duels()
    if active_duels:
        print(f"Обнаружено {len(active_duels)} незавершённых дуэлей. Очистка...")
        for match_id in active_duels:
            await db.interrupt_duel(match_id)
        print("Очистка дуэлей завершена.")

async def cleanup_active_timers():
    """Завершает все 'зомби-таймеры' при старте бота."""
    active_timers = await db.get_all_active_timers()
    if active_timers:
        print(f"Обнаружено {len(active_timers)} незавершённых таймеров. Очистка...")
        for match_id in active_timers:
            await db.interrupt_timer_match(match_id)
        print("Очистка таймеров завершена.")

async def run_compensation(bot: Bot):
    """Одноразовая функция для начисления компенсации."""
    flag_file = 'compensation_sent.flag'
    if not os.path.exists(flag_file):
        print("Начинаю рассылку компенсации...")
        all_users = await db.get_all_users()
        message_text = "Извините за технические неполадки 😔\n\nОшибки исправлены, и всем выдана компенсация <b>+2 ⭐</b>.\n\n(Для получения звёзд, которые вам не начислили ранее, напишите в техподдержку с точным количеством и подтверждением). Спасибо за понимание!"
        
        success_count = 0
        fail_count = 0
        for user_id in all_users:
            try:
                await db.add_stars(user_id, 2)
                await bot.send_message(user_id, message_text)
                await asyncio.sleep(0.1) # Небольшая задержка, чтобы не попасть под лимиты Telegram
                success_count += 1
            except Exception as e:
                fail_count += 1
                print(f"Не удалось отправить компенсацию пользователю {user_id}: {e}")
        
        with open(flag_file, 'w') as f:
            f.write('done')
        print(f"Рассылка компенсации завершена. Успешно: {success_count}, Ошибки: {fail_count}.")
    else:
        print("Компенсация уже была отправлена ранее. Пропускаю...")

async def send_bonus_reminders(bot: Bot):
    """Рассылает пользователям уведомления о доступном бонусе."""
    users_to_notify = await db.get_users_for_notification()
    if not users_to_notify:
        print("Нет пользователей для уведомления о бонусе.")
        return

    print(f"Начинаю рассылку уведомлений о бонусе для {len(users_to_notify)} пользователей...")
    sent_count = 0
    for user_id in users_to_notify:
        try:
            await bot.send_message(user_id, "⏰ Эй! Твой ежедневный бонус уже доступен. Не забудь забрать его командой /bonus 😉")
            sent_count += 1
            await asyncio.sleep(0.1)
        except Exception:
            pass 
    print(f"Уведомления о бонусе отправлены. Успешно: {sent_count}.")


async def main():
    await db.init_db()
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    print("Проверка незавершённых игр...")
    await cleanup_active_duels()
    await cleanup_active_timers()
    
    print("Проверка необходимости рассылки компенсации...")
    await run_compensation(bot)

    # ЗАПУСКАЕМ ПЛАНИРОВЩИК УВЕДОМЛЕНИЙ
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_bonus_reminders, 'interval', hours=2, args=(bot,))
    scheduler.start()
    print("Планировщик уведомлений о бонусе запущен.")

    # Регистрируем роутеры (обработчики)
    dp.include_router(admin_handlers.router)
    dp.include_router(duel_handlers.router)
    dp.include_router(timer_handlers.router)
    dp.include_router(game_handlers.router)
    dp.include_router(menu_handler.router)
    dp.include_router(user_handlers.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())