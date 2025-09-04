# tests/test_economy.py
import uuid

import pytest

from database import db


@pytest.fixture(autouse=True)
async def setup_database():
    """Initializes a clean database for each test."""
    await db.init_db()
    # You might want to use an in-memory SQLite for tests
    # For now, we'll just re-init the existing one.
    # A better approach would be to parametrize the DB name.
    await _add_test_user(1001, 1000)
    yield
    # Teardown: clean up if necessary, though re-init handles it.


async def _add_test_user(user_id: int, balance: int):
    """Helper to add a user with a specific balance."""
    async with db.connect() as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO users (user_id, username, full_name, balance, registration_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"testuser{user_id}", f"Test User {user_id}", 0, 123456789),
        )
        # Use unrestricted add to set a precise balance
        await conn.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?", (balance, user_id)
        )
        await conn.commit()


@pytest.mark.asyncio
async def test_credit_user_balance():
    """Tests simple balance addition."""
    user_id = 1001
    initial_balance = await db.get_user_balance(user_id)
    assert initial_balance == 1000

    success = await db.add_balance_unrestricted(user_id, 50, "test_credit")
    assert success is True

    new_balance = await db.get_user_balance(user_id)
    assert new_balance == initial_balance + 50


@pytest.mark.asyncio
async def test_debit_user_balance_sufficient_funds():
    """Tests simple balance subtraction when funds are sufficient."""
    user_id = 1001
    initial_balance = await db.get_user_balance(user_id)
    assert initial_balance == 1000

    success = await db.spend_balance(user_id, 200, "test_debit")
    assert success is True

    new_balance = await db.get_user_balance(user_id)
    assert new_balance == initial_balance - 200


@pytest.mark.asyncio
async def test_debit_user_balance_insufficient_funds():
    """Tests that spending fails when funds are insufficient."""
    user_id = 1001
    initial_balance = await db.get_user_balance(user_id)
    assert initial_balance == 1000

    success = await db.spend_balance(user_id, 1500, "test_debit_fail")
    assert success is False

    final_balance = await db.get_user_balance(user_id)
    assert final_balance == initial_balance


@pytest.mark.asyncio
async def test_idempotency_spend_balance():
    """Tests that a debit operation with the same idempotency key is not duplicated."""
    user_id = 1001
    idem_key = f"idem-{uuid.uuid4()}"
    initial_balance = await db.get_user_balance(user_id)

    # First attempt should succeed
    success1 = await db.spend_balance(user_id, 100, "idem_test", idem_key=idem_key)
    assert success1 is True
    balance_after_1 = await db.get_user_balance(user_id)
    assert balance_after_1 == initial_balance - 100

    # Second attempt with the same key should also "succeed" but not change the balance
    success2 = await db.spend_balance(user_id, 100, "idem_test", idem_key=idem_key)
    assert success2 is True
    balance_after_2 = await db.get_user_balance(user_id)
    assert balance_after_2 == balance_after_1  # No change


@pytest.mark.asyncio
async def test_create_and_revert_withdrawal_request():
    """Tests the flow of creating a withdrawal and then rejecting it, returning funds."""
    user_id = 1001
    admin_id = 9999
    withdrawal_amount = 300
    initial_balance = await db.get_user_balance(user_id)

    # 1. Create a request
    idem_key = f"reward-test-{uuid.uuid4()}"
    result = await db.create_reward_request(
        user_id, "test_item", withdrawal_amount, idem_key
    )
    assert result["success"] is True
    reward_id = result["reward_id"]
    assert reward_id is not None

    balance_after_hold = await db.get_user_balance(user_id)
    assert balance_after_hold == initial_balance - withdrawal_amount

    # 2. Reject the request
    rejection_success = await db.reject_reward(reward_id, admin_id, "test rejection")
    assert rejection_success is True

    final_balance = await db.get_user_balance(user_id)
    assert final_balance == initial_balance  # Funds should be returned
