# tests/test_duel_handlers.py
import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest
from aiogram.fsm.storage.memory import MemoryStorage

from database import db
from handlers import duel_handlers
from keyboards.factories import DuelCallback

# --- Константы для тестов ---
P1_ID = 101
P2_ID = 102
STAKE = 50
INITIAL_BALANCE = 1000
BOT_ID = 123456


# --- Фикстуры для настройки окружения ---


@pytest.fixture(autouse=True)
async def setup_database(monkeypatch):
    """
    Создает единую БД в памяти для каждого теста и патчит db.connect,
    чтобы все обращения к БД использовали одно и то же соединение.
    """
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row

    @asynccontextmanager
    async def mock_connect():
        yield conn

    monkeypatch.setattr(db, "connect", mock_connect)

    # Инициализируем схему на нашем единственном соединении
    await db.init_db()

    # Добавляем тестовых пользователей
    await db.add_user(P1_ID, "player1", "Player One", initial_balance=INITIAL_BALANCE)
    await db.add_user(P2_ID, "player2", "Player Two", initial_balance=INITIAL_BALANCE)

    # Очищаем глобальные переменные хендлера перед каждым тестом для изоляции
    duel_handlers.duel_queue.clear()
    duel_handlers.active_duels.clear()

    yield

    await conn.close()


@pytest.fixture
def mock_bot():
    """Создает мок-объект бота."""
    return AsyncMock()


@pytest.fixture
def memory_storage():
    """Создает FSM storage в памяти."""
    return MemoryStorage()


# --- Тесты ---


@pytest.mark.asyncio
async def test_full_duel_lifecycle(mock_bot, memory_storage):
    """
    Тестирует полный "счастливый путь" дуэли:
    1. Игрок 1 начинает поиск.
    2. Игрок 2 начинает поиск, и игра создается.
    3. Игроки делают ходы в двух раундах.
    4. Игрок 2 побеждает (согласно подстроенным картам).
    5. Проверяется корректность изменения балансов и статистики.
    """
    # --- ARRANGE (Подготовка) ---
    # Переменные p1_state и p2_state не используются, поэтому мы их комментируем,
    # чтобы убрать ошибку F841.
    # p1_state = FSMContext(
    #     storage=memory_storage,
    #     key=StorageKey(bot_id=BOT_ID, user_id=P1_ID, chat_id=P1_ID),
    # )
    # p2_state = FSMContext(
    #     storage=memory_storage,
    #     key=StorageKey(bot_id=BOT_ID, user_id=P2_ID, chat_id=P2_ID),
    # )

    # Мокаем (подменяем) функцию раздачи карт, чтобы контролировать результат
    with patch("handlers.duel_handlers.deal_hand") as mock_deal:
        # P1 (ID 101) получает [9, 7, 5, 3, 1], P2 (ID 102) получает [10, 8, 6, 4, 2]
        mock_deal.side_effect = [[9, 7, 5, 3, 1], [10, 8, 6, 4, 2]]

        # --- ACT 1: Игрок 1 ищет игру ---
        p1_callback = MagicMock()
        p1_callback.answer = AsyncMock()
        p1_callback.from_user.id = P1_ID
        p1_callback.message.chat.id = P1_ID
        p1_callback.message.message_id = 11
        p1_callback_data = DuelCallback(action="stake", value=STAKE)

        await duel_handlers.find_duel_handler(
            p1_callback, p1_callback_data, mock_bot, {"trace_id": "trace-p1"}
        )
        await asyncio.sleep(0.01)

        # --- ASSERT 1: Игрок 1 в очереди ---
        assert len(duel_handlers.duel_queue) == 1
        assert duel_handlers.duel_queue[STAKE][0] == P1_ID
        mock_bot.edit_message_caption.assert_called_once()
        assert "Ищем соперника" in mock_bot.edit_message_caption.call_args[1]["caption"]

        # --- ACT 2: Игрок 2 ищет игру, матч начинается ---
        p2_callback = MagicMock()
        p2_callback.answer = AsyncMock()
        p2_callback.from_user.id = P2_ID
        p2_callback.message.chat.id = P2_ID
        p2_callback.message.message_id = 22
        p2_callback_data = DuelCallback(action="stake", value=STAKE)

        await duel_handlers.find_duel_handler(
            p2_callback, p2_callback_data, mock_bot, {"trace_id": "trace-p2"}
        )
        await asyncio.sleep(0.01)

        # --- ASSERT 2: Игра создана ---
        assert len(duel_handlers.duel_queue) == 0
        assert len(duel_handlers.active_duels) == 1
        match_id = list(duel_handlers.active_duels.keys())[0]
        match = duel_handlers.active_duels[match_id]

        # В start_duel_game p1 - это тот, кто ищет, p2 - тот, кто нашелся
        assert match.p1.id == P1_ID
        assert match.p2.id == P2_ID
        assert "Раунд 1" in mock_bot.edit_message_caption.call_args[1]["caption"]
        assert await db.get_user_balance(P1_ID) == INITIAL_BALANCE - STAKE
        assert await db.get_user_balance(P2_ID) == INITIAL_BALANCE - STAKE

        # --- ACT 3: Раунд 1 (P2 (ID 102) побеждает) ---
        p1_play_callback = MagicMock()
        p1_play_callback.from_user.id = P1_ID
        p1_play_callback_data = DuelCallback(action="play", match_id=match_id, value=9)
        await duel_handlers.play_card_handler(
            p1_play_callback, p1_play_callback_data, mock_bot
        )

        p2_play_callback = MagicMock()
        p2_play_callback.from_user.id = P2_ID
        p2_play_callback_data = DuelCallback(action="play", match_id=match_id, value=10)
        await duel_handlers.play_card_handler(
            p2_play_callback, p2_play_callback_data, mock_bot
        )
        await asyncio.sleep(0.01)

        # --- ASSERT 3: Результат раунда 1 ---
        assert match.p2_wins == 1
        assert match.p1_wins == 0

        # --- ACT 4: Раунд 2 (P2 (ID 102) побеждает снова) ---
        with patch("asyncio.sleep", return_value=None):
            await duel_handlers.start_new_round(mock_bot, match)
            p1_play_callback_data = DuelCallback(
                action="play", match_id=match_id, value=7
            )
            await duel_handlers.play_card_handler(
                p1_play_callback, p1_play_callback_data, mock_bot
            )
            p2_play_callback_data = DuelCallback(
                action="play", match_id=match_id, value=8
            )
            await duel_handlers.play_card_handler(
                p2_play_callback, p2_play_callback_data, mock_bot
            )
            await asyncio.sleep(0.01)

            # --- ASSERT 4: Финальные результаты ---
            assert match.p2_wins == 2
            await duel_handlers.start_new_round(mock_bot, match)
            await asyncio.sleep(0.01)

            assert len(duel_handlers.active_duels) == 0

            rake = int(STAKE * 2 * (7 / 100))
            prize = STAKE * 2 - rake
            p1_final_balance = await db.get_user_balance(P1_ID)
            p2_final_balance = await db.get_user_balance(P2_ID)

            assert p2_final_balance == INITIAL_BALANCE - STAKE + prize
            assert p1_final_balance == INITIAL_BALANCE - STAKE

            p1_stats = await db.get_user_duel_stats(P1_ID)
            p2_stats = await db.get_user_duel_stats(P2_ID)
            assert p1_stats["wins"] == 0
            assert p1_stats["losses"] == 1
            assert p2_stats["wins"] == 1
            assert p2_stats["losses"] == 0
