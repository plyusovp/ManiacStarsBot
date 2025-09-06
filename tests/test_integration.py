# tests/test_integration.py
import uuid
from contextlib import asynccontextmanager
from unittest.mock import patch

import aiosqlite
import pytest
import pytest_asyncio

from database import db
from handlers.game_handlers import process_coinflip_round


@pytest_asyncio.fixture(autouse=True)
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
    # Добавляем тестовых пользователей
    await db.add_user(123, "integ_user123", "Integ User 123", initial_balance=1000)
    await db.add_user(456, "integ_user456", "Integ User 456", initial_balance=1000)
    await db.add_user(789, "integ_user789", "Integ User 789", initial_balance=50)

    yield

    await conn.close()


@pytest.mark.asyncio
async def test_idempotency_spend_balance():
    """
    Проверяет, что повторное списание с тем же ключом идемпотентности
    не приводит к двойному списанию и оставляет одну корректную запись в ledger.
    """
    user_id = 123
    idem_key = f"idem-integ-{uuid.uuid4()}"
    initial_balance = await db.get_user_balance(user_id)
    amount = 100

    # Первый запрос - ОК
    success1 = await db.spend_balance(user_id, amount, "idem_test", idem_key=idem_key)
    assert success1 is True
    balance_after_1 = await db.get_user_balance(user_id)
    assert balance_after_1 == initial_balance - amount

    # Второй запрос с тем же ключом - no-op (без операции)
    success2 = await db.spend_balance(user_id, amount, "idem_test", idem_key=idem_key)
    assert success2 is True
    balance_after_2 = await db.get_user_balance(user_id)
    assert balance_after_2 == balance_after_1, "Баланс не должен был измениться"

    # Проверяем, что в ledger только одна запись
    async with db.connect() as conn:
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM ledger_entries WHERE reason = 'idem_test' AND user_id = ?",
            (user_id,),
        )
        count = (await cursor.fetchone())[0]
        assert count == 1


@pytest.mark.asyncio
async def test_full_coinflip_scenario():
    """
    Тестирует полный сценарий игры 'Орёл и Решка':
    1. Списание ставки.
    2. Проведение раунда (в этом тесте мы "заставим" его выиграть).
    3. Начисление выигрыша.
    4. Проверка итогового баланса и записей в ledger.
    """
    user_id = 123
    stake = 50
    level = "easy"
    initial_balance = await db.get_user_balance(user_id)
    idem_key = f"cf-integ-{uuid.uuid4()}"

    # Мокаем secrets.randbelow, чтобы результат всегда был выигрышным
    with patch("handlers.game_handlers.secrets.randbelow", return_value=0):
        result = await process_coinflip_round(
            user_id, stake, level, idem_key, "trace-123"
        )

    assert result.get("success") is True
    assert result.get("is_win") is True

    final_balance = await db.get_user_balance(user_id)
    prize = result.get("prize", 0)
    expected_balance = initial_balance - stake + prize
    assert final_balance == expected_balance, "Итоговый баланс рассчитан неверно"

    # Проверяем записи в ledger
    async with db.connect() as conn:
        cursor = await conn.execute(
            "SELECT amount, reason FROM ledger_entries WHERE user_id = ? ORDER BY id DESC LIMIT 2",
            (user_id,),
        )
        rows = await cursor.fetchall()
        assert len(rows) >= 2
        # Записи идут в обратном порядке: сначала выигрыш, потом списание
        assert rows[0]["amount"] == prize
        assert rows[0]["reason"] == "coinflip_win"
        assert rows[1]["amount"] == -stake
        assert rows[1]["reason"] == "coinflip_stake"


@pytest.mark.asyncio
async def test_create_and_reject_gift_request_scenario():
    """
    Тестирует сценарий заявки на подарок:
    1. Создание заявки (hold) - средства списываются.
    2. Отклонение заявки (reject) - средства возвращаются 1:1.
    """
    user_id = 123
    admin_id = 9999
    withdrawal_amount = 300
    initial_balance = await db.get_user_balance(user_id)

    # 1. Создаем заявку, деньги "замораживаются"
    idem_key = f"reward-test-{uuid.uuid4()}"
    result = await db.create_reward_request(
        user_id, "test_item", withdrawal_amount, idem_key
    )
    assert result["success"] is True
    reward_id = result["reward_id"]
    assert reward_id is not None

    balance_after_hold = await db.get_user_balance(user_id)
    assert balance_after_hold == initial_balance - withdrawal_amount

    # 2. Админ отклоняет заявку
    rejection_success = await db.reject_reward(reward_id, admin_id, "test rejection")
    assert rejection_success is True

    # 3. Проверяем, что баланс вернулся к исходному
    final_balance = await db.get_user_balance(user_id)
    assert final_balance == initial_balance

    # 4. Проверяем ledger на наличие списания и возврата
    async with db.connect() as conn:
        cursor = await conn.execute(
            "SELECT amount, reason FROM ledger_entries WHERE user_id = ? AND (reason = 'reward_hold' OR reason = 'reward_revert')",
            (user_id,),
        )
        rows = await cursor.fetchall()
        assert len(rows) == 2
        assert sum(row["amount"] for row in rows) == 0
