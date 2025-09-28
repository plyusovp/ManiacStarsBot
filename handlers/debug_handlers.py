# handlers/debug_handlers.py
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

# Инициализируем роутер и логгер
router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data)
async def unhandled_callback_catcher(callback: CallbackQuery, state: FSMContext):
    """
    Эта 'ловушка' ловит абсолютно все колбэки, которые не были пойманы
    другими, более специфичными, хендлерами.
    """
    current_state = await state.get_state()
    logger.warning(
        "!!! ПОЙМАН НЕОБРАБОТАННЫЙ КОЛБЭК !!!\n"
        f"--> Пользователь: {callback.from_user.id}\n"
        f"--> Данные колбэка: '{callback.data}'\n"
        f"--> Текущее FSM состояние: '{current_state}'"
    )
    # Отвечаем пользователю, чтобы он понял, что что-то не так
    await callback.answer(
        "Ой! Кажется, я запутался в состояниях. Попробуйте начать заново с /menu.",
        show_alert=True,
    )
