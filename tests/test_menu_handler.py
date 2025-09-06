import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from handlers.menu_handler import games_menu_handler


@pytest.mark.asyncio
async def test_games_menu_handler_edits_message(monkeypatch):
    bot = AsyncMock()
    callback = MagicMock()
    callback.answer = AsyncMock()
    callback.message.chat.id = 123
    callback.message.message_id = 42
    state = MagicMock()
    state.clear = AsyncMock()
    clean_mock = AsyncMock()
    monkeypatch.setattr("handlers.menu_handler.clean_junk_message", clean_mock)

    await games_menu_handler(callback, state, bot)

    bot.edit_message_media.assert_called_once()
    callback.answer.assert_awaited()
    clean_mock.assert_awaited_once()
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_games_menu_handler_sends_photo_on_error(monkeypatch):
    bot = AsyncMock()
    bot.edit_message_media.side_effect = Exception("edit failed")
    callback = MagicMock()
    callback.answer = AsyncMock()
    callback.message.chat.id = 123
    callback.message.message_id = 42
    state = MagicMock()
    state.clear = AsyncMock()
    clean_mock = AsyncMock()
    monkeypatch.setattr("handlers.menu_handler.clean_junk_message", clean_mock)

    await games_menu_handler(callback, state, bot)

    bot.edit_message_media.assert_called_once()
    bot.send_photo.assert_called_once()
    callback.answer.assert_awaited()
    clean_mock.assert_awaited_once()
    state.clear.assert_awaited_once()
