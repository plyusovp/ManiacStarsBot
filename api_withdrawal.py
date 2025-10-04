"""
API для создания заявок на вывод звезд из приложения в бота.
Этот файл содержит функции для интеграции с внешним приложением.
"""

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional

from database import db


async def create_app_withdrawal_api(
    user_id: int,
    amount: int,
    app_transaction_id: str,
    signature: str,
    secret_key: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Создает заявку на вывод из приложения в бота через API.
    
    Args:
        user_id: ID пользователя в боте
        amount: Сумма для вывода
        app_transaction_id: Уникальный ID транзакции в приложении
        signature: HMAC подпись для проверки подлинности
        secret_key: Секретный ключ для проверки подписи
        notes: Дополнительные примечания
    
    Returns:
        Dict с результатом операции
    """
    try:
        # Проверяем подпись
        if not _verify_signature(user_id, amount, app_transaction_id, signature, secret_key):
            return {
                "success": False,
                "error": "invalid_signature",
                "message": "Неверная подпись запроса"
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


def _verify_signature(
    user_id: int,
    amount: int,
    app_transaction_id: str,
    signature: str,
    secret_key: str
) -> bool:
    """
    Проверяет HMAC подпись запроса.
    
    Args:
        user_id: ID пользователя
        amount: Сумма
        app_transaction_id: ID транзакции в приложении
        signature: Подпись для проверки
        secret_key: Секретный ключ
    
    Returns:
        True если подпись верна, False иначе
    """
    try:
        # Создаем строку для подписи
        message = f"{user_id}:{amount}:{app_transaction_id}"
        
        # Вычисляем ожидаемую подпись
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Сравниваем подписи
        return hmac.compare_digest(signature, expected_signature)
    
    except Exception as e:
        logging.error(f"Error verifying signature: {e}")
        return False


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
    user_id = 123456789
    amount = 100
    app_transaction_id = "app_tx_12345"
    secret_key = "your_secret_key_here"
    
    # Создаем подпись
    message = f"{user_id}:{amount}:{app_transaction_id}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Создаем заявку
    result = await create_app_withdrawal_api(
        user_id=user_id,
        amount=amount,
        app_transaction_id=app_transaction_id,
        signature=signature,
        secret_key=secret_key,
        notes="Вывод из приложения"
    )
    
    print(f"Результат: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # Проверяем статус заявки
    if result["success"]:
        withdrawal_id = result["withdrawal_id"]
        status_result = await get_app_withdrawal_status(withdrawal_id)
        print(f"Статус заявки: {json.dumps(status_result, ensure_ascii=False, indent=2)}")
