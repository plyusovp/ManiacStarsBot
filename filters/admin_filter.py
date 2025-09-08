from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config import settings


class AdminFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        # Эта строка проверяет, есть ли ID пользователя в списке админов из вашего конфига
        return event.from_user.id in settings.ADMIN_IDS