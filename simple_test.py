"""
Простой тест системы вывода звезд без эмодзи.
"""

import asyncio
import hmac
import hashlib
import json
from typing import Dict, Any

from api_withdrawal import create_app_withdrawal_api, get_app_withdrawal_status


async def test_withdrawal_system():
    """Тестирует систему вывода звезд."""
    print("Тестирование системы вывода звезд из приложения в бота")
    print("=" * 60)
    
    # Параметры для тестирования
    user_id = 123456789
    amount = 100
    app_transaction_id = "test_tx_001"
    secret_key = "test_secret_key_123"
    
    print(f"Параметры теста:")
    print(f"   User ID: {user_id}")
    print(f"   Amount: {amount} звезд")
    print(f"   App Transaction ID: {app_transaction_id}")
    print()
    
    # Генерируем подпись
    message = f"{user_id}:{amount}:{app_transaction_id}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"Подпись: {signature}")
    print()
    
    # Тест 1: Создание заявки
    print("1. Тест создания заявки...")
    result = await create_app_withdrawal_api(
        user_id=user_id,
        amount=amount,
        app_transaction_id=app_transaction_id,
        signature=signature,
        secret_key=secret_key,
        notes="Тестовая заявка"
    )
    
    print(f"   Результат: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result["success"]:
        withdrawal_id = result["withdrawal_id"]
        print(f"   УСПЕХ: Заявка создана с ID: {withdrawal_id}")
        print()
        
        # Тест 2: Проверка статуса заявки
        print("2. Тест проверки статуса заявки...")
        status_result = await get_app_withdrawal_status(withdrawal_id)
        print(f"   Результат: {json.dumps(status_result, ensure_ascii=False, indent=2)}")
        
        if status_result["success"]:
            print(f"   УСПЕХ: Статус заявки: {status_result['status']}")
        else:
            print(f"   ОШИБКА: {status_result['message']}")
    else:
        print(f"   ОШИБКА: {result['message']}")
    
    print()
    print("=" * 60)
    print("Тестирование завершено")


async def main():
    """Главная функция для запуска тестов."""
    try:
        await test_withdrawal_system()
    except Exception as e:
        print(f"ОШИБКА во время тестирования: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Запуск тестирования системы вывода звезд")
    print("Внимание: Убедитесь, что база данных инициализирована!")
    print()
    
    # Запускаем тесты
    asyncio.run(main())
