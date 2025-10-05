"""
API для создания заявок на вывод звезд из приложения в бота.
Этот файл содержит функции для интеграции с внешним приложением.
"""

import hashlib
import hmac
import json
import logging
import time
import urllib.parse
from typing import Dict, Any, Optional

from database import db


def validate_telegram_init_data(init_data: str, bot_token: str) -> Optional[Dict[str, Any]]:
    """
    Валидирует initData от Telegram Web App согласно официальной документации.
    
    Args:
        init_data: Строка initData от Telegram
        bot_token: Токен бота для проверки подписи
    
    Returns:
        Dict с данными пользователя если валидация успешна, None иначе
    """
    try:
        # Разбираем строку initData на параметры
        parsed_data = urllib.parse.parse_qs(init_data)
        
        # Извлекаем hash и остальные параметры
        if 'hash' not in parsed_data:
            logging.error("Hash not found in initData")
            return None
        
        received_hash = parsed_data['hash'][0]
        
        # Создаем строку для проверки подписи
        # Убираем hash из параметров и сортируем остальные
        data_check_string_parts = []
        for key, value in parsed_data.items():
            if key != 'hash':
                data_check_string_parts.append(f"{key}={value[0]}")
        
        # Сортируем параметры по алфавиту
        data_check_string_parts.sort()
        data_check_string = '\n'.join(data_check_string_parts)
        
        # Создаем секретный ключ из bot_token
        secret_key = hmac.new(
            "WebAppData".encode('utf-8'),
            bot_token.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Вычисляем ожидаемый hash
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Проверяем подпись
        if not hmac.compare_digest(received_hash, expected_hash):
            logging.error("Invalid hash in initData")
            return None
        
        # Проверяем время auth_date (не старше 24 часов)
        if 'auth_date' in parsed_data:
            try:
                auth_date = int(parsed_data['auth_date'][0])
                current_time = int(time.time())
                if current_time - auth_date > 86400:  # 24 часа
                    logging.error("Auth date is too old")
                    return None
            except (ValueError, IndexError):
                logging.error("Invalid auth_date in initData")
                return None
        
        # Извлекаем данные пользователя
        user_data = {}
        if 'user' in parsed_data:
            try:
                user_data = json.loads(parsed_data['user'][0])
            except json.JSONDecodeError:
                logging.error("Invalid user data in initData")
                return None
        
        return {
            'user_id': user_data.get('id'),
            'user_data': user_data,
            'auth_date': parsed_data.get('auth_date', [None])[0],
            'query_id': parsed_data.get('query_id', [None])[0]
        }
        
    except Exception as e:
        logging.error(f"Error validating initData: {e}")
        return None


async def create_app_withdrawal_api(
    amount: int,
    app_transaction_id: str,
    init_data: str,
    bot_token: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Создает заявку на вывод из приложения в бота через API.
    
    Args:
        amount: Сумма для вывода
        app_transaction_id: Уникальный ID транзакции в приложении
        init_data: initData от Telegram Web App
        bot_token: Токен бота для валидации
        notes: Дополнительные примечания
    
    Returns:
        Dict с результатом операции
    """
    try:
        # Валидируем initData от Telegram
        telegram_data = validate_telegram_init_data(init_data, bot_token)
        if not telegram_data:
            return {
                "success": False,
                "error": "invalid_telegram_auth",
                "message": "Неверная аутентификация Telegram"
            }
        
        # Извлекаем user_id из проверенных данных
        user_id = telegram_data['user_id']
        if not user_id:
            return {
                "success": False,
                "error": "invalid_telegram_auth",
                "message": "Не удалось извлечь user_id из данных Telegram"
            }
        
        # Проверяем, что пользователь существует
        if not await db.user_exists(user_id):
            return {
                "success": False,
                "error": "user_not_found",
                "message": "Пользователь не найден"
            }
        
        # Создаем заявку
        result = await db.create_app_withdrawal(
            user_id=user_id,
            amount=amount,
            app_transaction_id=app_transaction_id,
            notes=notes
        )
        
        if result["success"]:
            logging.info(
                f"App withdrawal created: user_id={user_id}, amount={amount}, "
                f"app_transaction_id={app_transaction_id}, withdrawal_id={result['withdrawal_id']}"
            )
            return {
                "success": True,
                "withdrawal_id": result["withdrawal_id"],
                "message": "Заявка на вывод создана успешно"
            }
        else:
            return {
                "success": False,
                "error": result["reason"],
                "message": _get_error_message(result["reason"])
            }
    
    except Exception as e:
        logging.error(f"Error creating app withdrawal: {e}", exc_info=True)
        return {
            "success": False,
            "error": "internal_error",
            "message": "Внутренняя ошибка сервера"
        }


def _get_error_message(error_code: str) -> str:
    """Возвращает человекочитаемое сообщение об ошибке."""
    error_messages = {
        "invalid_amount": "Неверная сумма",
        "user_not_found": "Пользователь не найден",
        "duplicate_transaction": "Транзакция уже существует",
        "transaction_failed": "Ошибка создания транзакции"
    }
    return error_messages.get(error_code, "Неизвестная ошибка")


async def get_app_withdrawal_status(withdrawal_id: int) -> Dict[str, Any]:
    """
    Получает статус заявки на вывод из приложения.
    
    Args:
        withdrawal_id: ID заявки
    
    Returns:
        Dict с информацией о заявке
    """
    try:
        details = await db.get_app_withdrawal_details(withdrawal_id)
        if not details:
            return {
                "success": False,
                "error": "withdrawal_not_found",
                "message": "Заявка не найдена"
            }
        
        withdrawal = details["withdrawal"]
        return {
            "success": True,
            "withdrawal_id": withdrawal["id"],
            "user_id": withdrawal["user_id"],
            "amount": withdrawal["amount"],
            "status": withdrawal["status"],
            "app_transaction_id": withdrawal.get("app_transaction_id"),
            "created_at": withdrawal["created_at"],
            "updated_at": withdrawal.get("updated_at"),
            "notes": withdrawal.get("notes")
        }
    
    except Exception as e:
        logging.error(f"Error getting withdrawal status: {e}", exc_info=True)
        return {
            "success": False,
            "error": "internal_error",
            "message": "Внутренняя ошибка сервера"
        }


# Пример использования для интеграции с приложением
async def example_integration():
    """
    Пример интеграции с внешним приложением.
    Показывает, как приложение может создавать заявки на вывод.
    """
    # Параметры запроса
    amount = 100
    app_transaction_id = "app_tx_12345"
    init_data = "user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22John%22%7D&auth_date=1234567890&hash=abc123"
    bot_token = "your_bot_token_here"
    
    # Создаем заявку
    result = await create_app_withdrawal_api(
        amount=amount,
        app_transaction_id=app_transaction_id,
        init_data=init_data,
        bot_token=bot_token,
        notes="Вывод из приложения"
    )
    
    print(f"Результат: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # Проверяем статус заявки
    if result["success"]:
        withdrawal_id = result["withdrawal_id"]
        status_result = await get_app_withdrawal_status(withdrawal_id)
        print(f"Статус заявки: {json.dumps(status_result, ensure_ascii=False, indent=2)}")
