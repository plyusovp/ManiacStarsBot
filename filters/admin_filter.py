# filters/admin_filter.py
from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from config import settings


class AdminFilter(BaseFilter):
    """
    Фильтр для проверки, является ли пользователь администратором.
    """

    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        # Проверяем, есть ли ID пользователя в списке ADMIN_IDS из конфига
        return obj.from_user.id in settings.ADMIN_IDS
