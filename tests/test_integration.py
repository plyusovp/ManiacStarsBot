# tests/test_integration.py
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from database import db
from handlers import admin_handlers, user_handlers


# Fixture to setup a clean in-memory FSM storage for each test
@pytest.fixture
def fsm_context():
    storage = MemoryStorage()
    # A key is required to create a context instance
    key = MagicMock()
    key.bot_id = 1
    key.chat_id = 123
    key.user_id = 123
    return FSMContext(storage=storage, key=key)


@pytest.fixture(autouse=True)
async def setup_database():
    """Initializes a clean database for each integration test."""
    await db.init_db()
    await _add_test_user(123, 1000)
    await _add_test_user(456, 1000)
    await _add_test_user(789, 50)  # User for withdrawal failure
    yield


async def _add_test_user(user_id: int, balance: int):
    """Helper to add a user."""
    async with db.connect() as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO users (user_id, username, full_name, balance, registration_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"integ_user{user_id}", f"Integ User {user_id}", balance, 123),
        )
        await conn.commit()


@pytest.mark.asyncio
async def test_full_duel_scenario():
    """
    Integration test for a full duel from creation to payout.
    This test mocks bot interactions but uses the real database logic.
    """
    p1_id, p2_id = 123, 456
    stake = 100

    p1_initial_balance = await db.get_user_balance(p1_id)
    p2_initial_balance = await db.get_user_balance(p2_id)

    # 1. Create the duel (stakes are not spent here yet)
    match_id = await db.create_duel(p1_id, p2_id, stake)
    assert match_id is not None

    # Simulate spending for the duel
    await db.spend_balance(p1_id, stake, "duel_stake")
    await db.spend_balance(p2_id, stake, "duel_stake")

    # 2. Simulate game result: p1 wins
    winner_id, loser_id = p1_id, p2_id
    prize = stake * 2  # Simplified prize for test

    # 3. Finish the duel and award the prize
    await db.finish_duel_atomic(match_id, winner_id, loser_id, prize)

    # 4. Verify balances and stats
    p1_final_balance = await db.get_user_balance(p1_id)
    p2_final_balance = await db.get_user_balance(p2_id)

    assert p1_final_balance == p1_initial_balance - stake + prize
    assert p2_final_balance == p2_initial_balance - stake

    winner_stats = await db.get_user_duel_stats(winner_id)
    loser_stats = await db.get_user_duel_stats(loser_id)

    assert winner_stats["wins"] == 1
    assert winner_stats["losses"] == 0
    assert loser_stats["wins"] == 0
    assert loser_stats["losses"] == 1


@pytest.mark.asyncio
async def test_withdrawal_request_flow(fsm_context: FSMContext):
    """
    Tests the withdrawal request FSM flow:
    - User initiates withdrawal.
    - User enters amount.
    - Confirmation is requested.
    - Admin approves it.
    """
    bot_mock = AsyncMock()
    user_id = 123
    admin_id = 9999
    amount_to_withdraw = 200

    # Mock user message and callback
    message_mock = MagicMock()
    message_mock.from_user.id = user_id
    message_mock.chat.id = user_id
    message_mock.text = str(amount_to_withdraw)

    callback_mock = MagicMock()
    callback_mock.from_user.id = user_id
    callback_mock.message.chat.id = user_id
    callback_mock.message.message_id = 12345

    # 1. Start withdrawal process
    await user_handlers.withdraw_start_handler(callback_mock, fsm_context, bot_mock)
    assert (
        await fsm_context.get_state() == user_handlers.UserState.enter_withdrawal_amount
    )

    # 2. Process amount
    await user_handlers.process_withdrawal_amount_handler(
        message_mock, fsm_context, bot_mock
    )
    assert await fsm_context.get_state() == user_handlers.UserState.confirm_withdrawal
    data = await fsm_context.get_data()
    assert data["withdrawal_amount"] == amount_to_withdraw

    # 3. Confirm withdrawal
    await user_handlers.process_withdrawal_confirm_handler(
        callback_mock, fsm_context, bot_mock
    )
    assert await fsm_context.get_state() is None  # State should be cleared

    # 4. Verify request in DB
    pending_rewards = await db.get_pending_rewards()
    assert len(pending_rewards) == 1
    reward = pending_rewards[0]
    assert reward["user_id"] == user_id
    assert reward["stars_cost"] == amount_to_withdraw
    assert reward["status"] == "pending"

    # 5. Admin approves
    callback_data_mock = MagicMock()
    callback_data_mock.target_id = reward["id"]

    callback_admin_mock = MagicMock()
    callback_admin_mock.from_user.id = admin_id

    await admin_handlers.reward_approve_handler(
        callback_admin_mock, callback_data_mock, bot_mock, {}
    )

    # 6. Verify status change
    details = await db.get_reward_full_details(reward["id"])
    assert details is not None
    assert details["reward"]["status"] == "approved"
