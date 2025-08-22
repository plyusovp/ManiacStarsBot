# handlers/utils.py
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


async def clean_junk_message(callback: CallbackQuery, state: FSMContext):
    """Удаляет предыдущее 'мусорное' сообщение, если оно было."""
    data = await state.get_data()
    junk_message_id = data.get("junk_message_id")
    if junk_message_id:
        try:
            # Используем bot из объекта callback, чтобы не передавать его отдельно
            await callback.bot.delete_message(callback.message.chat.id, junk_message_id)
        except TelegramBadRequest:
            pass  # Если сообщение уже удалено, ничего страшного

        # Очищаем состояние, чтобы не пытаться удалить сообщение снова
        current_data = await state.get_data()
        current_data.pop("junk_message_id", None)
        await state.set_data(current_data)
