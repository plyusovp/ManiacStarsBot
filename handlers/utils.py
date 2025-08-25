# handlers/utils.py
import base64
import hashlib
import hmac
import json
import time
from typing import Dict, Optional

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import settings


# --- Существующая функция ---
async def clean_junk_message(callback: CallbackQuery, state: FSMContext):
    """Удаляет предыдущее 'мусорное' сообщение, если оно было."""
    data = await state.get_data()
    junk_message_id = data.get("junk_message_id")
    if junk_message_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, junk_message_id)
        except TelegramBadRequest:
            pass
        current_data = await state.get_data()
        current_data.pop("junk_message_id", None)
        await state.set_data(current_data)


# --- НОВЫЕ ФУНКЦИИ БЕЗОПАСНОСТИ ---
def generate_signed_payload(data: Dict) -> str:
    """
    Генерирует подписанный и закодированный payload.
    :param data: Словарь с данными для подписи.
    :return: Строка вида 'base64(json).hmac_signature'
    """
    data["ts"] = int(time.time())
    json_payload = json.dumps(data, separators=(",", ":"), sort_keys=True)
    encoded_payload = (
        base64.urlsafe_b64encode(json_payload.encode()).rstrip(b"=").decode()
    )

    signature = hmac.new(
        settings.PAYLOAD_HMAC_SECRET.encode(), encoded_payload.encode(), hashlib.sha256
    ).hexdigest()

    return f"{encoded_payload}.{signature}"


def verify_signed_payload(payload: str, max_age_hours: int) -> Optional[Dict]:
    """
    Проверяет подпись и срок жизни payload.
    :param payload: Подписанная строка.
    :param max_age_hours: Максимальный срок жизни в часах.
    :return: Словарь с данными, если проверка пройдена, иначе None.
    """
    try:
        encoded_part, signature = payload.split(".", 1)

        expected_signature = hmac.new(
            settings.PAYLOAD_HMAC_SECRET.encode(), encoded_part.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature):
            return None

        decoded_payload = base64.urlsafe_b64decode(encoded_part + "==")
        data = json.loads(decoded_payload)

        payload_ts = data.get("ts")
        if not isinstance(payload_ts, int):
            return None

        if time.time() - payload_ts > max_age_hours * 3600:
            return None

        return data
    except (ValueError, TypeError, Exception):
        return None
