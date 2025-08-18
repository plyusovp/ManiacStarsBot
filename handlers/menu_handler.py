# handlers/menu_handler.py
from aiogram import Router, Bot
from aiogram.types import Message
from keyboards.inline import main_menu
from config import PHOTO_MAIN_MENU

router = Router()

async def show_main_menu(bot: Bot, chat_id: int, user_id: int):
    """Отправляет главное меню с фотографией."""
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    text = f"""
🔪 <b>Добро пожаловать в Maniac Stars!</b> 🔪

Зови друзей и лутай по <b>5 ⭐</b> за каждого.
<i>Всего 3 кента и у тебя уже подарок!</i>

💪 <b>Только у нас:</b>
— Уникальные Достижения с наградами!
— Ежедневный бонус! Жми /bonus

<b>Твоя реферальная ссылка:</b>
<code>{ref_link}</code>
"""
    await bot.send_photo(chat_id=chat_id, photo=PHOTO_MAIN_MENU, caption=text, reply_markup=main_menu())