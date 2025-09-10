import pytest
from unittest.mock import AsyncMock

from handlers import menu_handler
from config import settings
from lexicon.texts import LEXICON
from keyboards.inline import main_menu_keyboard
from database import db


@pytest.mark.asyncio
async def test_show_main_menu_sends_photo_when_edit_fails(monkeypatch):
    bot = AsyncMock()
    bot.send_photo = AsyncMock()
    monkeypatch.setattr(menu_handler, "safe_edit_media", AsyncMock(return_value=False))
    monkeypatch.setattr(db, "get_user_balance", AsyncMock(return_value=5))

    await menu_handler.show_main_menu(bot, chat_id=123, message_id=1)

    expected_caption = LEXICON["main_menu"].format(balance=5)
    bot.send_photo.assert_awaited_once_with(
        chat_id=123,
        photo=settings.PHOTO_MAIN_MENU,
        caption=expected_caption,
        reply_markup=main_menu_keyboard(),
    )
