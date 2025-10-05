"""
Простой HTTP сервер для обработки webhook'ов от приложения.
Позволяет приложению создавать заявки на вывод звезд в бота.
"""

import asyncio
import json
import logging
from typing import Dict, Any

from aiohttp import web
from aiohttp.web import Request, Response

from api_withdrawal import create_app_withdrawal_api, get_app_withdrawal_status
from config import settings


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_withdrawal_handler(request: Request) -> Response:
    """
    Обработчик для создания заявки на вывод из приложения.
    
    POST /api/withdrawal/create
    Body: {
        "amount": int,
        "app_transaction_id": str,
        "initData": str,
        "notes": str (optional)
    }
    """
    try:
        # Получаем данные из запроса
        data = await request.json()
        
        # Проверяем обязательные поля
        required_fields = ["amount", "app_transaction_id", "initData"]
        for field in required_fields:
            if field not in data:
                return web.json_response({
                    "success": False,
                    "error": "missing_field",
                    "message": f"Отсутствует обязательное поле: {field}"
                }, status=400)
        
        # Получаем параметры
        amount = data["amount"]
        app_transaction_id = data["app_transaction_id"]
        init_data = data["initData"]
        notes = data.get("notes")
        
        # Валидация данных
        if not isinstance(amount, int) or amount <= 0:
            return web.json_response({
                "success": False,
                "error": "invalid_amount",
                "message": "Неверная сумма"
            }, status=400)
        
        if not isinstance(app_transaction_id, str) or not app_transaction_id:
            return web.json_response({
                "success": False,
                "error": "invalid_transaction_id",
                "message": "Неверный app_transaction_id"
            }, status=400)
        
        if not isinstance(init_data, str) or not init_data:
            return web.json_response({
                "success": False,
                "error": "invalid_init_data",
                "message": "Неверный initData"
            }, status=400)
        
        # Создаем заявку
        result = await create_app_withdrawal_api(
            amount=amount,
            app_transaction_id=app_transaction_id,
            init_data=init_data,
            bot_token=settings.BOT_TOKEN,
            notes=notes
        )
        
        # Возвращаем результат
        if result["success"]:
            return web.json_response(result, status=200)
        else:
            return web.json_response(result, status=400)
    
    except json.JSONDecodeError:
        return web.json_response({
            "success": False,
            "error": "invalid_json",
            "message": "Неверный JSON"
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error in create_withdrawal_handler: {e}", exc_info=True)
        return web.json_response({
            "success": False,
            "error": "internal_error",
            "message": "Внутренняя ошибка сервера"
        }, status=500)


async def get_withdrawal_status_handler(request: Request) -> Response:
    """
    Обработчик для получения статуса заявки на вывод.
    
    GET /api/withdrawal/status/{withdrawal_id}
    """
    try:
        # Получаем withdrawal_id из URL
        withdrawal_id = int(request.match_info["withdrawal_id"])
        
        # Получаем статус заявки
        result = await get_app_withdrawal_status(withdrawal_id)
        
        # Возвращаем результат
        if result["success"]:
            return web.json_response(result, status=200)
        else:
            return web.json_response(result, status=404)
    
    except ValueError:
        return web.json_response({
            "success": False,
            "error": "invalid_withdrawal_id",
            "message": "Неверный ID заявки"
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error in get_withdrawal_status_handler: {e}", exc_info=True)
        return web.json_response({
            "success": False,
            "error": "internal_error",
            "message": "Внутренняя ошибка сервера"
        }, status=500)


async def health_check_handler(request: Request) -> Response:
    """Обработчик для проверки здоровья сервера."""
    return web.json_response({
        "status": "ok",
        "message": "Сервер работает"
    })


def create_app() -> web.Application:
    """Создает и настраивает веб-приложение."""
    app = web.Application()
    
    # Добавляем маршруты
    app.router.add_post("/api/withdrawal/create", create_withdrawal_handler)
    app.router.add_get("/api/withdrawal/status/{withdrawal_id}", get_withdrawal_status_handler)
    app.router.add_get("/health", health_check_handler)
    
    return app


async def start_server(host: str = None, port: int = None):
    """Запускает веб-сервер."""
    app = create_app()
    
    # Используем переменные окружения или значения по умолчанию
    host = host or getattr(settings, 'WEB_SERVER_HOST', '0.0.0.0')
    port = port or getattr(settings, 'WEB_SERVER_PORT', 8080)
    
    logger.info(f"Запуск сервера на {host}:{port}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info("Сервер запущен")
    
    # Ждем завершения
    try:
        await asyncio.Future()  # Запускаем навсегда
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    # Запускаем сервер
    asyncio.run(start_server())
