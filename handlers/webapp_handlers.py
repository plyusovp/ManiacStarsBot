# handlers/webapp_handlers.py

import logging
import json
from hashlib import sha256
from hmac import HMAC
from typing import Optional

from aiohttp import web
from aiogram import Bot
from aiogram.types import User

from config import settings
from database import db

# Логгер для этого файла
logger = logging.getLogger(__name__)

# ЭТО ВАЖНО: Вместо aiogram.Router используем RouteTableDef из aiohttp
routes = web.RouteTableDef()


def is_valid_initdata(init_data: str, bot_token: str) -> tuple[bool, Optional[User]]:
    """
    Проверяет, что данные получены от Telegram и не были подделаны.
    Эта функция остается без изменений, она и так была заебись.
    """
    try:
        data_parts = {
            key: value
            for key, value in (part.split("=", 1) for part in init_data.split("&"))
        }
        
        received_hash = data_parts.pop("hash")
        
        check_string = "\n".join(
            f"{key}={value}" for key, value in sorted(data_parts.items())
        )
        
        secret_key = HMAC(
            key=bot_token.encode(), msg=b"WebAppData", digestmod=sha256
        ).digest()
        
        calculated_hash = HMAC(
            key=secret_key, msg=check_string.encode(), digestmod=sha256
        ).hexdigest()

        if calculated_hash != received_hash:
            logger.warning("Invalid initData hash received.")
            return False, None

        user_data = data_parts.get("user")
        if not user_data:
            logger.warning("User data not found in initData.")
            return False, None
            
        user_dict = json.loads(user_data)
        
        return True, User(**user_dict)

    except Exception as e:
        logger.error(f"Failed to validate initData: {e}", exc_info=True)
        return False, None


# А вот декоратор теперь правильный - от aiohttp
@routes.post("/api/withdraw")
async def handle_withdraw(request: web.Request):
    """
    Этот хендлер будет принимать запросы на вывод из твоего кликера.
    """
    bot: Bot = request.app["bot"]
    
    try:
        data = await request.json()
        logger.info(f"Получен запрос на вывод: {data}")

        init_data = data.get("initData")
        amount = data.get("amount")

        if not init_data or not isinstance(amount, int) or amount <= 0:
            logger.error(f"Некорректный запрос: {data}")
            return web.json_response(
                {"status": "error", "message": "Missing required fields."}, status=400
            )

        is_valid, user = is_valid_initdata(init_data, bot.token)
        if not is_valid or not user:
            logger.error(f"Невалидный initData от пользователя: {user.id if user else 'Unknown'}")
            return web.json_response(
                {"status": "error", "message": "Invalid initData."}, status=403
            )
            
        stars_to_add = amount / 200
        if not stars_to_add.is_integer() or stars_to_add <= 0:
            logger.error(f"Некорректное количество звезд для начисления: {stars_to_add}")
            return web.json_response(
                {"status": "error", "message": "Invalid amount for star conversion."}, status=400
            )

        stars_to_add = int(stars_to_add)

        success = await db.add_balance_unrestricted(
            user_id=user.id,
            amount=stars_to_add,
            reason="webapp_withdraw",
            ref_id=data.get("app_transaction_id", "unknown_tx")
        )

        if success:
            logger.info(f"Пользователю {user.id} успешно начислено {stars_to_add} звезд.")
            return web.json_response({"status": "ok", "message": f"{stars_to_add} stars added."})
        else:
            logger.error(f"Не удалось начислить звезды пользователю {user.id}.")
            return web.json_response(
                {"status": "error", "message": "Failed to update balance."}, status=500
            )

    except Exception as e:
        logger.exception("Критическая ошибка в обработчике вывода.")
        return web.json_response(
            {"status": "error", "message": "Internal server error."}, status=500
        )