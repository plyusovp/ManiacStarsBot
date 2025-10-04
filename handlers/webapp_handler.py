import json
import logging
import uuid
from aiogram import Router, F
from aiogram.types import Message
from database import db

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.web_app_data)
async def process_webapp_data(message: Message):
    """
    Обрабатывает данные, полученные из веб-приложения,
    и выполняет операцию вывода средств.
    """
    try:
        # 1. Получаем данные из сообщения
        webapp_data_str = message.web_app_data.data
        logger.info(f"Получены данные из WebApp: {webapp_data_str}")

        # 2. Парсим JSON
        data = json.loads(webapp_data_str)

        # 3. Проверяем, что это операция вывода
        if data.get("action") != "withdraw":
            logger.warning(f"Получено неизвестное действие: {data.get('action')}")
            return

        # 4. Извлекаем необходимые данные
        user_id = data.get("user_id")
        withdraw_amount = data.get("withdraw_amount", 0)
        commission_amount = data.get("commission_amount", 0)
        bot_stars = data.get("bot_stars_received", 0)
        timestamp = data.get("timestamp", "unknown_ts")
        total_deducted = withdraw_amount + commission_amount

        if not all([user_id, isinstance(withdraw_amount, int), isinstance(bot_stars, int)]):
            logger.error(f"Некорректные данные для вывода: user_id={user_id}, withdraw={withdraw_amount}, stars={bot_stars}")
            await message.answer("❌ Некорректные данные от приложения")
            return

        # 5. Проверяем баланс пользователя
        current_balance = await db.get_user_balance(user_id)
        if current_balance < total_deducted:
            await message.answer(
                f"❌ Недостаточно средств!\n"
                f"Требуется: {total_deducted} ⭐\n"
                f"Доступно: {current_balance} ⭐"
            )
            return

        # 6. Создаем уникальный ключ для предотвращения дублирования операций
        idem_key = f"webapp_withdraw-{user_id}-{uuid.uuid4()}"

        # 7. Списываем средства с баланса
        success = await db.spend_balance(
            user_id=user_id,
            amount=total_deducted,
            reason="webapp_withdrawal",
            ref_id=f"webapp-{timestamp}",
            idem_key=idem_key,
        )

        # 8. Отправляем пользователю уведомление
        if success:
            await message.answer(
                f"✅ Вывод выполнен!\n\n"
                f"💰 Списано: {total_deducted} ⭐\n"
                f"⭐ Зачислено: {bot_stars} звёзд\n"
                f"🆔 User ID: {user_id}\n\n"
                f"📊 Комиссия: {commission_amount} ⭐\n"
                f"🔑 ID операции: {idem_key}"
            )
            logger.info(f"Успешно обработан вывод для пользователя {user_id}: {idem_key}")
        else:
            await message.answer("❌ Ошибка при списании средств. Попробуйте позже.")
            logger.error(f"Не удалось списать средства для пользователя {user_id}: {idem_key}")

    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON из WebApp", exc_info=True)
        await message.answer("❌ Ошибка обработки данных от приложения")
    except Exception:
        logger.error("Непредвиденная ошибка в обработчике WebApp", exc_info=True)
        await message.answer(
            "❌ Произошла внутренняя ошибка. Пожалуйста, попробуйте позже."
        )
