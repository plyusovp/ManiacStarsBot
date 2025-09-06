# tests/test_concurrency.py
import asyncio
import logging
from contextlib import asynccontextmanager

import aiosqlite
import pytest
import pytest_asyncio

from database import db

USER_ID = 2002
INITIAL_BALANCE = 50000
CONCURRENT_REQUESTS = 200
DEBIT_AMOUNT = 10


@pytest_asyncio.fixture(autouse=True)
async def setup_database(monkeypatch):
    """
    Creates a single in-memory DB for the test and patches db.connect.
    This is crucial for concurrency tests to ensure all operations
    are performed on the *same* database instance.
    """
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row

    @asynccontextmanager
    async def mock_connect():
        yield conn

    monkeypatch.setattr(db, "connect", mock_connect)

    await db.init_db()
    # Add a user with a known balance
    await db.add_user(
        USER_ID, "concurrency_user", "Concurrency User", initial_balance=INITIAL_BALANCE
    )

    yield

    await conn.close()


@pytest.mark.asyncio
async def test_concurrent_debits_race_condition():
    """
    Симулирует N параллельных списаний для одного пользователя, чтобы проверить
    устойчивость к состоянию гонки. Транзакционный механизм SQLite в режиме WAL
    (или PostgreSQL) должен предотвратить повреждение данных.
    """
    successful_debits = []
    failed_debits = []

    async def debit_task():
        """Одна операция списания."""
        success = await db.spend_balance(USER_ID, DEBIT_AMOUNT, "concurrent_debit")
        if success:
            successful_debits.append(1)
        else:
            failed_debits.append(1)

    tasks = [debit_task() for _ in range(CONCURRENT_REQUESTS)]
    await asyncio.gather(*tasks)

    # --- Проверка результатов (Definition of Done) ---
    final_balance = await db.get_user_balance(USER_ID)
    expected_balance = INITIAL_BALANCE - (len(successful_debits) * DEBIT_AMOUNT)

    logging.info(f"Успешных списаний: {len(successful_debits)}")
    logging.info(f"Неуспешных списаний: {len(failed_debits)}")
    logging.info(f"Итоговый баланс: {final_balance}, ожидаемый: {expected_balance}")

    assert final_balance == expected_balance, "Итоговый баланс некорректен после гонки"

    async with db.connect() as conn:
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM ledger_entries WHERE reason = 'concurrent_debit' AND user_id = ?",
            (USER_ID,),
        )
        ledger_entries_count = (await cursor.fetchone())[0]

    assert ledger_entries_count == len(
        successful_debits
    ), "Количество записей в журнале не совпадает с количеством успешных списаний"
