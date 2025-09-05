# tests/test_economy.py
from contextlib import asynccontextmanager

import aiosqlite
import pytest
from freezegun import freeze_time

from database import db
from economy import EARN_RULES


@pytest.fixture(autouse=True)
async def setup_database(monkeypatch):
    """
    Создает единую БД в памяти для каждого теста и патчит db.connect.
    """
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row

    @asynccontextmanager
    async def mock_connect():
        yield conn

    monkeypatch.setattr(db, "connect", mock_connect)

    await db.init_db()
    # Добавляем тестового пользователя
    await db.add_user(1001, "testuser1001", "Test User 1001", initial_balance=1000)

    yield

    await conn.close()


@pytest.mark.asyncio
async def test_credit_user_balance():
    """Тестирует простое начисление на баланс."""
    user_id = 1001
    initial_balance = await db.get_user_balance(user_id)
    assert initial_balance == 1000

    success = await db.add_balance_unrestricted(user_id, 50, "test_credit")
    assert success is True

    new_balance = await db.get_user_balance(user_id)
    assert new_balance == initial_balance + 50


@pytest.mark.asyncio
async def test_debit_user_balance_sufficient_funds():
    """Тестирует простое списание с баланса при наличии средств."""
    user_id = 1001
    initial_balance = await db.get_user_balance(user_id)
    assert initial_balance == 1000

    success = await db.spend_balance(user_id, 200, "test_debit")
    assert success is True

    new_balance = await db.get_user_balance(user_id)
    assert new_balance == initial_balance - 200


@pytest.mark.asyncio
async def test_debit_user_balance_insufficient_funds():
    """Тестирует отказ в списании при недостаточном балансе."""
    user_id = 1001
    initial_balance = await db.get_user_balance(user_id)
    assert initial_balance == 1000

    success = await db.spend_balance(user_id, 1500, "test_debit_fail")
    assert success is False

    final_balance = await db.get_user_balance(user_id)
    assert final_balance == initial_balance


@pytest.mark.asyncio
@freeze_time("2025-09-05")
async def test_daily_earn_limit():
    """
    Тестирует дневной лимит начислений.
    1. Первое начисление должно пройти успешно.
    2. Второе, превышающее лимит, должно быть отклонено.
    3. На следующий день лимит должен сброситься.
    """
    user_id = 1001
    source = "referral_bonus"  # У этого источника есть daily_cap
    limit = EARN_RULES[source]["daily_cap"]
    amount = limit - 10
    initial_balance = await db.get_user_balance(user_id)

    # 1. Первое начисление, не превышающее лимит
    result1 = await db.add_balance_with_checks(user_id, amount, source)
    assert result1.get("success") is True, "Первое начисление должно пройти"
    balance1 = await db.get_user_balance(user_id)
    assert balance1 == initial_balance + amount

    # 2. Второе начисление, которое превысит лимит
    result2 = await db.add_balance_with_checks(user_id, 20, source)  # 20 > 10
    assert result2.get("success") is False, "Второе начисление должно провалиться"
    assert result2.get("reason") == "daily_cap_exceeded"
    balance2 = await db.get_user_balance(user_id)
    assert balance2 == balance1, "Баланс не должен был измениться"

    # 3. Переходим на следующий день
    with freeze_time("2025-09-06"):
        # Попытка начисления снова должна пройти успешно
        result3 = await db.add_balance_with_checks(user_id, 10, source)
        assert (
            result3.get("success") is True
        ), "Начисление на следующий день должно пройти"
        balance3 = await db.get_user_balance(user_id)
        assert balance3 == balance2 + 10
