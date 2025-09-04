# tests/test_concurrency.py
import asyncio

import pytest

from database import db

USER_ID = 2002
INITIAL_BALANCE = 5000
CONCURRENT_REQUESTS = 50
DEBIT_AMOUNT = 10


@pytest.fixture(autouse=True)
async def setup_database():
    """Initializes a clean database for the concurrency test."""
    await db.init_db()
    # Add a user with a known balance
    async with db.connect() as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO users (user_id, username, full_name, balance, registration_date) VALUES (?, ?, ?, ?, ?)",
            (USER_ID, "concurrency_user", "Concurrency User", INITIAL_BALANCE, 123456),
        )
        await conn.commit()
    yield


@pytest.mark.asyncio
async def test_concurrent_debits_do_not_corrupt_balance():
    """
    Simulates many parallel debit requests for the same user to check for race conditions.
    The database's transaction mechanism should prevent data corruption.
    """

    async def debit_task():
        """A single debit operation."""
        # Each call gets its own connection from the pool managed by `connect()`
        # aiosqlite with WAL mode handles concurrency gracefully.
        await db.spend_balance(USER_ID, DEBIT_AMOUNT, "concurrent_debit")

    # Create and run many debit tasks concurrently
    tasks = [debit_task() for _ in range(CONCURRENT_REQUESTS)]
    await asyncio.gather(*tasks)

    # Check the final balance
    final_balance = await db.get_user_balance(USER_ID)
    expected_balance = INITIAL_BALANCE - (CONCURRENT_REQUESTS * DEBIT_AMOUNT)

    assert (
        final_balance == expected_balance
    ), "Balance is incorrect after concurrent debits"
