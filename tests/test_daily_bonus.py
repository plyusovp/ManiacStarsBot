from contextlib import asynccontextmanager

import aiosqlite
import pytest
import pytest_asyncio

from database import db


@pytest_asyncio.fixture(autouse=True)
async def setup_db(monkeypatch):
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row

    @asynccontextmanager
    async def mock_connect():
        yield conn

    monkeypatch.setattr(db, "connect", mock_connect)
    await db.init_db()
    yield conn
    await conn.close()


@pytest.mark.asyncio
async def test_daily_bonus_flow(setup_db):
    user_id = 2024
    await db.add_user(user_id, "u", "Test", initial_balance=0)

    # user should be notified before first bonus
    notify_users = await db.get_users_for_notification()
    assert user_id in notify_users

    res1 = await db.get_daily_bonus(user_id)
    assert res1["status"] == "success" and res1["reward"] == 1
    balance1 = await db.get_user_balance(user_id)
    assert balance1 == 1

    res2 = await db.get_daily_bonus(user_id)
    assert res2["status"] == "wait" and res2["seconds_left"] > 0

    # simulate passing of more than a day
    await setup_db.execute(
        "UPDATE users SET last_bonus_time = last_bonus_time - 86500 WHERE user_id = ?",
        (user_id,),
    )
    await setup_db.commit()

    # After time travel user again in notification list and can claim bonus
    notify_users = await db.get_users_for_notification()
    assert user_id in notify_users

    res3 = await db.get_daily_bonus(user_id)
    assert res3["status"] == "success"
    balance2 = await db.get_user_balance(user_id)
    assert balance2 == 2
