# scripts/mini_load_test.py
import asyncio
import logging
import secrets  # Используем secrets для более криптографически стойких случайных чисел
import time
import uuid

from database import db

# --- Настройки теста ---
TEST_DURATION_SECONDS = 60  # Как долго проводить тест
CONCURRENT_WORKERS = 50  # Количество одновременных "пользователей"
TEST_USER_ID = 999999  # ID тестового пользователя
INITIAL_BALANCE = 1_000_000  # Начальный баланс

# Инициализируем генератор случайных чисел один раз
rand = secrets.SystemRandom()

# --- Статистика ---
stats = {
    "started": 0,
    "completed": 0,
    "successful": 0,
    "failed_insufficient_funds": 0,
    "failed_limit": 0,
    "failed_other": 0,
}


async def setup_test_user():
    """Создает или обновляет тестового пользователя с начальным балансом."""
    await db.init_db()  # Убедимся, что таблицы существуют
    async with db.connect() as conn:
        await conn.execute(
            """
            INSERT OR REPLACE INTO users
            (user_id, username, full_name, balance, registration_date, risk_level)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                TEST_USER_ID,
                "load_test_user",
                "Load Test User",
                INITIAL_BALANCE,
                int(time.time()),
                0,
            ),
        )
        # Очистим его лимиты на всякий случай
        await conn.execute(
            "DELETE FROM earn_counters_daily WHERE user_id = ?", (TEST_USER_ID,)
        )
        await conn.commit()
    logging.info(
        f"Тестовый пользователь {TEST_USER_ID} готов с балансом {INITIAL_BALANCE} ⭐"
    )


async def worker(worker_id: int):
    """
    Симулирует действия одного пользователя.
    Случайным образом пытается списать или начислить средства.
    """
    logging.info(f"Воркер {worker_id} запущен.")
    while time.time() - stats["start_time"] < TEST_DURATION_SECONDS:
        stats["started"] += 1
        try:
            # Выбираем случайное действие
            action = rand.choice(["spend", "earn", "earn_limited"])
            amount = rand.randint(10, 100)
            idem_key = f"loadtest-{worker_id}-{uuid.uuid4()}"

            if action == "spend":
                success = await db.spend_balance(
                    TEST_USER_ID, amount, "load_test_spend", idem_key=idem_key
                )
                if success:
                    stats["successful"] += 1
                else:
                    # Это ожидаемая ошибка, если баланс закончился
                    stats["failed_insufficient_funds"] += 1

            elif action == "earn":
                result = await db.add_balance_with_checks(
                    TEST_USER_ID, amount, "promo_activation"
                )  # promo_activation безлимитный
                if result.get("success"):
                    stats["successful"] += 1
                else:
                    stats["failed_other"] += 1
                    logging.warning(f"Ошибка начисления: {result.get('reason')}")

            elif action == "earn_limited":
                # referral_bonus имеет дневной лимит
                result = await db.add_balance_with_checks(
                    TEST_USER_ID, amount, "referral_bonus"
                )
                if result.get("success"):
                    stats["successful"] += 1
                elif result.get("reason") == "daily_cap_exceeded":
                    stats["failed_limit"] += 1
                else:
                    stats["failed_other"] += 1
                    logging.warning(
                        f"Ошибка лимитного начисления: {result.get('reason')}"
                    )

            stats["completed"] += 1
            await asyncio.sleep(rand.uniform(0.1, 0.5))  # Пауза между действиями

        except Exception as e:
            stats["failed_other"] += 1
            logging.error(
                f"Непредвиденная ошибка в воркере {worker_id}: {e}", exc_info=True
            )


async def main():
    """Основная функция для запуска теста."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    await setup_test_user()

    stats["start_time"] = time.time()

    # Запускаем воркеров
    tasks = [worker(i) for i in range(CONCURRENT_WORKERS)]
    await asyncio.gather(*tasks)

    end_time = time.time()
    duration = end_time - stats["start_time"]
    rps = stats["completed"] / duration if duration > 0 else 0

    # --- Выводим результаты ---
    final_balance = await db.get_user_balance(TEST_USER_ID)
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
    print("=" * 50)
    print(f"Продолжительность: {duration:.2f} сек.")
    print(f"Количество воркеров: {CONCURRENT_WORKERS}")
    print(f"Всего операций завершено: {stats['completed']}")
    print(f"Средний RPS (операций/сек): {rps:.2f}\n")

    print(f"✅ Успешных: {stats['successful']}")
    print(f"❌ Неуспешных (всего): {stats['completed'] - stats['successful']}")
    print(f"  - Недостаточно средств: {stats['failed_insufficient_funds']} (ожидаемо)")
    print(f"  - Превышен лимит: {stats['failed_limit']} (ожидаемо)")
    print(f"  - Другие ошибки: {stats['failed_other']}\n")

    print(f"Начальный баланс: {INITIAL_BALANCE} ⭐")
    print(f"Итоговый баланс: {final_balance} ⭐")
    print("=" * 50)

    # Примечание по Event Loop Lag:
    # Измерить event loop lag из внешнего скрипта сложно.
    # Это лучше делать внутри самого приложения.
    # Пример внутри бота:
    # async def monitor_lag():
    #     loop = asyncio.get_event_loop()
    #     while True:
    #         start_time = loop.time()
    #         await asyncio.sleep(0.1)
    #         lag = loop.time() - start_time - 0.1
    #         if lag > 0.1: # 100ms
    #              logging.warning(f"Event loop lag detected: {lag:.3f}s")
    # asyncio.create_task(monitor_lag())


if __name__ == "__main__":
    asyncio.run(main())
