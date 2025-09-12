import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message
from config import settings # Берем токен из вашего конфига

# Включаем простое логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

# Создаем роутер и наш временный обработчик
test_router = Router()
@test_router.message(F.photo)
async def get_photo_id_handler(message: Message):
    try:
        file_id = message.photo[-1].file_id
        await message.answer(f"ID картинки: `{file_id}`")
    except Exception as e:
        # Если ошибка внутри хендлера, мы ее увидим
        await message.answer(f"ОШИБКА ВНУТРИ ОБРАБОТЧИКА: {e}")
        logging.exception("Ошибка в обработчике фото!")

# Основная функция запуска
async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(test_router)
    
    # Запускаем бота
    print("--- ЗАПУСК ТЕСТОВОГО БОТА (только для фото) ---")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())