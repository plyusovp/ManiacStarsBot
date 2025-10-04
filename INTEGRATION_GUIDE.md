# Руководство по интеграции системы вывода звезд

## Обзор

Система позволяет пользователям выводить звезды из внешнего приложения в бота Telegram. Процесс включает:

1. Пользователь инициирует вывод в приложении
2. Приложение создает заявку через API
3. Администратор рассматривает заявку в боте
4. При одобрении средства начисляются на баланс в боте

## API Endpoints

### 1. Создание заявки на вывод

**POST** `/api/withdrawal/create`

**Заголовки:**
```
Content-Type: application/json
```

**Тело запроса:**
```json
{
    "user_id": 123456789,
    "amount": 100,
    "app_transaction_id": "app_tx_12345",
    "signature": "hmac_signature_here",
    "notes": "Вывод из приложения (опционально)"
}
```

**Параметры:**
- `user_id` (int, обязательный) - ID пользователя в боте
- `amount` (int, обязательный) - Сумма для вывода в звездах
- `app_transaction_id` (string, обязательный) - Уникальный ID транзакции в приложении
- `signature` (string, обязательный) - HMAC подпись для проверки подлинности
- `notes` (string, опциональный) - Дополнительные примечания

**Ответ при успехе:**
```json
{
    "success": true,
    "withdrawal_id": 42,
    "message": "Заявка на вывод создана успешно"
}
```

**Ответ при ошибке:**
```json
{
    "success": false,
    "error": "error_code",
    "message": "Описание ошибки"
}
```

### 2. Получение статуса заявки

**GET** `/api/withdrawal/status/{withdrawal_id}`

**Ответ при успехе:**
```json
{
    "success": true,
    "withdrawal_id": 42,
    "user_id": 123456789,
    "amount": 100,
    "status": "pending",
    "app_transaction_id": "app_tx_12345",
    "created_at": "2024-01-01 12:00:00",
    "updated_at": "2024-01-01 12:00:00",
    "notes": "Вывод из приложения"
}
```

**Возможные статусы:**
- `pending` - Ожидает рассмотрения
- `approved` - Одобрена (средства начислены)
- `rejected` - Отклонена
- `completed` - Выполнена

## Генерация HMAC подписи

Для безопасности все запросы должны содержать HMAC подпись.

### Алгоритм генерации подписи:

1. Создайте строку сообщения: `{user_id}:{amount}:{app_transaction_id}`
2. Вычислите HMAC-SHA256: `HMAC(secret_key, message, SHA256)`
3. Преобразуйте в hex-строку

### Пример на Python:

```python
import hmac
import hashlib

def generate_signature(user_id, amount, app_transaction_id, secret_key):
    message = f"{user_id}:{amount}:{app_transaction_id}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

# Пример использования
user_id = 123456789
amount = 100
app_transaction_id = "app_tx_12345"
secret_key = "your_secret_key_here"

signature = generate_signature(user_id, amount, app_transaction_id, secret_key)
```

## Коды ошибок

| Код ошибки | Описание |
|------------|----------|
| `missing_field` | Отсутствует обязательное поле |
| `invalid_user_id` | Неверный user_id |
| `invalid_amount` | Неверная сумма |
| `invalid_transaction_id` | Неверный app_transaction_id |
| `invalid_json` | Неверный JSON |
| `invalid_signature` | Неверная подпись |
| `user_not_found` | Пользователь не найден |
| `duplicate_transaction` | Транзакция уже существует |
| `withdrawal_not_found` | Заявка не найдена |
| `internal_error` | Внутренняя ошибка сервера |

## Пример интеграции

### Python (aiohttp):

```python
import aiohttp
import hmac
import hashlib
import json

async def create_withdrawal(user_id, amount, app_transaction_id, secret_key):
    # Генерируем подпись
    message = f"{user_id}:{amount}:{app_transaction_id}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Подготавливаем данные
    data = {
        "user_id": user_id,
        "amount": amount,
        "app_transaction_id": app_transaction_id,
        "signature": signature,
        "notes": "Вывод из приложения"
    }
    
    # Отправляем запрос
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://your-bot-server:8080/api/withdrawal/create",
            json=data,
            headers={"Content-Type": "application/json"}
        ) as response:
            result = await response.json()
            return result
```

### JavaScript (fetch):

```javascript
const crypto = require('crypto');

async function createWithdrawal(userId, amount, appTransactionId, secretKey) {
    // Генерируем подпись
    const message = `${userId}:${amount}:${appTransactionId}`;
    const signature = crypto
        .createHmac('sha256', secretKey)
        .update(message)
        .digest('hex');
    
    // Подготавливаем данные
    const data = {
        user_id: userId,
        amount: amount,
        app_transaction_id: appTransactionId,
        signature: signature,
        notes: "Вывод из приложения"
    };
    
    // Отправляем запрос
    const response = await fetch('http://your-bot-server:8080/api/withdrawal/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    
    const result = await response.json();
    return result;
}
```

## Администрирование

### Просмотр заявок в боте:

1. Отправьте команду `/admin` в боте
2. Выберите "📱 Выводы из приложения"
3. Просмотрите список заявок
4. Нажмите на заявку для просмотра деталей

### Действия с заявками:

- **✅ Одобрить** - Начисляет средства на баланс пользователя в боте
- **❌ Отклонить** - Отклоняет заявку с указанием причины
- **✅ Выполнено** - Отмечает заявку как выполненную

## Безопасность

1. **HMAC подписи** - Все запросы должны содержать валидную подпись
2. **Секретный ключ** - Храните секретный ключ в безопасности
3. **HTTPS** - Используйте HTTPS для передачи данных
4. **Валидация** - Проверяйте все входящие данные

## Мониторинг

### Логирование:

Все операции логируются с указанием:
- user_id
- amount
- app_transaction_id
- withdrawal_id
- timestamp

### Метрики:

- Количество созданных заявок
- Количество одобренных заявок
- Количество отклоненных заявок
- Среднее время обработки

## Troubleshooting

### Частые проблемы:

1. **"invalid_signature"** - Проверьте правильность генерации подписи
2. **"user_not_found"** - Убедитесь, что пользователь зарегистрирован в боте
3. **"duplicate_transaction"** - Используйте уникальные app_transaction_id
4. **"invalid_amount"** - Сумма должна быть положительным числом

### Проверка статуса:

Используйте endpoint `/api/withdrawal/status/{withdrawal_id}` для проверки статуса заявки.

## Поддержка

При возникновении проблем:
1. Проверьте логи сервера
2. Убедитесь в правильности подписи
3. Проверьте формат данных
4. Обратитесь к администратору бота
